from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import json
import os
from datetime import datetime, timedelta
from utils import current_time

REPORT_FILE = "data/reports.json"
INFO_FILE = "data/baocaotuan.json"

# members = [
#     "Co Hương", "Goem", "Huyen", "Hieu", "Vũ", "Lâm Bình", "Tú", "Vk Gấu", "Thuy", "Bi", "aTha",
#     "Family", "Vinh(PH)", "A6 ATuan", "Aliem", "cHang", "aSang", "a6.4", "Diaky Tuana6", "a6 usa", "a6.2", "a6.3", "atuan.2 a6", "phungD", "Tuan(vani)",
#     "Khang", "Trung", "TH 001", "TH 002", "TH 003", "TH 004", "TH 005", "aha Khang", "Dieu(khangtc) 35%", "Khang ut2", "ut khang"
# ]
members = [
    "Co Huong", "Goem", "Huyền", "Hieu", "Vũ", "Lâm Bình", "Tu", "Vk Gau", "Thuy", "Bi", "Atha",
    "Family", "Vinh", "A6. A Tuan", "ALiem", "CHang", "ASang", "A6.4", "A6.usa", "A6.2", "A6.3", "Phung D", "Tuan(Vani)",
    "Khang", "Trung", "TH 001", "TH 002", "TH 003", "TH 004", "TH 005", "Aha Khang", "Dieu(Khang)", "Khang Ut 2", "Duy Khang", "Ut Khang"
]

class WeeklyReportState(StatesGroup):
    choosing_person = State()
    entering_rate = State()
    entering_amount = State()
    adding_member = State()
    custom_rate = State()

rate_overrides = {}

def load_reports():
    if not os.path.exists(REPORT_FILE):
        return {}
    try:
        with open(REPORT_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def load_info():
    if not os.path.exists(INFO_FILE):
        return {}
    try:
        with open(INFO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_info(info):
    os.makedirs(os.path.dirname(INFO_FILE), exist_ok=True)
    with open(INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

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

# các đoạn xử lý còn lại không thay đổi và sử dụng load_info() để lấy rate/group_master từ file data/baocaotuan.json


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

    # ⛳️ Gán rate cố định từ baocaotuan.json
    info = load_info()
    default_rate = info.get(name, {}).get("rate", 0)
    rate_overrides[name] = default_rate
    await state.update_data(current_rate=default_rate)

    await query.message.answer(
        f"👤 {name} (tỷ lệ: {default_rate}%)\n💵 Nhập số tiền (có thể âm hoặc dương):",
        reply_markup=types.ForceReply(selective=True)
    )
    await WeeklyReportState.entering_amount.set()


async def show_rate_options(message):
    info = load_info()
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Lấy danh sách rate từ baocaotuan.json nếu có
    unique_rates = sorted(set(entry.get("rate", 0) for entry in info.values()))
    for rate in unique_rates:
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
    await query.message.answer(
    "💵 Nhập số tiền (có thể âm hoặc dương):",
    reply_markup=types.ForceReply(selective=True)
    )

    await WeeklyReportState.entering_amount.set()

async def handle_custom_rate(query: CallbackQuery):
    await query.answer()
    await query.message.answer("Gõ tỷ lệ tuỳ chỉnh:")
    await WeeklyReportState.custom_rate.set()
    await query.message.delete() 



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
    data = await state.get_data()
    report_data = data.get("report_data", {})

    if not report_data:
        await query.message.answer("⚠️ Bạn chưa nhập liệu cho ai cả.\nVui lòng nhập thông tin ít nhất 1 người trước khi hoàn thành.")
        return

    await query.message.delete()
    await finish_weekly_report(query.message, state)


async def finish_weekly_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    report_data = data.get("report_data", {})
    if not report_data:
        await message.answer("❌ Không có dữ liệu để lưu.")
        return

    week_key = get_week_key()
    save_report(week_key, report_data)

    # Gửi danh sách tổng hợp trước
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

    # Sau đó gửi từng người bản tóm tắt riêng
    for person, entry in report_data.items():
        amount = entry["amount"]
        rate = entry["rate"]
        tientuan = entry["tientuan"]
        label = "Bù" if tientuan > 0 else "Thu"

        await message.answer(f"👤 {person}")
        await message.answer(f"{amount:,.0f} - {rate:.0f}%\n{label} {tientuan:,}")

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

def register(dp):
    dp.register_callback_query_handler(weekly_menu, lambda c: c.data == "weekly_menu")
    dp.register_callback_query_handler(start_weekly_report, lambda c: c.data == "weekly_start")
    dp.register_callback_query_handler(show_history_menu, lambda c: c.data == "weekly_history")
    dp.register_callback_query_handler(handle_choose_person, lambda c: c.data.startswith("choose_"), state=WeeklyReportState.choosing_person)
    #dp.register_callback_query_handler(enter_rate_callback, lambda c: c.data.startswith("rate_"), state=WeeklyReportState.entering_rate)
    #dp.register_callback_query_handler(handle_custom_rate, lambda c: c.data == "custom_rate", state=WeeklyReportState.entering_rate)
    dp.register_callback_query_handler(finish_report_callback, lambda c: c.data == "finish_report", state=WeeklyReportState.choosing_person)
    #dp.register_message_handler(enter_custom_rate, state=WeeklyReportState.custom_rate)
    dp.register_message_handler(add_member, state=WeeklyReportState.adding_member)
    dp.register_message_handler(enter_amount, state=WeeklyReportState.entering_amount)
    dp.register_callback_query_handler(show_history_detail, lambda c: c.data in ["history_this_week", "history_last_week"])
    dp.register_callback_query_handler(show_all_weeks_report, lambda c: c.data == "weekly_all_history")
    dp.register_callback_query_handler(
    handle_choose_person, lambda c: c.data.startswith("choose_"), state=WeeklyReportState.choosing_person
)

