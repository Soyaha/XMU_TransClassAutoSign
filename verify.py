import uuid
import threading
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

def send_code(driver, rollcall_id):
    stop_flag = threading.Event()
    url = f"https://lnt.xmu.edu.cn/api/rollcall/{rollcall_id}/answer_number_rollcall"

    def put_request(i, headers, cookies):
        if stop_flag.is_set():
            return None
        payload = {
            "deviceId": str(uuid.uuid1()),
            "numberCode": pad(i)
        }
        try:
            r = requests.put(url, json=payload, headers=headers, cookies=cookies, timeout=5)
            if r.status_code == 200:
                stop_flag.set()
                return pad(i)
        except Exception as e:
            pass
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
        "Content-Type": "application/json"
    }
    cookies_list = driver.get_cookies()
    cookies = {c['name']: c['value'] for c in cookies_list}
    print("正在遍历签到码...")
    t00 = time.time()
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(put_request, i, headers, cookies) for i in range(10000)]
        for f in as_completed(futures):
            res = f.result()
            if res is not None:
                print("签到码:", res)
                t01 = time.time()
                print("用时: %.2f 秒" % (t01 - t00))
                return True
    t01 = time.time()
    print("失败。\n用时: %.2f 秒" % (t01 - t00))
    return False

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