import os
import sys
import requests
import urllib3
import json
import traceback
from datetime import datetime

# air4thai.pcd.go.th ส่ง SSL certificate chain มาไม่ครบ (ขาด intermediate cert)
# เบราว์เซอร์ทั่วไปแก้ปัญหานี้ให้เองอัตโนมัติ (AIA chasing) แต่ requests/urllib3 ไม่มีกลไกนี้
# เนื่องจากเป็น public open-data API (ไม่มีข้อมูล sensitive/การ auth) จึงปิดการตรวจสอบ cert
# เฉพาะจุดนี้ และปิด warning ที่จะแสดงออกมาด้วย
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_air_quality_to_geojson():
    url = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(BASE_DIR, "air_quality.geojson")

    print(f"[i] เวลาที่เริ่มรัน: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[i] จะเขียนไฟล์ที่: {output_path}")

    try:
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        print(f"[i] HTTP status: {response.status_code}")
        # พิมพ์ตัวอย่าง response ไว้ debug เผื่อโดน block/redirect เป็นหน้าอื่น
        print(f"[i] Response (200 ตัวอักษรแรก): {response.text[:200]!r}")

        response.raise_for_status()  # โยน exception ถ้า status ไม่ใช่ 2xx แทนที่จะเงียบผ่านไป

        raw_data = response.json()
        stations = raw_data.get('stations', [])
        print(f"[i] จำนวนสถานีที่ได้จาก API: {len(stations)}")

        if not stations:
            raise ValueError("API ส่งข้อมูลว่างเปล่ากลับมา (stations = [])")

        latest_date = max(
            (s.get('AQILast', {}).get('date', '1900-01-01') for s in stations),
            default='1900-01-01'
        )
        print(f"[i] วันที่ล่าสุดที่พบใน API response: {latest_date}")

        geojson = {
            "type": "FeatureCollection",
            "metadata": {
                "last_updated_thai": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "latest_station_date": latest_date,
            },
            "features": []
        }

        skipped = 0
        for station in stations:
            if not station.get('lat') or not station.get('long'):
                skipped += 1
                continue

            aqi_info = station.get('AQILast', {})
            date_val = aqi_info.get('date', '1900-01-01')
            time_val = aqi_info.get('time', '00:00')
            combined_timestamp = f"{date_val} {time_val}:00"

            try:
                pm25_value = float(aqi_info.get("PM25", {}).get("value", -1))
                pm25_aqi = int(aqi_info.get("PM25", {}).get("aqi", -1))
                overall_aqi = int(aqi_info.get("AQI", {}).get("aqi", -1))
            except (ValueError, TypeError) as conv_err:
                print(f"[!] ข้ามสถานี {station.get('stationID')} เพราะแปลงค่าไม่ได้: {conv_err}")
                skipped += 1
                continue

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(station['long']), float(station['lat'])]
                },
                "properties": {
                    "stationID": station.get('stationID'),
                    "nameTH": station.get('nameTH'),
                    "timestamp": combined_timestamp,
                    "PM25_value": pm25_value,
                    "PM25_aqi": pm25_aqi,
                    "overall_aqi": overall_aqi,
                    "stationType": station.get('stationType')
                }
            }
            geojson["features"].append(feature)

        if len(geojson["features"]) == 0:
            raise ValueError("ไม่มี feature ไหนถูกสร้างสำเร็จเลยแม้แต่อันเดียว")

        print(f"[i] สร้าง feature สำเร็จ {len(geojson['features'])} รายการ (ข้าม {skipped} สถานี)")

        tmp_path = output_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, output_path)

        mtime = datetime.fromtimestamp(os.path.getmtime(output_path))
        filesize = os.path.getsize(output_path)
        print(f"[+] เขียนไฟล์สำเร็จ: {output_path}")
        print(f"[+] ขนาดไฟล์: {filesize:,} bytes | แก้ไขล่าสุด: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        return True

    except Exception as e:
        print(f"[-] เกิดข้อผิดพลาด: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = fetch_air_quality_to_geojson()
    if not success:
        # สำคัญมาก: ทำให้ process exit ด้วย code != 0
        # เพื่อให้ GitHub Actions รู้ว่า step นี้ "ล้มเหลวจริง" และขึ้นสีแดงให้เห็นชัดๆ
        sys.exit(1)
