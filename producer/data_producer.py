# producer/data_producer.py
import csv
import os
import random
import time
from datetime import datetime

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "stream_data")
os.makedirs(OUT_DIR, exist_ok=True)
STREAM_FILE = os.path.join(OUT_DIR, "live_stream.csv")

FIELDS = ["patient_name","patient_id","heart_rate","systolic","diastolic","temperature","oxygen","timestamp"]

# sample patients
PATIENTS = [
    {"patient_id": 1001, "patient_name": "Asha Sharma"},
    {"patient_id": 1002, "patient_name": "Ravi Patel"},
    {"patient_id": 1003, "patient_name": "Meera Gupta"},
    {"patient_id": 1004, "patient_name": "Raj Singh"},
    {"patient_id": 1005, "patient_name": "Priya Das"},
]

# initialize file with header if not exists
if not os.path.exists(STREAM_FILE):
    with open(STREAM_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()

print("Producer started — emitting vitals for multiple patients every 2 seconds.")
try:
    while True:
        rows = []
        for p in PATIENTS:
            row = {
                "patient_name": p["patient_name"],
                "patient_id": p["patient_id"],
                "heart_rate": random.randint(55, 120),
                "systolic": random.randint(100, 160),
                "diastolic": random.randint(60, 100),
                "temperature": round(random.uniform(36.0, 39.0), 1),
                "oxygen": round(random.uniform(90.0, 99.0), 1),
                "timestamp": datetime.utcnow().isoformat()
            }
            rows.append(row)
        # append rows to CSV (acts as a simple message queue)
        with open(STREAM_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            for r in rows:
                writer.writerow(r)
                print("Produced:", r)
        time.sleep(2)
except KeyboardInterrupt:
    print("Producer stopped by user.")
