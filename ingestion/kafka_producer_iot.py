# kafka_producer_iot.py
from kafka import KafkaProducer
import json, time, random, datetime

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

while True:
    record = {
        "patient_id": random.randint(1000, 2000),
        "heart_rate": random.randint(60, 120),
        "blood_pressure": f"{random.randint(100,140)}/{random.randint(70,90)}",
        "temperature": round(random.uniform(97.0, 100.5), 1),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    producer.send('iot_vitals', record)
    print("Sent vitals:", record)
    time.sleep(2)
