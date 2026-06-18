import requests
import json
from datetime import datetime

def fetch_air_quality():
    """
    ดึงข้อมูลคุณภาพอากาศจาก Air4Thai และบันทึกเป็นไฟล์ JSON ที่สะอาด
    """
    url = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            raw_data = response.json()
            
            # เตรียมโครงสร้างสำหรับบันทึก
            processed_data = {
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_stations": len(raw_data.get('stations', [])),
                "stations": []
            }

            for station in raw_data.get('stations', []):
                aqi_info = station.get('AQILast', {})
                
                # กรองเฉพาะค่าสารมลพิษที่มีอยู่จริงใน API
                pollutants = {}
                for p in ["PM25", "PM10", "O3", "CO", "NO2", "SO2"]:
                    if p in aqi_info:
                        # เก็บค่าข้อมูลและสถานะสี
                        pollutants[p] = {
                            "value": float(aqi_info[p].get("value", -1)),
                            "aqi": int(aqi_info[p].get("aqi", -1)),
                            "color_id": aqi_info[p].get("color_id", "0")
                        }

                # รวมข้อมูลสถานี
                record = {
                    "stationID": station.get('stationID'),
                    "nameTH": station.get('nameTH'),
                    "nameEN": station.get('nameEN'),
                    "lat": station.get('lat'),
                    "long": station.get('long'),
                    "date": aqi_info.get('date'),
                    "time": aqi_info.get('time'),
                    "pollutants": pollutants,
                    "overall_aqi": aqi_info.get('AQI')
                }
                processed_data["stations"].append(record)
            
            # บันทึกเป็นไฟล์ JSON
            output_file = "air_quality_latest.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=4)
            
            print(f"[+] อัปเดตข้อมูลสำเร็จ: {output_file}")
            return True
        else:
            print(f"[-] ไม่สามารถเชื่อมต่อ API ได้ (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"[-] เกิดข้อผิดพลาดในระบบ: {str(e)}")
        return False

if __name__ == "__main__":
    fetch_air_quality()
