import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("postgresql://postgres:root@localhost:5432/emr_db")
df = pd.read_sql("SELECT * FROM iot_vitals_cleaned", engine)

st.set_page_config(page_title="EMR Dashboard", layout="wide")
st.title("🏥 Electronic Medical Records Dashboard")

col1, col2 = st.columns(2)
with col1:
    st.metric("Average Heart Rate", round(df['heart_rate'].mean(), 2))
with col2:
    st.metric("Average Temperature (°C)", round(df['temperature_C'].mean(), 2))

st.subheader("Diagnosis Counts (Simulated)")
diagnosis_df = pd.DataFrame({
    "diagnosis": ["Asthma", "Diabetes", "Flu", "Migraine", "Hypertension"],
    "count": [45, 30, 25, 15, 20]
})
st.bar_chart(diagnosis_df.set_index("diagnosis"))

st.subheader("Raw Data View")
st.dataframe(df.head(10))
