import requests
import json
from datetime import datetime

def fetch_air_quality_to_geojson():
    url = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            raw_data = response.json()
            
            geojson = {
                "type": "FeatureCollection",
                "metadata": {
                    "last_updated_thai": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                "features": []
            }

            for station in raw_data.get('stations', []):
                if not station.get('lat') or not station.get('long'):
                    continue
                
                aqi_info = station.get('AQILast', {})
                
                # รวมวันที่และเวลาเป็นฟอร์แมตที่ ArcGIS ชอบ: YYYY-MM-DD HH:MM:00
                date_val = aqi_info.get('date', '1900-01-01')
                time_val = aqi_info.get('time', '00:00')
                combined_timestamp = f"{date_val} {time_val}:00"

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
                        "timestamp": combined_timestamp, # ArcGIS จะจำว่าเป็น Field วันที่โดยอัตโนมัติ
                        "PM25_value": float(aqi_info.get("PM25", {}).get("value", -1)),
                        "PM25_aqi": int(aqi_info.get("PM25", {}).get("aqi", -1)),
                        "overall_aqi": int(aqi_info.get("AQI", {}).get("aqi", -1)),
                        "stationType": station.get('stationType')
                    }
                }
                geojson["features"].append(feature)
            
            with open("air_quality.geojson", "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False, indent=4)
            
            print(f"[+] สร้างไฟล์ air_quality.geojson สำเร็จ! พร้อมคอลัมน์ timestamp")
            return True
    except Exception as e:
        print(f"[-] เกิดข้อผิดพลาด: {e}")
        return False

if __name__ == "__main__":
    fetch_air_quality_to_geojson()
