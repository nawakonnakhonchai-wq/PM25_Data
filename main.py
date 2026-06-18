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
            
            # โครงสร้าง GeoJSON
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }

            for station in raw_data.get('stations', []):
                # ข้ามสถานีที่ไม่มีพิกัด
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
                        "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "PM25_value": float(aqi_info.get("PM25", {}).get("value", -1)),
                        "PM25_aqi": int(aqi_info.get("PM25", {}).get("aqi", -1)),
                        "overall_aqi": int(aqi_info.get("AQI", {}).get("aqi", -1)),
                        "stationType": station.get('stationType')
                    }
                }
                geojson["features"].append(feature)
            
            # บันทึกเป็นไฟล์ .geojson
            output_file = "air_quality.geojson"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(geojson, f, ensure_ascii=False, indent=4)
            
            print(f"[+] สร้างไฟล์ {output_file} สำเร็จ!")
            return True
    except Exception as e:
        print(f"[-] เกิดข้อผิดพลาด: {e}")
        return False

if __name__ == "__main__":
    fetch_air_quality_to_geojson()
