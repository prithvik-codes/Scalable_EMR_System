# simulator/simulator.py
import threading
import time
import random
from datetime import datetime
from db.db import SessionLocal, Base, engine
from db.models import Patient, Vitals

# ensure tables exist
Base.metadata.create_all(bind=engine)

# Settings
DEFAULT_INTERVAL = 3.0   # seconds between inserts for each patient

# Control objects
_sim_thread = None
_stop_event = None

SAMPLE_PATIENTS = [
    {"name": "Asha Sharma", "gender": "F", "age": 34, "contact": "9999999991"},
    {"name": "Ravi Patel", "gender": "M", "age": 45, "contact": "9999999992"},
    {"name": "Meera Gupta", "gender": "F", "age": 28, "contact": "9999999993"},
    {"name": "Raj Singh", "gender": "M", "age": 60, "contact": "9999999994"},
    {"name": "Priya Das", "gender": "F", "age": 50, "contact": "9999999995"},
]

def seed_patients_if_needed():
    session = SessionLocal()
    try:
        if session.query(Patient).count() == 0:
            for p in SAMPLE_PATIENTS:
                session.add(Patient(**p))
            session.commit()
            print("Simulator: seeded sample patients.")
    finally:
        session.close()

def _make_vitals(patient_id):
    return Vitals(
        patient_id=patient_id,
        heart_rate=random.randint(55, 120),
        systolic=random.randint(100, 160),
        diastolic=random.randint(60, 100),
        temperature=round(random.uniform(36.0, 39.0), 1),
        oxygen=round(random.uniform(90.0, 99.0), 1),
        recorded_at=datetime.utcnow()
    )

def _run_simulator(interval):
    """
    Background thread target: insert vitals for every patient on each loop.
    """
    session = SessionLocal()
    try:
        # fetch patients snapshot
        pts = session.query(Patient).all()
        if not pts:
            print("Simulator: no patients found (seed first).")
            return
    finally:
        session.close()

    print("Simulator started; inserting vitals every", interval, "sec.")
    global _stop_event
    while not _stop_event.is_set():
        session = SessionLocal()
        try:
            patients = session.query(Patient).all()
            for p in patients:
                v = _make_vitals(p.id)
                session.add(v)
                # optional: print small log
                # print(f"[SIM] {p.name} HR={v.heart_rate} O2={v.oxygen}")
            session.commit()
        except Exception as e:
            session.rollback()
            print("Simulator error:", e)
        finally:
            session.close()
        # wait interval seconds but break early if stop requested
        for _ in range(int(interval * 10)):
            if _stop_event.is_set():
                break
            time.sleep(0.1)
    print("Simulator stopped.")

def start_simulation(interval=DEFAULT_INTERVAL):
    """
    Start simulator in background thread. No-op if already running.
    """
    global _sim_thread, _stop_event
    if _sim_thread and _sim_thread.is_alive():
        return False  # already running
    seed_patients_if_needed()
    _stop_event = threading.Event()
    _sim_thread = threading.Thread(target=_run_simulator, args=(interval,), daemon=True)
    _sim_thread.start()
    return True

def stop_simulation():
    global _sim_thread, _stop_event
    if _stop_event:
        _stop_event.set()
    _sim_thread = None
    _stop_event = None
    return True

def is_running():
    global _sim_thread
    return bool(_sim_thread and _sim_thread.is_alive())
