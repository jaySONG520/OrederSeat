import requests
import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# 配置参数
OPEN_ID = 'oBTGB5P68o7-XW-OhgeCrKyFdsGY'
ACCESS_TOKEN = '435cc5872307437b97a2c844d04fb4f1'
CENTER_ID = 38
PREFERRED_SEATS = [1,2,3,4,5,6,7,8,9,12,13,14,15]
MAX_WORKERS = 20
RETRY_INTERVAL = 180  # 每次失败等待3分钟

headers = {
    "xweb_xhr": "1",
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 MicroMessenger/7.0.20.1781(0x6700143B)",
    "Referer": "https://servicewechat.com/wxb3e386ddfe6d15f9/13/page-frame.html"
}

lock = threading.Lock()
success = False  # 全局预约成功标志

def get_tomorrow():
    return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

def get_available_seats():
    url = f"https://changguan.yunlib.cn/api/mod/venue/seat/list?openId={OPEN_ID}&id={CENTER_ID}&day={get_tomorrow()}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        seat_list = data.get("data", {}).get("seatList", [])
        return [seat["seatNumber"] for seat in seat_list if seat["status"] == 0]
    except Exception as e:
        print("🚫 查询空位失败：", e)
        return []

def reserve(seat_number):
    global success
    while not success:
        url = "https://changguan.yunlib.cn/api/mod/venue/reserve"
        data = {
            "openId": OPEN_ID,
            "day": get_tomorrow(),
            "touristList": "",
            "id": CENTER_ID,
            "seatNumberList": seat_number
        }
        try:
            res = requests.post(url, headers=headers, data=data, timeout=10)
            result = res.json()
            msg = result.get("msg", "")
            if result.get("code") == 200:
                with lock:
                    success = True
                print(f"✅ 成功预约座位号 {seat_number}")
                check_reservation_success()
                return
            elif "已有预约记录" in msg:
                with lock:
                    success = True
                print(f"⚠️ {seat_number} 提示已有预约，将直接查询当前预约记录")
                check_reservation_success()
                return
            else:
                print(f"❌ 座位 {seat_number} 预约失败：{msg}，{RETRY_INTERVAL//60}分钟后重试")
        except Exception as e:
            print(f"⚠️ 座位 {seat_number} 异常：{e}")
        time.sleep(RETRY_INTERVAL)

def check_reservation_success():
    url = f"https://changguan.yunlib.cn/api/mod/venue/enrol?openId={OPEN_ID}&status=0&page=1&limit=10"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        records = data.get("data", {}).get("records", [])
        if not records:
            print("📭 没有查到预约记录")
            return
        print("📌 当前预约记录：")
        for rec in records:
            print(f"🪑 座位：{rec.get('seatNumberList')} | 日期：{rec.get('day')} | 状态：{rec.get('status')}")
    except Exception as e:
        print("❌ 获取预约记录失败：", e)

def main():
    print("🚀 自动预约抢座开始")
    available = get_available_seats()
    print(f"🎯 可预约：{available}")

    target_seats = [s for s in PREFERRED_SEATS if s in available]
    other_seats = [s for s in available if s not in PREFERRED_SEATS]
    seats_to_try = target_seats + other_seats

    if not seats_to_try:
        print("❌ 当前无可预约座位")
        return

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for seat in seats_to_try:
            executor.submit(reserve, seat)

if __name__ == "__main__":
    main()
