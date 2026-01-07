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
RETRY_INTERVAL = 180  # 每次失败等待3分钟（高峰期会自动调整为0.1秒）
BASE_URL = "https://order-admin-ext.bnszwhw.cn"

headers = {
    "xweb_xhr": "1",
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 MicroMessenger/7.0.20.1781(0x6700143B)",
    "Referer": "https://servicewechat.com/wxb3e386ddfe6d15f9/14/page-frame.html"
}

lock = threading.Lock()
success = False  # 全局预约成功标志

def get_tomorrow():
    # 转换为 2026/01/08 这种斜杠格式
    return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y/%m/%d')

def get_available_seats():
    url = f"{BASE_URL}/api/mod/venue/seat/list?openId={OPEN_ID}&id={CENTER_ID}&day={get_tomorrow()}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        seat_list = data.get("data", {}).get("seatList", [])
        return [seat["seatNumber"] for seat in seat_list if seat["status"] == 0]
    except Exception as e:
        print("🚫 查询空位失败：", e)
        return []

def reserve(seat_number, start_time=None):
    global success
    while not success:
        # 计算动态重试间隔：高峰期前30秒使用0.1秒，之后使用正常间隔
        if start_time:
            elapsed = time.time() - start_time
            if elapsed < 30:  # 前30秒高峰期
                retry_interval = 0.1
            else:
                retry_interval = RETRY_INTERVAL
        else:
            retry_interval = RETRY_INTERVAL
        
        url = f"{BASE_URL}/api/mod/venue/reserve"
        data = {
            "openId": OPEN_ID,
            "day": get_tomorrow(),
            "touristList": "",
            "id": CENTER_ID,
            "seatNumberList": seat_number
        }
        try:
            res = requests.post(url, headers=headers, data=data, timeout=5)
            result = res.json()
            msg = result.get("msg", "")
            # 核心改动：判断 code 是否为 0
            if result.get("code") == 0:
                with lock:
                    success = True
                print(f"✅ 成功预约座位：{seat_number}")
                check_reservation_success()
                return
            elif "已有预约" in msg or "已有预约记录" in msg:
                with lock:
                    success = True
                print(f"⚠️ 提示已有预约，停止操作")
                check_reservation_success()
                return
            else:
                if retry_interval < 1:
                    print(f"❌ 座位 {seat_number} 预约失败：{msg}，继续重试...")
                else:
                    print(f"❌ 座位 {seat_number} 预约失败：{msg}，{retry_interval//60}分钟后重试")
        except Exception as e:
            print(f"⚠️ 请求异常: {e}")
        time.sleep(retry_interval)

def check_reservation_success():
    url = f"{BASE_URL}/api/mod/venue/enrol?openId={OPEN_ID}&status=0&page=1&limit=10"
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

def wait_until_target_time():
    """精准对时：等待到 21:59:59.850 左右自动触发"""
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=21, minute=59, second=59, microsecond=850000)
        
        # 如果已经过了今天的目标时间，等待明天的
        if now > target_time:
            target_time += datetime.timedelta(days=1)
        
        wait_seconds = (target_time - now).total_seconds()
        
        if wait_seconds > 1:
            print(f"⏰ 当前时间：{now.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"🎯 目标时间：{target_time.strftime('%H:%M:%S.%f')[:-3]}")
            print(f"⏳ 等待 {wait_seconds:.2f} 秒后自动开始...")
            time.sleep(min(wait_seconds - 0.1, 1))  # 提前0.1秒准备
        else:
            # 最后0.1秒内，精确等待
            time.sleep(wait_seconds)
            break

def main():
    print("🚀 自动预约抢座系统启动")
    print("=" * 50)
    
    # 精准对时：等待到 21:59:59.850 左右自动触发
    wait_until_target_time()
    
    start_time = time.time()
    print(f"\n🎬 开始抢座！时间：{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print("=" * 50)
    
    available = get_available_seats()
    print(f"🎯 可预约座位：{available}")

    target_seats = [s for s in PREFERRED_SEATS if s in available]
    other_seats = [s for s in available if s not in PREFERRED_SEATS]
    seats_to_try = target_seats + other_seats

    if not seats_to_try:
        print("❌ 当前无可预约座位")
        return

    print(f"📋 优先座位：{target_seats}")
    print(f"📋 其他座位：{other_seats}")
    print(f"🚀 启动 {len(seats_to_try)} 个并发线程开始抢座...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for seat in seats_to_try:
            executor.submit(reserve, seat, start_time)
        
        # 等待所有任务完成（或成功）
        while not success:
            time.sleep(0.1)

if __name__ == "__main__":
    main()
