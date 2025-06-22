from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import json
import os
from datetime import datetime, timedelta
from utils import current_time

REPORT_FILE = "data/reports.json"

members = [
    "TH13 Co Hương", "TH14 gom", "TH2 Huyen", "TH3 Hieu", "TH4 Vũ", "TH5 Lâm Bình", "TH6 Tú", "TH7 vk gấu", "TH8 thuy", "TH9 Bi", "THatha",
    "TH Family", "TH Vinh(PH)", "TH a6 aTuan", "TH Aliem PH", "TH cHang PH", "TH10 aSang", "TH a6.4", "TH Diaky tuana6", "TH a6 usa", "TH a6.2", "TH a6.3", "TH atuan.2 a6", "TH phungD", "TH tuan(vani)",
    "TH12 Khang", "TH Trung", "TH 001", "TH 002", "TH 003", "TH 004", "TH 005", "TH aha Khang", "TH dieu(khangtc) 35%", "TH khang ut2", "TH ut khang"
]

class WeeklyReportState(StatesGroup):
    choosing_person = State()
    entering_rate = State()
    entering_amount = State()
    adding_member = State()
    custom_rate = State()


rate_overrides = {}
available_rates = [10, 15, 20, 25, 30, 35, 40, 45, 50]

def load_reports():
    if not os.path.exists(REPORT_FILE):
        return {}
    try:
        with open(REPORT_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_report(week_key: str, week_data: dict):
    print(f"[CALL] save_report: week={week_key}, entries={len(week_data)}")

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    try:
        with open(REPORT_FILE, "r", encoding="utf-8") as f:
            reports = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        reports = {}

    reports[week_key] = week_data

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)

    print(f"[DONE] reports.json saved with {len(reports)} tuần")



def get_week_range(date=None):
    if date is None:
        date = datetime.today()
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%d/%m')} - {sunday.strftime('%d/%m')}"

def get_week_key(date=None):
    if date is None:
        date = datetime.today()
    monday = date - timedelta(days=date.weekday())
    return monday.strftime("%Y-%m-%d")
async def show_all_weeks_report(query: CallbackQuery):
    await query.answer()
    reports = load_reports()
    if not reports:
        await query.message.answer("⚠️ Không có dữ liệu báo cáo nào.")
        return

    lines = ["<b>Tổng hợp các tuần:</b>"]
    for week, entries in sorted(reports.items()):
        total = sum(x["tientuan"] for x in entries.values())
        lines.append(f"🗓️ {week} | {'+' if total > 0 else ''}{total:,} VNĐ")

    await query.message.answer("\n".join(lines), parse_mode="HTML")

async def weekly_menu(query: CallbackQuery):
    await query.answer()
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Kết Tuần", callback_data="weekly_start"),
        InlineKeyboardButton("📅 History", callback_data="weekly_history")
    )
    await query.message.edit_text("📊 Báo Cáo Tuần gồm:", reply_markup=keyboard)
async def handle_backup(query: CallbackQuery):
    await query.answer()
    if not os.path.exists(BACKUP_FILE):
        await query.message.answer("⚠️ Chưa có file backup nào.")
    else:
        await query.message.answer_document(types.InputFile(BACKUP_FILE), caption="📦 Dữ liệu backup báo cáo tuần")
async def start_weekly_report(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await state.update_data(remaining_members=members.copy(), report_data={}, current_person=None)
    await query.message.delete()
    await show_member_buttons(query.message, state)

async def show_member_buttons(message, state: FSMContext):
    data = await state.get_data()
    remaining_members = data.get("remaining_members", [])

    keyboard = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(name, callback_data=f"choose_{name}") for name in remaining_members]
    for i in range(0, len(buttons), 3):
        keyboard.row(*buttons[i:i+3])
    keyboard.add(
        InlineKeyboardButton("➕ Thêm người", callback_data="add_member"),
        InlineKeyboardButton("✅ Hoàn thành báo cáo", callback_data="finish_report")
    )

    sent = await message.answer("Chọn người cần nhập thông tin:", reply_markup=keyboard)
    await state.update_data(last_member_message_id=sent.message_id)
    await WeeklyReportState.choosing_person.set()

async def handle_choose_person(query: CallbackQuery, state: FSMContext):
    await query.answer()
    name = query.data.split("choose_")[-1]
    await state.update_data(current_person=name)

    data = await state.get_data()
    last_msg_id = data.get("last_member_message_id")
    if last_msg_id:
        try:
            await query.bot.delete_message(query.message.chat.id, last_msg_id)
        except:
            pass

    await show_rate_options(query.message)
    await WeeklyReportState.entering_rate.set()

async def show_rate_options(message):
    keyboard = InlineKeyboardMarkup(row_width=5)
    for rate in available_rates:
        keyboard.insert(InlineKeyboardButton(f"{rate}%", callback_data=f"rate_{rate}"))
    keyboard.add(InlineKeyboardButton("➕ Tự nhập", callback_data="custom_rate"))
    await message.answer("Chọn tỷ lệ (%):", reply_markup=keyboard)
    
async def enter_rate_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.delete()
    rate_val = float(query.data.split("rate_")[1])
    session = await state.get_data()
    current_person = session.get("current_person")
    rate_overrides[current_person] = rate_val
    await state.update_data(current_rate=rate_val)
    await query.message.answer("💵 Nhập số tiền (có thể âm hoặc dương):\n👉 Gõ /rate nếu muốn thay đổi lại tỷ lệ.")
    await WeeklyReportState.entering_amount.set()

async def handle_custom_rate(query: CallbackQuery):
    await query.answer()
    await query.message.answer("Gõ tỷ lệ tuỳ chỉnh:")
    await WeeklyReportState.custom_rate.set()
    await query.message.delete() 

async def enter_custom_rate(message: types.Message, state: FSMContext):
    try:
        rate_val = float(message.text.strip().replace("%", ""))
    except:
        return await message.answer("⚠️ Nhập tỷ lệ không hợp lệ. Vui lòng nhập lại.")

    data = await state.get_data()
    current_person = data.get("current_person")
    rate_overrides[current_person] = rate_val
    await state.update_data(current_rate=rate_val)
    if rate_val not in available_rates:
        available_rates.append(int(rate_val))
    await message.answer("💵 Nhập số tiền (có thể âm hoặc dương):\n👉 Gõ /rate nếu muốn thay đổi lại tỷ lệ.")
    await WeeklyReportState.entering_amount.set()

async def add_member(message: types.Message, state: FSMContext):
    new_name = message.text.strip()
    if not new_name:
        await message.answer("⚠️ Tên không hợp lệ.")
        return
    data = await state.get_data()
    remaining = data.get("remaining_members", [])
    if new_name not in members:
        members.append(new_name)
    if new_name not in remaining:
        remaining.append(new_name)
    await state.update_data(current_person=new_name, remaining_members=remaining)
    await show_rate_options(message)
    await WeeklyReportState.entering_rate.set()

async def enter_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data.get("current_person") is None:
        return await message.answer("⚠️ Bạn chưa chọn người. Vui lòng chọn người trước.")

    if message.text.startswith("/rate"):
        await show_rate_options(message)
        await WeeklyReportState.entering_rate.set()
        return
    try:
        amount = int(message.text.replace(",", "").replace(".", ""))
    except:
        return await message.answer("⚠️ Nhập số tiền không hợp lệ.")

    person = data["current_person"]
    rate = rate_overrides.get(person, data.get("current_rate", 0))
    tientuan = round(amount - amount * rate / 100)
    await message.answer(f"👤 {person}")
    await message.answer(f"{amount:,.0f} - {rate:.0f}%\n{'Bù' if tientuan > 0 else 'Thu'} {tientuan:,}")
    new_report_data = data.get("report_data", {})
    new_report_data[person] = {
        "amount": amount,
        "rate": rate,
        "tientuan": tientuan
    }
    remaining = data.get("remaining_members", [])
    if person in remaining:
        remaining.remove(person)
    await state.update_data(report_data=new_report_data, remaining_members=remaining, current_person=None)
    if not remaining:
        await finish_weekly_report(message, state)
    else:
        await show_member_buttons(message, state)

async def finish_report_callback(query: CallbackQuery, state: FSMContext):
    await query.answer()
    await query.message.delete()
    await finish_weekly_report(query.message, state)
    print(f"[✅ SAVED] Tuần: {week_key}, Tổng: {len(report_data)} mục")


async def finish_weekly_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    report_data = data.get("report_data", {})
    if not report_data:
        await message.answer("❌ Không có dữ liệu để lưu.")
        return

    week_key = get_week_key()
    save_report(week_key, report_data)

    
    week_title = f"🗓️ Lịch Sử Tuần {get_week_range()}"
    header = "ID | Name       | Type | Amount"
    lines = []
    for idx, (person, entry) in enumerate(report_data.items(), 1):
        icon = "🟢" if entry["tientuan"] > 0 else "🔴"
        label = "Bù" if entry["tientuan"] > 0 else "Thu"
        amount = f"{entry['tientuan']:,}"
        lines.append(f"{idx:02} | {person:<10} | {icon} {label:<3} | {amount} VNĐ")

    msg = f"<pre>{week_title}\n{header}\n" + "\n".join(lines) + "</pre>"
    await message.answer(msg, parse_mode="HTML")
    await state.finish()

async def show_history_menu(callback: CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📅 Tuần này", callback_data="history_this_week"),
        InlineKeyboardButton("📆 Tuần trước", callback_data="history_last_week")
    )
    await callback.message.edit_text("🕓️ Chọn tuần cần xem:", reply_markup=keyboard)

async def show_history_detail(query: CallbackQuery):
    await query.answer()

    if query.data == "history_this_week":
        date = datetime.today()
    else:  # "history_last_week"
        date = datetime.today() - timedelta(days=7)

    week_key = get_week_key(date)
    reports = load_reports()
    data = reports.get(week_key)

    if not data:
        await query.message.edit_text("⚠️ Không có dữ liệu cho tuần này.")
        return

    week_title = f"🗓️ Lịch Sử Tuần {get_week_range(date)}"
    header = "ID | Name       | Type | Amount"
    lines = []
    for idx, (person, entry) in enumerate(data.items(), 1):
        icon = "🟢" if entry["tientuan"] > 0 else "🔴"
        label = "Bù" if entry["tientuan"] > 0 else "Thu"
        amount = f"{entry['tientuan']:,}"
        lines.append(f"{idx:02} | {person:<10} | {icon} {label:<3} | {amount} VNĐ")

    msg = f"<pre>{week_title}\n{header}\n" + "\n".join(lines) + "</pre>"
    await query.message.edit_text(msg, parse_mode="HTML")

def register(dp):
    dp.register_callback_query_handler(weekly_menu, lambda c: c.data == "weekly_menu")
    dp.register_callback_query_handler(start_weekly_report, lambda c: c.data == "weekly_start")
    dp.register_callback_query_handler(show_history_menu, lambda c: c.data == "weekly_history")
    dp.register_callback_query_handler(handle_choose_person, lambda c: c.data.startswith("choose_"), state=WeeklyReportState.choosing_person)
    dp.register_callback_query_handler(enter_rate_callback, lambda c: c.data.startswith("rate_"), state=WeeklyReportState.entering_rate)
    dp.register_callback_query_handler(handle_custom_rate, lambda c: c.data == "custom_rate", state=WeeklyReportState.entering_rate)
    dp.register_callback_query_handler(finish_report_callback, lambda c: c.data == "finish_report", state=WeeklyReportState.choosing_person)
    dp.register_message_handler(enter_custom_rate, state=WeeklyReportState.custom_rate)
    dp.register_message_handler(add_member, state=WeeklyReportState.adding_member)
    dp.register_message_handler(enter_amount, state=WeeklyReportState.entering_amount)
    dp.register_callback_query_handler(show_history_detail, lambda c: c.data in ["history_this_week", "history_last_week"])
    dp.register_callback_query_handler(show_all_weeks_report, lambda c: c.data == "weekly_all_history")
