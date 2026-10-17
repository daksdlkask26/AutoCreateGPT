import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT_DIR / "data" / "input" / "Bin.csv"
OUTPUT_FILE = ROOT_DIR / "data" / "output" / "Bin.json"

print("Converting Bin.csv to Bin.json...")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    bin_lines = [line.strip() for line in f if line.strip()]

bin_data = []
for i, line in enumerate(bin_lines, start=1):
    parts = [x.strip() for x in line.split(",")]
    if len(parts) != 4:
        print(f"Skip line {i}: wrong format -> {line}")
        continue

    cardNumber, expireMonth, expireYear, cvv = parts

    bin_data.append({
        "id": i,  # nếu bạn muốn id dạng string
        "name": "정민규",
        "billing": {
            "street": "17 Garosu-gil",
            "district": "Gangnam-gu",
            "city": "Seoul",
            "postalCode": "06035",
            "country": "South Korea",
            "countryCode": "KR"
        },
        "payment": {
            "cardNumber": cardNumber,
            "expireMonth": expireMonth,
            "expireYear": expireYear,
            "cvv": cvv,
            "cardType": "Visa"
        },
        "contact": {
            "firstName": "민규",
            "lastName": "정",
            "fullName": "정민규",
            "email": "",
            "phone": "+82-10-1234-5678"
        }
    })

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(bin_data, f, indent=4, ensure_ascii=False)

print("Done -> Bin.json")
