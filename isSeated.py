import requests

# 配置
OPEN_ID = 'oBTGB5P68o7-XW-OhgeCrKyFdsGY'
ACCESS_TOKEN = '435cc5872307437b97a2c844d04fb4f1'

headers = {
    "xweb_xhr": "1",
    "access-token": ACCESS_TOKEN,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 MicroMessenger/7.0.20.1781(0x6700143B)",
    "Referer": "https://servicewechat.com/wxb3e386ddfe6d15f9/13/page-frame.html"
}

def check_reservation_success():
    url = f"https://changguan.yunlib.cn/api/mod/venue/enrol?openId={OPEN_ID}&status=0&page=1&limit=10"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        records = data.get("data", {}).get("records", [])
        if not records:
            print("📭 没有查到任何当前有效预约记录")
            return
        print("📌 当前预约记录如下：")
        for rec in records:
            seat = rec.get('seatNumberList')
            day = rec.get('day')
            venue = rec.get('title') or '未知场馆'
            print(f"🪑 场馆：{venue} | 座位：{seat} | 日期：{day}")
    except Exception as e:
        print("❌ 获取预约记录失败：", e)

if __name__ == "__main__":
    check_reservation_success()
