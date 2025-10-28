import great_expectations as ge
import pandas as pd

df = pd.read_csv("data/iot_vitals.csv")
gdf = ge.from_pandas(df)

gdf.expect_column_values_to_not_be_null("patient_id")
gdf.expect_column_values_to_be_between("heart_rate", 50, 140)
gdf.expect_column_values_to_match_regex("blood_pressure", r"\d{2,3}/\d{2,3}")

results = gdf.validate()
print(results)
