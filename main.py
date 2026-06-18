import requests
import json
from datetime import datetime, timedelta

def fetch_air_quality_to_geojson():
    url = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            raw_data = response.json()
            
            # คำนวณเวลาไทย (UTC+7) สำหรับ Metadata ของไฟล์
            time_th_now = datetime.utcnow() + timedelta(hours=7)
            
            geojson = {
                "type": "FeatureCollection",
                "metadata": {
                    "last_updated_utc": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                    "last_updated_thai": time_th_now.strftime('%Y-%m-%d %H:%M:%S')
                },
                "features": []
            }

            for station in raw_data.get('stations', []):
                if not station.get('lat') or not station.get('long'):
                    continue
                
                aqi_info = station.get('AQILast', {})
                
                # สร้าง Feature
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(station['long']), float(station['lat'])]
                    },
                    "properties": {
                        "stationID": station.get('stationID'),
                        "nameTH": station.get('nameTH'),
                        "nameEN": station.get('nameEN'),
                        # เพิ่มช่องเวลาไทยโดยเฉพาะ (แปลงจาก string ใน API)
                        "time_th": aqi_info.get('time'), # ของเดิมเป็นเวลาไทยจาก API อยู่แล้ว
                        "date_th": aqi_info.get('date'),
                        "PM25_value": float(aqi_info.get("PM25", {}).get("value", -1)),
                        "PM25_aqi": int(aqi_info.get("PM25", {}).get("aqi", -1)),
                        "overall_aqi": int(aqi_info.get("AQI", {}).get("aqi", -1)),
                        "stationType": station.get('stationType')
                    }
                }
                geojson["features"].append(feature)
            
            with open("air_quality.geojson", "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False, indent=4)
            
            print(f"[+] สร้างไฟล์ air_quality.geojson พร้อมเวลาไทยเรียบร้อยแล้ว!")
            return True
    except Exception as e:
        print(f"[-] เกิดข้อผิดพลาด: {e}")
        return False

if __name__ == "__main__":
    fetch_air_quality_to_geojson()
