import os
import time
import pandas as pd
from datetime import datetime
from db.db import engine, SessionLocal, Base
from db.models import Patient, Vitals

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

STREAM_FILE = os.path.join(os.path.dirname(__file__), "..", "stream_data", "live_stream.csv")
print("Looking for stream file at:", os.path.abspath(STREAM_FILE))  # <-- keep this line

def seed_patients_if_needed():
    session = SessionLocal()
    try:
        if session.query(Patient).count() == 0:
            print("Seeding sample patients...")
            patients = [
                {"name": "Asha Sharma", "gender": "F", "age": 34, "contact": "9999999991"},
                {"name": "Ravi Patel", "gender": "M", "age": 45, "contact": "9999999992"},
                {"name": "Meera Gupta", "gender": "F", "age": 28, "contact": "9999999993"},
                {"name": "Raj Singh", "gender": "M", "age": 60, "contact": "9999999994"},
                {"name": "Priya Das", "gender": "F", "age": 50, "contact": "9999999995"},
            ]
            for p in patients:
                session.add(Patient(**p))
            session.commit()
    finally:
        session.close()


def process_once():
    print("🔄 Checking stream file...")
    if not os.path.exists(STREAM_FILE):
        print("Stream file not found.")
        return

    try:
        df = pd.read_csv(STREAM_FILE)
    except Exception as e:
        print("Error reading stream file:", e)
        return

    if df.empty:
        print("No data yet...")
        return

    session = SessionLocal()
    try:
        for _, row in df.iterrows():
            if pd.isna(row.get("patient_name")):
                continue

            p = session.query(Patient).filter(Patient.name == row["patient_name"]).first()
            if not p:
                p = Patient(name=row["patient_name"])
                session.add(p)
                session.flush()

            try:
                ts = datetime.fromisoformat(row["timestamp"])
            except Exception:
                ts = datetime.utcnow()

            vitals = Vitals(
                patient_id=p.id,
                heart_rate=int(row["heart_rate"]),
                systolic=int(row["systolic"]),
                diastolic=int(row["diastolic"]),
                temperature=float(row["temperature"]),
                oxygen=float(row["oxygen"]),
                recorded_at=ts
            )
            session.add(vitals)

        session.commit()
        print(f"✅ Processed {len(df)} rows at {datetime.utcnow().isoformat()}")
        open(STREAM_FILE, "w").close()

    except Exception as e:
        session.rollback()
        print("❌ Processing error:", e)
    finally:
        session.close()


if __name__ == "__main__":
    seed_patients_if_needed()
    print("Processor started. Polling every 5s. Ctrl+C to stop.")
    try:
        while True:
            process_once()
            time.sleep(5)
    except KeyboardInterrupt:
        print("Stopped.")
