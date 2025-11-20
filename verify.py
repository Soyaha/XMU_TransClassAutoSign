import uuid
import threading, asyncio, aiohttp
import requests
import time
import json
from get_config import get_config_path
from concurrent.futures import ThreadPoolExecutor, as_completed

with open(get_config_path()) as f:
    config = json.load(f)
    #latitude = config["latitude"]
    #longitude = config["longitude"]
    locations = config.get("locations", []) # 使用 .get 避免在 "locations" 不存在时报错

def pad(i):
    return str(i).zfill(4)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://ids.xmu.edu.cn/authserver/login",
}
base_url = "https://lnt.xmu.edu.cn"
async def send_code_async(session, rollcall_id):
    cookies = {cookie.name: cookie.value for cookie in session.cookies}
    url = f"{base_url}/api/rollcall/{rollcall_id}/answer_number_rollcall"
    found_code = None
    stop_flag = asyncio.Event()

    async def put_request(session, i):
        nonlocal found_code
        if stop_flag.is_set():
            return None

        payload = {
            "deviceId": str(uuid.uuid4()),
            "numberCode": pad(i)
        }
        try:
            async with session.put(url, data=payload, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    stop_flag.set()
                    found_code = pad(i)
                    return pad(i)
        except asyncio.CancelledError:
            raise
        except Exception:
            return None
        return None
    
    t00 = time.time()

    connector = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, connector=connector) as client_session:
        tasks = [asyncio.create_task(put_request(client_session, i)) for i in range(10000)]
        pending = set(tasks)
        try:
            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for d in done:
                    try:
                        res = d.result()
                    except Exception:
                        res = None
                    if res:
                        for p in pending:
                            p.cancel()
                        await asyncio.gather(*pending, return_exceptions=True)
                        t01 = time.time()
                        print(f"Code {res} found in {t01 - t00:.2f} seconds.")
                        return True
            t01 = time.time()
            print("Failed. \nDuration: %.2f s" % (t01 - t00))
            return False
        finally:
            for p in pending:
                p.cancel()
                await asyncio.gather(*pending, return_exceptions=True)

def send_code(session, rollcall_id):
    return asyncio.run(send_code_async(session, rollcall_id))
def send_radar(driver, rollcall_id, latitude, longitude):
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer?api_version=1.76"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "accuracy": 35,  # 精度，写无限大会不会在哪都能签？
        "altitude": 0,
        "altitudeAccuracy": None,
        "deviceId": str(uuid.uuid1()),
        "heading": None,
        "latitude": latitude,
        "longitude": longitude,
        "speed": None
    }
    res = requests.put(url, json=payload, headers=headers, cookies={c['name']: c['value'] for c in driver.get_cookies()})
    if res.status_code == 200:
        return True
    return False

def send_radar_all_locations(driver, rollcall_id):
    """遍历配置文件中所有的地点，尝试进行雷达签到"""
    if not locations:
        print("错误：配置文件中未找到 'locations' 列表或列表为空。")
        return False

    print(f"开始尝试雷达签到，共 {len(locations)} 个地点。")
    for loc in locations:
        loc_name = loc.get("name", "未命名地点")
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        if lat is None or lon is None:
            print(f"跳过地点 '{loc_name}'，因为它缺少经度或纬度。")
            continue

        print(f"正在尝试地点: {loc_name} ({lat}, {lon})")
        # 调用改造后的 send_radar 函数
        if send_radar(driver, rollcall_id, lat, lon):
            print(f"成功！在地点 '{loc_name}' 签到成功。")
            return True
        else:
            print(f"在 '{loc_name}' 尝试失败，继续下一个地点...")
            time.sleep(1) # 每次尝试后短暂休息，避免请求过快

    print("所有配置的地点都尝试完毕，均未签到成功。")
    return False
