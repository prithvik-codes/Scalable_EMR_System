# app/dashboard.py
import streamlit as st
import pandas as pd
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.db import SessionLocal, engine, Base
from db.db import SessionLocal, engine, Base
from db.models import Patient, Vitals, MedicalRecord
from sqlalchemy import desc, func
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Scalable EMR Dashboard", layout="wide")
Base.metadata.create_all(bind=engine)

def get_patients():
    session = SessionLocal()
    try:
        return session.query(Patient).order_by(Patient.name).all()
    finally:
        session.close()

def get_patient_details(patient_id):
    session = SessionLocal()
    try:
        patient = session.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None
        vitals = session.query(Vitals).filter(Vitals.patient_id == patient_id).order_by(Vitals.recorded_at).all()
        records = session.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).order_by(desc(MedicalRecord.created_at)).all()
        return patient, vitals, records
    finally:
        session.close()

def add_medical_record(patient_id, diagnosis, prescription, doctor):
    session = SessionLocal()
    try:
        rec = MedicalRecord(patient_id=patient_id, diagnosis=diagnosis, prescription=prescription, doctor=doctor)
        session.add(rec)
        session.commit()
        return True
    except:
        session.rollback()
        return False
    finally:
        session.close()

# --- UI ---
st.title("🏥 Scalable EMR — Demo Dashboard")
st.markdown("**Department of Computer Science & Engineering — Project Demo**")

cols = st.columns([1,3])
with cols[0]:
    st.subheader("Patients")
    patients = get_patients()
    patient_map = {p.name: p.id for p in patients}
    patient_names = list(patient_map.keys())
    selected = st.selectbox("Select patient", ["-- Select --"] + patient_names)
    if selected and selected != "-- Select --":
        pid = patient_map[selected]
    else:
        pid = None

    st.markdown("---")
    if st.button("Refresh Patients"):
        st.rerun()

    st.markdown("**Quick Stats**")
    # global stats
    session = SessionLocal()
    try:
        total_patients = session.query(func.count(Patient.id)).scalar()
        total_vitals = session.query(func.count(Vitals.id)).scalar()
    finally:
        session.close()
    st.write(f"Total patients: **{total_patients}**")
    st.write(f"Total vitals records: **{total_vitals}**")

with cols[1]:
    if not pid:
        st.info("Select a patient to view details or refresh to load sample data.")
    else:
        patient, vitals, records = get_patient_details(pid)
        st.header(f"{patient.name}  •  {patient.age or '-'} yrs  •  {patient.gender or '-'}")
        st.write(f"Contact: {patient.contact or '-'}")
        st.write(f"Address: {patient.address or '-'}")

        # Recent vitals
        if len(vitals) == 0:
            st.warning("No vitals recorded yet for this patient.")
        else:
            df_v = pd.DataFrame([{
                "recorded_at": v.recorded_at,
                "heart_rate": v.heart_rate,
                "systolic": v.systolic,
                "diastolic": v.diastolic,
                "temperature": v.temperature,
                "oxygen": v.oxygen
            } for v in vitals])
            df_v["recorded_at"] = pd.to_datetime(df_v["recorded_at"])
            df_v = df_v.sort_values("recorded_at")

            st.subheader("Vitals over time")
            fig = px.line(df_v, x="recorded_at", y=["heart_rate", "systolic", "diastolic", "temperature", "oxygen"],
                          labels={"value":"Value","recorded_at":"Recorded At"}, height=350)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Medical Records")
        if len(records) == 0:
            st.info("No medical records found.")
        else:
            for r in records:
                st.markdown(f"**{r.doctor or 'Doctor'}** — *{r.created_at.strftime('%Y-%m-%d %H:%M')}*")
                st.markdown(f"- **Diagnosis:** {r.diagnosis}")
                st.markdown(f"- **Prescription:** {r.prescription}")
                st.markdown("---")

        st.subheader("Add Medical Record")
        with st.form("record_form", clear_on_submit=True):
            diag = st.text_area("Diagnosis", height=80)
            presc = st.text_area("Prescription", height=80)
            doc = st.text_input("Doctor name")
            submitted = st.form_submit_button("Add Record")
            if submitted:
                ok = add_medical_record(pid, diag, presc, doc)
                if ok:
                    st.success("Record added.")
                    st.rerun()
                else:
                    st.error("Failed to add record.")
