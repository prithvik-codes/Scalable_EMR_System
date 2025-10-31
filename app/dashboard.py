# app/dashboard.py
import psycopg2
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import func, desc
from db.db import SessionLocal, engine, Base
from db.models import Patient, Vitals, MedicalRecord
from datetime import datetime
from simulator.simulator import start_simulation, stop_simulation, is_running, seed_patients_if_needed

# Page config
st.set_page_config(page_title="Smart EMR Dashboard", layout="wide", initial_sidebar_state="expanded")

# Basic CSS / theme
st.markdown("""
<style>
:root {
  --bg: #f7fafc;
  --card: #ffffff;
  --muted: #6b7280;
  --accent-hr: #e63946;
  --accent-bp: #457b9d;
  --accent-temp: #f4a261;
  --accent-oxy: #2a9d8f;
}
body { background-color: var(--bg); }
.block-container { padding-top: 10px; padding-bottom: 10px; }
.card {
  background: var(--card);
  border-radius: 12px;
  padding: 15px;
  box-shadow: 0px 6px 18px rgba(15,23,42,0.06);
  margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

Base.metadata.create_all(bind=engine)

# Sidebar navigation
st.sidebar.image("https://img.icons8.com/fluency/48/000000/stethoscope.png", width=48)
st.sidebar.title("Scalable EMR — Demo")
page = st.sidebar.radio("Go to", ["Dashboard", "Analytics", "Doctor Portal", "Admin Panel"])

st.sidebar.markdown("---")
st.sidebar.subheader("Simulation")
sim_running = is_running()
colA, colB = st.sidebar.columns([1,1])
with colA:
    if st.button("Start Simulation" if not sim_running else "Running...", disabled=sim_running):
        start_simulation(interval=3.0)
        st.rerun()
with colB:
    if st.button("Stop Simulation" if sim_running else "Stopped", disabled=not sim_running):
        stop_simulation()
        st.rerun()

# Refresh button
st.sidebar.markdown("**Refresh UI**")
if st.sidebar.button("Refresh"):
    st.rerun()

# Helpers
@st.cache_data(ttl=5)
def load_patients():
    s = SessionLocal()
    try:
        return s.query(Patient).order_by(Patient.name).all()
    finally: s.close()

@st.cache_data(ttl=3)
def load_vitals_for_patient(pid, limit=200):
    s = SessionLocal()
    try:
        q = s.query(Vitals).filter(Vitals.patient_id == pid).order_by(Vitals.recorded_at.desc()).limit(limit)
        rows = list(reversed(q.all()))
        return pd.DataFrame([{
            "time": r.recorded_at,
            "heart_rate": r.heart_rate,
            "systolic": r.systolic,
            "diastolic": r.diastolic,
            "temperature": r.temperature,
            "oxygen": r.oxygen
        } for r in rows])
    finally: s.close()

@st.cache_data(ttl=5)
def global_metrics():
    s = SessionLocal()
    try:
        total_patients = s.query(func.count(Patient.id)).scalar()
        total_vitals = s.query(func.count(Vitals.id)).scalar()
        total_records = s.query(func.count(MedicalRecord.id)).scalar()
        alerts = s.query(Vitals, Patient).join(Patient).filter(
            (Vitals.heart_rate > 110) | (Vitals.oxygen < 92) | (Vitals.temperature > 38.0)
        ).order_by(Vitals.recorded_at.desc()).limit(10).all()
        return dict(patients=total_patients, vitals=total_vitals, records=total_records, alerts=alerts)
    finally: s.close()

# ✅ Load Prescriptions
@st.cache_data(ttl=5)
def load_prescriptions(pid):
    s = SessionLocal()
    try:
        recs = (
            s.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == pid)
            .order_by(desc(MedicalRecord.created_at))
            .all()
        )
        return recs
    finally:
        s.close()


# ---------------- DASHBOARD ----------------
if page == "Dashboard":
    metrics = global_metrics()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Patients", metrics["patients"])
    c2.metric("Vitals", metrics["vitals"])
    c3.metric("Reports", metrics["records"])
    c4.metric("Simulation", "Running ✅" if is_running() else "Stopped ❌")

    patients = load_patients()
    pmap = {p.name:p.id for p in patients}
    sel = st.selectbox("Select Patient", ["-- Select --"] + list(pmap.keys()))

    if sel != "-- Select --":
        pid = pmap[sel]
        df = load_vitals_for_patient(pid, 300)
        if df.empty:
            st.warning("No vitals recorded yet")
        else:
            latest = df.iloc[-1]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Heart Rate", latest["heart_rate"])
            c2.metric("BP", f"{latest['systolic']}/{latest['diastolic']}")
            c3.metric("Temp", latest["temperature"])
            c4.metric("O2", latest["oxygen"])

            # ✅ Added Prescriptions tab here
            tabs = st.tabs(["HR", "BP", "Temp", "Oxygen", "Table", "Prescriptions"])

            with tabs[0]:
                f = go.Figure()
                f.add_trace(go.Scatter(x=df.time, y=df.heart_rate, mode="lines+markers"))
                st.plotly_chart(f, use_container_width=True)

            with tabs[1]:
                f = go.Figure()
                f.add_trace(go.Scatter(x=df.time, y=df.systolic, name="Systolic"))
                f.add_trace(go.Scatter(x=df.time, y=df.diastolic, name="Diastolic"))
                st.plotly_chart(f, use_container_width=True)

            with tabs[2]:
                f = go.Figure()
                f.add_trace(go.Scatter(x=df.time, y=df.temperature, mode="lines+markers"))
                st.plotly_chart(f, use_container_width=True)

            with tabs[3]:
                df = df.sort_values("time")
                f = go.Figure()
                f.add_trace(go.Scatter(x=df.time, y=df.oxygen, mode="lines+markers"))
                st.plotly_chart(f, use_container_width=True)

            with tabs[4]:
                st.dataframe(df.tail(25))

            # ✅ Prescription History Tab
            with tabs[5]:
                st.subheader(f"🩺 Prescription Records for {sel}")

                recs = load_prescriptions(pid)

                if not recs:
                    st.info("No prescriptions recorded yet.")
                else:
                    for r in recs:
                        st.markdown(f"""
**👨‍⚕️ Doctor:** {r.doctor}  
**📅 Date:** {r.created_at.strftime('%Y-%m-%d %H:%M')}  
**📌 Diagnosis:** {r.diagnosis}  
💊 Prescription: {r.prescription}""")

# # ---------------- DASHBOARD ----------------
# if page == "Dashboard":
#     metrics = global_metrics()
#     c1,c2,c3,c4 = st.columns(4)
#     c1.metric("Patients", metrics["patients"])
#     c2.metric("Vitals", metrics["vitals"])
#     c3.metric("Reports", metrics["records"])
#     c4.metric("Simulation", "Running ✅" if is_running() else "Stopped ❌")

#     patients = load_patients()
#     pmap = {p.name:p.id for p in patients}
#     sel = st.selectbox("Select Patient", ["-- Select --"] + list(pmap.keys()))

#     if sel != "-- Select --":
#         pid = pmap[sel]
#         df = load_vitals_for_patient(pid, 300)
#         if df.empty:
#             st.warning("No vitals recorded yet")
#         else:
#             latest = df.iloc[-1]
#             c1,c2,c3,c4 = st.columns(4)
#             c1.metric("Heart Rate", latest["heart_rate"])
#             c2.metric("BP", f"{latest['systolic']}/{latest['diastolic']}")
#             c3.metric("Temp", latest["temperature"])
#             c4.metric("O2", latest["oxygen"])

#             tabs = st.tabs(["HR", "BP", "Temp", "Oxygen", "Table"])
#             # Heart rate
#             with tabs[0]:
#                 f = go.Figure()
#                 f.add_trace(go.Scatter(x=df.time, y=df.heart_rate, mode="lines+markers"))
#                 st.plotly_chart(f, use_container_width=True)

#             # BP
#             with tabs[1]:
#                 f = go.Figure()
#                 f.add_trace(go.Scatter(x=df.time, y=df.systolic, name="Systolic"))
#                 f.add_trace(go.Scatter(x=df.time, y=df.diastolic, name="Diastolic"))
#                 st.plotly_chart(f, use_container_width=True)

#             # Temperature
#             with tabs[2]:
#                 f = go.Figure()
#                 f.add_trace(go.Scatter(x=df.time, y=df.temperature, mode="lines+markers"))
#                 st.plotly_chart(f, use_container_width=True)

#             # Oxygen
#             with tabs[3]:
#                 df = df.sort_values("time")
#                 f = go.Figure()
#                 f.add_trace(go.Scatter(x=df.time, y=df.oxygen, mode="lines+markers"))
#                 st.plotly_chart(f, use_container_width=True)

#             with tabs[4]:
#                 st.dataframe(df.tail(25))

#     st.subheader("Recent Alerts")
#     for v,p in metrics["alerts"]:
#         st.write(f"**{p.name}** — HR={v.heart_rate}, BP={v.systolic}/{v.diastolic}, Temp={v.temperature}, O₂={v.oxygen}")

# ---------------- ANALYTICS ----------------

elif page == "Analytics":
    st.header("\n📊 Analytics & Insights\n")
    session = SessionLocal()
    try:
        records = session.query(MedicalRecord).all()
        diag_counts = {}
        for r in records:
            if r.diagnosis:
                diag_counts[r.diagnosis] = diag_counts.get(r.diagnosis,0)+1
        diag_df = pd.DataFrame([{"disease":k,"count":v} for k,v in diag_counts.items()]).sort_values("count", ascending=False)
        if not diag_df.empty:
            st.subheader("Top Diagnoses")
            st.bar_chart(diag_df.set_index("disease")["count"])
        else:
            st.info("No medical records for analytics yet.")

        vitals_df = pd.read_sql("SELECT * FROM vitals", con=engine)
        if not vitals_df.empty:
            avg_by_patient = vitals_df.groupby("patient_id")[["heart_rate","systolic","diastolic","oxygen","temperature"]].mean().reset_index()
            st.subheader("Average Vitals per Patient (sample)")
            st.dataframe(avg_by_patient.head(20))
    finally:
        session.close()


# ---------------- DOCTOR PORTAL ----------------elif page == "Doctor Portal":
elif page == "Doctor Portal":
    st.header("👨‍⚕️ Doctor Portal")

    # ---- Doctor List Handling ----
    if "doctor_list" not in st.session_state:
        # Load existing doctors from medical records
        s = SessionLocal()
        try:
            docs = s.query(MedicalRecord.doctor).distinct().all()
            st.session_state.doctor_list = [d[0] for d in docs if d[0]]
        finally:
            s.close()

    st.subheader("Add / Select Doctor")

    new_doc = st.text_input("Add New Doctor Name")

    if st.button("Add Doctor"):
        if new_doc.strip() and new_doc not in st.session_state.doctor_list:
            st.session_state.doctor_list.append(new_doc.strip())
            st.success(f"✅ Doctor **{new_doc}** added")
        else:
            st.warning("Doctor already exists or name empty")

    doc = st.selectbox("Select Doctor", ["-- Select --"] + st.session_state.doctor_list)

    if doc == "-- Select --":
        st.stop()

    # ---- Select Patient ----
    patients = load_patients()
    pmap = {p.name: p.id for p in patients}
    pat = st.selectbox("Select Patient", list(pmap.keys()))

    diagnosis = st.text_input("Diagnosis")
    notes = st.text_area("Prescription / Notes")

    if st.button("Save Prescription"):
        s = SessionLocal()
        try:
            s.add(MedicalRecord(
                patient_id=pmap[pat],
                doctor=doc,
                diagnosis=diagnosis,
                prescription=notes,
                created_at=datetime.now()
            ))
            s.commit()
            st.success("✅ Prescription saved!")
            st.rerun()
        finally:
            s.close()

    # ---- History ----
    st.subheader(f"📋 Prescription History — Dr. {doc}")
    s = SessionLocal()
    recs = s.query(MedicalRecord).filter(MedicalRecord.doctor == doc).order_by(desc(MedicalRecord.created_at)).all()
    for r in recs:
        p = s.query(Patient).filter_by(id=r.patient_id).first()
        st.write(f"**Patient:** {p.name}  \n**Date:** {r.created_at}  \n**Diagnosis:** {r.diagnosis}  \n**Rx:** {r.prescription}  \n---")
    s.close()



# ---------------- ADMIN PANEL ----------------
elif page == "Admin Panel":
    st.header("Admin Panel")

    if st.button("Seed Sample Patients"):
        seed_patients_if_needed()
        st.success("Seeded sample patients")
        st.rerun()

    st.write("Add Patient")
    with st.form("addp"):
        n = st.text_input("Name")
        age = st.number_input("Age", 1,100)
        g = st.selectbox("Gender", ["M","F","O"])
        c = st.text_input("Contact")
        a = st.text_area("Address")
        if st.form_submit_button("Save"):
            s=SessionLocal()
            s.add(Patient(name=n,age=age,gender=g,contact=c,address=a))
            s.commit()
            s.close()
            st.success("Added")
            st.rerun()

st.write("---")
st.caption("Scalable EMR Simulation System")
