
import json
from datetime import datetime
from zoneinfo import ZoneInfo  # ✅ CHUẨN giờ theo hệ thống
import pytz
FUND_FILE = "data/fund.json"

def load_fund():
    try:
        with open(FUND_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"accounts": [], "members": [], "transactions": []}

def save_fund(data):
    with open(FUND_FILE, "w", encoding="utf-8") as f:
        f.write('{\n  "accounts": ' + json.dumps(data["accounts"], ensure_ascii=False) + ',\n')
        f.write('  "members": ' + json.dumps(data["members"], ensure_ascii=False) + ',\n')
        f.write('  "transactions": [\n')
        for i, t in enumerate(data["transactions"]):
            line = json.dumps(t, ensure_ascii=False, separators=(',', ':'))
            comma = ',' if i < len(data["transactions"]) - 1 else ''
            f.write(f"    {line}{comma}\n")
        f.write('  ]\n}')


import pendulum

def current_time():
    now = pendulum.now("Asia/Ho_Chi_Minh")
    formatted = now.format("DD-MM HH:mm")  # ⬅️ định dạng cũ
    print("✅ current_time:", formatted)
    return formatted