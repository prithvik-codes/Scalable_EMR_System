import pandas as pd
from sqlalchemy import create_engine

# Extract CSV data (simulate daily batch)
df = pd.read_csv("data/iot_vitals.csv")

# Transform
df["temperature_C"] = (df["temperature"] - 32) * 5/9
df["bp_systolic"] = df["blood_pressure"].apply(lambda x: int(x.split('/')[0]))
df["bp_diastolic"] = df["blood_pressure"].apply(lambda x: int(x.split('/')[1]))

# Load to PostgreSQL
engine = create_engine("postgresql://postgres:root@localhost:5432/emr_db")
df.to_sql("iot_vitals_cleaned", engine, if_exists="append", index=False)

print("✅ Batch ETL complete: loaded", len(df), "records")
