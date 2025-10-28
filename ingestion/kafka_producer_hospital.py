# kafka_producer_hospital.py
from kafka import KafkaProducer
import json, time, random
from faker import Faker

fake = Faker()
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

diagnoses = ["Asthma", "Diabetes", "Hypertension", "Migraine", "Flu"]

while True:
    record = {
        "patient_id": random.randint(1000, 2000),
        "name": fake.name(),
        "age": random.randint(18, 80),
        "gender": random.choice(["Male", "Female"]),
        "diagnosis": random.choice(diagnoses),
        "doctor": fake.name(),
        "admission_date": str(fake.date_this_year()),
        "city": fake.city()
    }
    producer.send('hospital_records', record)
    print("Sent hospital record:", record)
    time.sleep(3)
