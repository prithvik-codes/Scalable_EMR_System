from pymongo import MongoClient
import json

client = MongoClient("mongodb://localhost:27017/")
db = client["emr_database"]
collection = db["hospital_records"]

with open("data/hospital_records.json", "r") as file:
    data = json.load(file)
    collection.insert_many(data)

print("Inserted records into MongoDB.")
