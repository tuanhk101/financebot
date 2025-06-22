from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery
from features import manage_fund, weekly_report
from features.weekly_report import show_all_weeks_report
from features.weekly_report import handle_backup
# ✅ Định nghĩa trực tiếp start_handler tại đây
async def start_handler(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💰 Quản Lý Quỹ", callback_data="fund_menu"),
        types.InlineKeyboardButton("📊 Báo Cáo Tuần", callback_data="weekly_menu"),
        types.InlineKeyboardButton("📊 Tổng hợp", callback_data="weekly_all_history")
    )
    await message.answer("📋 Chọn chức năng:", reply_markup=keyboard)

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_handler, commands="start")

    dp.register_callback_query_handler(manage_fund.fund_menu, lambda c: c.data == "fund_menu")
    dp.register_callback_query_handler(weekly_report.weekly_menu, lambda c: c.data == "weekly_menu")
    dp.register_message_handler(show_all_weeks_report, commands=["history_all"])
    manage_fund.register(dp)
    weekly_report.register(dp)
    dp.register_message_handler(show_all_weeks_report, commands=["history_all"])
    dp.register_callback_query_handler(show_all_weeks_report, lambda c: c.data == "weekly_all_history")
    dp.register_callback_query_handler(handle_backup, lambda c: c.data == "weekly_backup")

