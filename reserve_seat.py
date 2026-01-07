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
    # ⚠️ 注意：Referer 版本号可能会更新，如果抢座失败请检查是否变为 15 或更高版本
    "Referer": "https://servicewechat.com/wxb3e386ddfe6d15f9/14/page-frame.html"
}

lock = threading.Lock()
success = False  # 全局预约成功标志
available_seats_cache = []  # 缓存查询到的空位列表
seats_query_done = False  # 空位查询是否完成

def get_tomorrow():
    # 转换为 2026/01/08 这种斜杠格式
    return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y/%m/%d')

def get_available_seats():
    """查询可用座位（异步调用，不阻塞主流程）"""
    global available_seats_cache, seats_query_done
    url = f"{BASE_URL}/api/mod/venue/seat/list?openId={OPEN_ID}&id={CENTER_ID}&day={get_tomorrow()}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        seat_list = data.get("data", {}).get("seatList", [])
        available_seats_cache = [seat["seatNumber"] for seat in seat_list if seat["status"] == 0]
        seats_query_done = True
        print(f"📊 后台查询完成，可用座位：{available_seats_cache}")
        return available_seats_cache
    except Exception as e:
        print(f"🚫 查询空位失败：{e}（不影响盲抢策略）")
        seats_query_done = True
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
    print("🚀 自动预约抢座系统启动（盲抢策略）")
    print("=" * 50)
    
    # 精准对时：等待到 21:59:59.850 左右自动触发
    wait_until_target_time()
    
    start_time = time.time()
    print(f"\n🎬 开始抢座！时间：{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print("=" * 50)
    
    # ⚡ 盲抢策略：立即对心仪座位发起抢座，不等待查询结果
    print(f"⚡ 盲抢模式：直接对心仪座位 {PREFERRED_SEATS} 发起抢座...")
    print("📡 同时后台异步查询空位列表（作为备用）\n")
    
    # 启动后台线程异步查询空位（不阻塞主流程）
    def query_seats_background():
        get_available_seats()
    
    query_thread = threading.Thread(target=query_seats_background, daemon=True)
    query_thread.start()
    
    # 立即对心仪座位发起盲抢
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 第一波：直接盲抢心仪座位
        for seat in PREFERRED_SEATS:
            executor.submit(reserve, seat, start_time)
        
        print(f"🚀 已启动 {len(PREFERRED_SEATS)} 个盲抢线程\n")
        
        # 等待一段时间，如果心仪座位都失败，再使用查询到的空位
        fallback_triggered = False
        wait_count = 0
        max_wait = 50  # 最多等待5秒（50 * 0.1秒）后触发备用策略
        
        while not success:
            time.sleep(0.1)
            wait_count += 1
            
            # 如果等待超过一定时间且查询已完成，启动备用座位抢座
            if not fallback_triggered and wait_count >= max_wait and seats_query_done:
                if available_seats_cache:
                    # 过滤掉已经在抢的心仪座位
                    backup_seats = [s for s in available_seats_cache if s not in PREFERRED_SEATS]
                    if backup_seats:
                        print(f"\n🔄 心仪座位暂未成功，启动备用座位抢座：{backup_seats}")
                        for seat in backup_seats:
                            executor.submit(reserve, seat, start_time)
                        fallback_triggered = True
                else:
                    print("\n⚠️ 查询接口无返回或所有座位已被抢完")
                    fallback_triggered = True
        
        print("\n✅ 抢座流程结束")

if __name__ == "__main__":
    main()
