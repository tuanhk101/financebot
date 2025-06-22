from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import os
from utils import load_fund, save_fund, current_time

FUND_FILE = "data/fund.json"

class FundState(StatesGroup):
    choosing_type = State()
    choosing_account = State()
    choosing_member = State()
    entering_amount = State()
    adding_account = State()
    adding_member = State()

async def fund_menu(query: CallbackQuery):
    await query.answer()
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📅 Ghi nhận Quỹ", callback_data="fund_record"),
        InlineKeyboardButton("📊 Báo Cáo Quỹ", callback_data="fund_report")
    )
    await query.message.edit_text("💰 Chọn chức năng quản lý quỹ:", reply_markup=keyboard)

async def handle_fund_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if query.data == "fund_record":
        await select_type(query.message)
    elif query.data == "fund_report":
        await fund_report(query.message)

async def select_type(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("🟢 Thu Quỹ", callback_data="type_thu"),
        InlineKeyboardButton("🔴 Chi Quỹ", callback_data="type_chi")
    )
    await message.edit_text("Chọn loại giao dịch:", reply_markup=keyboard)
    await FundState.choosing_type.set()

async def handle_type_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()
    fund_type = "Thu" if query.data == "type_thu" else "Chi"
    await state.update_data(fund_type=fund_type)
    fund = load_fund()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for acc in fund["accounts"]:
        keyboard.insert(InlineKeyboardButton(acc, callback_data=f"acc_{acc}"))
    keyboard.add(InlineKeyboardButton("➕ Thêm tài khoản", callback_data="add_account"))
    await query.message.edit_text("Chọn tài khoản:", reply_markup=keyboard)
    await FundState.choosing_account.set()

async def handle_account_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()
    if query.data == "add_account":
        await query.message.answer("Gõ tên tài khoản mới:")
        await FundState.adding_account.set()
        return

    account = query.data.replace("acc_", "")
    await state.update_data(account=account)

    fund = load_fund()
    keyboard = InlineKeyboardMarkup(row_width=2)
    for mem in fund["members"]:
        keyboard.insert(InlineKeyboardButton(mem, callback_data=f"mem_{mem}"))
    keyboard.add(InlineKeyboardButton("➕ Thêm người", callback_data="add_member"))
    await query.message.edit_text("Chọn người thực hiện:", reply_markup=keyboard)
    await FundState.choosing_member.set()

async def handle_member_callback(query: CallbackQuery, state: FSMContext):
    if query.data.startswith("mem_"):
        member = query.data.replace("mem_", "")
        await state.update_data(member=member)
        await query.message.delete()  # 🧹 Xoá menu chọn người sau khi chọn
        await query.message.answer("Nhập số tiền:")
        await FundState.entering_amount.set()

async def save_transaction(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
    except ValueError:
        await message.answer("⚠️ Số tiền không hợp lệ. Nhập lại:")
        return

    data = await state.get_data()
    fund = load_fund()
    fund["transactions"].append({
        "type": data["fund_type"],
        "account": data["account"],
        "amount": amount,
        "member": data["member"],
        "time": current_time()
    })
    save_fund(fund)

    icon = "🟢" if data["fund_type"] == "Thu" else "🔴"
    msg = (
        "✅ Giao dịch thành công!\n\n"
        f"{icon} Loại:       {data['fund_type']}\n"
        f"🏦 Tài khoản:  {data['account']}\n"
        f"💵 Số tiền:    {amount:,} VNĐ\n"
        f"👤 Người:      {data['member']}\n"
        f"🕒 Thời gian:  {current_time()}"
    )
    await message.answer(msg)
    await state.finish()

async def fund_report(message: types.Message):
    data = load_fund()
    thu = sum(x['amount'] for x in data['transactions'] if x['type'] == 'Thu')
    chi = sum(x['amount'] for x in data['transactions'] if x['type'] == 'Chi')
    sodu = thu - chi

    msg = "📉 Tổng Hợp Thu Chi\n"
    msg += "Loại | Số tiền\n"
    msg += "-------------------------\n"
    msg += f"🟢 Thu  | {thu:,} VNĐ\n"
    msg += f"🔴 Chi  | {chi:,} VNĐ\n"
    msg += f"💰 Số dư | {sodu:,} VNĐ\n\n"

    msg += "💼 Số Dư Theo Nguồn Tiền\n"
    msg += "-------------------------\n"
    acc_balance = {acc: 0 for acc in data['accounts']}
    for t in data['transactions']:
        amt = t['amount'] if t['type'] == 'Thu' else -t['amount']
        acc_balance[t['account']] = acc_balance.get(t['account'], 0) + amt
    for acc, val in acc_balance.items():
        msg += f"🏦 {acc:<6} : 💰 {val:,} VNĐ\n"

    msg += "\n🧾 Lịch Sử Quỹ:\n"
    msg += "-------------------------\n"
    msg += "ID | Time      | Type | Amount | Mem\n"
    for i, t in enumerate(data["transactions"], 1):
        icon = "🟢 T" if t["type"] == "Thu" else "🔴 C"
        msg += f"{i:02} | {t['time']} | {icon} | {t['amount']:,} | 👤 {t['member']}\n"

    await message.answer(f"<code>{msg}</code>", parse_mode="HTML")

async def add_account(message: types.Message, state: FSMContext):
    new_acc = message.text.strip()
    if not new_acc:
        await message.answer("⚠️ Tên tài khoản không hợp lệ.")
        return
    fund = load_fund()
    if new_acc not in fund["accounts"]:
        fund["accounts"].append(new_acc)
        save_fund(fund)
    await state.update_data(account=new_acc)
    await message.answer(f"✅ Đã thêm tài khoản {new_acc}.")

    keyboard = InlineKeyboardMarkup(row_width=2)
    for mem in fund["members"]:
        keyboard.insert(InlineKeyboardButton(mem, callback_data=f"mem_{mem}"))
    keyboard.add(InlineKeyboardButton("➕ Thêm người", callback_data="add_member"))
    await message.answer("Chọn người thực hiện:", reply_markup=keyboard)
    await FundState.choosing_member.set()

async def add_member(message: types.Message, state: FSMContext):
    new_mem = message.text.strip()
    if not new_mem:
        await message.answer("⚠️ Tên người không hợp lệ.")
        return
    fund = load_fund()
    if new_mem not in fund["members"]:
        fund["members"].append(new_mem)
        save_fund(fund)
    await state.update_data(member=new_mem)
    await message.answer(f"✅ Đã thêm người {new_mem}.")
    await message.answer("Nhập số tiền:")
    await FundState.entering_amount.set()

def register(dp):
    dp.register_callback_query_handler(fund_menu, lambda c: c.data == "fund_menu")
    dp.register_callback_query_handler(handle_fund_callback, lambda c: c.data.startswith("fund"))
    dp.register_callback_query_handler(handle_type_callback, lambda c: c.data.startswith("type"), state=FundState.choosing_type)
    dp.register_callback_query_handler(handle_account_callback, lambda c: c.data.startswith("acc") or c.data == "add_account", state=FundState.choosing_account)
    dp.register_callback_query_handler(handle_member_callback, lambda c: c.data.startswith("mem") or c.data == "add_member", state=FundState.choosing_member)
    dp.register_message_handler(save_transaction, state=FundState.entering_amount)
    dp.register_message_handler(add_account, state=FundState.adding_account)
    dp.register_message_handler(add_member, state=FundState.adding_member)
