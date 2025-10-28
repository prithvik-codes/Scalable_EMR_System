from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StringType, IntegerType

spark = SparkSession.builder \
    .appName("EMRStreamProcessor") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

schema = StructType() \
    .add("patient_id", IntegerType()) \
    .add("name", StringType()) \
    .add("age", IntegerType()) \
    .add("gender", StringType()) \
    .add("diagnosis", StringType()) \
    .add("doctor", StringType()) \
    .add("admission_date", StringType()) \
    .add("city", StringType())

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "hospital_records") \
    .load()

# Convert Kafka messages to DataFrame
json_df = df.selectExpr("CAST(value AS STRING)")
parsed_df = json_df.select(from_json(col("value"), schema).alias("data")).select("data.*")

# Add processing timestamp
processed_df = parsed_df.withColumn("processed_at", current_timestamp())

# Write stream to console (or database)
query = processed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .option("truncate", False) \
    .start()

query.awaitTermination()
