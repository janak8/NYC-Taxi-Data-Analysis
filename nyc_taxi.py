import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, hour, avg, round, when

#Spark session initialization
spark = SparkSession.builder.appName("NYC Taxi Analysis").getOrCreate()

#loading the dataset and converting to the spark dataframe
file_path = "yellow_tripdata_2023-01.csv" 
df = spark.read.csv(file_path, header=True, inferSchema=True)  # It if for the header include and datatype specifying

print("\nInitial DataFrame Schema:")
df.printSchema()  # printing the schema of the dataset (the data types)

# converting to the appropriate datetime columns
df = df.withColumn("tpep_pickup_datetime", to_timestamp(col("tpep_pickup_datetime")))
df = df.withColumn("tpep_dropoff_datetime", to_timestamp(col("tpep_dropoff_datetime")))

print("\nDataFrame after converting datetime columns:")
df.show(5)  # showing the first 5 columns 

df = df.dropna()

print("\nDataFrame after dropping missing values:")
df.show(5)  

# Removing invalid fares and trip distances
df = df.filter((col("fare_amount") > 0) & (col("trip_distance") > 0))   # Fare amount is always greater than 0

print("\nDataFrame after removing invalid fares and trip distances:")
df.show(5)  

df = df.withColumn("pickup_hour", hour(col("tpep_pickup_datetime")))

# creating new column with trip duration in minutes
df = df.withColumn("trip_duration",
                   (col("tpep_dropoff_datetime").cast("long") - col("tpep_pickup_datetime").cast("long")) / 60)

# creating new column with fare per mile
df = df.withColumn("fare_per_mile", col("total_amount") / col("trip_distance"))

# handleling potential division by zero in fare_per_mile
df = df.withColumn("fare_per_mile", when(col("trip_distance") == 0, 0).otherwise(col("fare_per_mile")))

print("\nDataFrame after feature engineering:")
df.show(5)  

# regestring dataframe column as sql table so that we can extract the elements
df.createOrReplaceTempView("taxi_data")

# sql query 
avg_fare_by_passenger = spark.sql("""
    SELECT passenger_count, ROUND(AVG(total_amount), 2) as avg_fare
    FROM taxi_data
    GROUP BY passenger_count
    ORDER BY avg_fare DESC
""")

print("\nAverage Fare by Passenger Count:")
avg_fare_by_passenger.show()  # printing the result of the sql query

# visualization
pdf_avg_fare = avg_fare_by_passenger.toPandas()
plt.figure(figsize=(10, 5))
sns.barplot(x="passenger_count", y="avg_fare", data=pdf_avg_fare)
plt.xlabel("Passenger Count")
plt.ylabel("Average Fare ($)")
plt.title("Average Fare by Passenger Count")
plt.show()

trips_by_hour = spark.sql("""
    SELECT pickup_hour, COUNT(*) as total_trips
    FROM taxi_data
    GROUP BY pickup_hour
    ORDER BY pickup_hour
""")

print("\nTotal Trips by Pickup Hour:")
trips_by_hour.show()  # printing the result of the SQL query

pdf_trips_by_hour = trips_by_hour.toPandas()
plt.figure(figsize=(10, 5))
sns.lineplot(x="pickup_hour", y="total_trips", data=pdf_trips_by_hour, marker='o')
plt.xlabel("Hour of the Day")
plt.ylabel("Total Trips")
plt.title("Total Trips by Pickup Hour")
plt.show()

# sql query for average trip duration by passenger count
avg_trip_duration_by_passenger = spark.sql("""
    SELECT passenger_count, ROUND(AVG(trip_duration), 2) as avg_trip_duration
    FROM taxi_data
    GROUP BY passenger_count
    ORDER BY avg_trip_duration DESC
""")

print("\nAverage Trip Duration by Passenger Count:")
avg_trip_duration_by_passenger.show()  # Print the result of the SQL query

# bar plot of average trip duration by passenger count
pdf_avg_trip_duration = avg_trip_duration_by_passenger.toPandas()
plt.figure(figsize=(10, 5))
sns.barplot(x="passenger_count", y="avg_trip_duration", data=pdf_avg_trip_duration)
plt.xlabel("Passenger Count")
plt.ylabel("Average Trip Duration (minutes)")
plt.title("Average Trip Duration by Passenger Count")
plt.show()

# sql query for verage fare per mile by pickup hour
avg_fare_per_mile_by_hour = spark.sql("""
    SELECT pickup_hour, ROUND(AVG(fare_per_mile), 2) as avg_fare_per_mile
    FROM taxi_data
    WHERE fare_per_mile > 0
    GROUP BY pickup_hour
    ORDER BY pickup_hour
""")

print("\nAverage Fare Per Mile by Pickup Hour:")
avg_fare_per_mile_by_hour.show()  # printing the result of the SQL query

# visualization line plot of average fare per mile by pickup hour
pdf_avg_fare_per_mile = avg_fare_per_mile_by_hour.toPandas()
plt.figure(figsize=(10, 5))
sns.lineplot(x="pickup_hour", y="avg_fare_per_mile", data=pdf_avg_fare_per_mile, marker='o')
plt.xlabel("Hour of the Day")
plt.ylabel("Average Fare Per Mile ($)")
plt.title("Average Fare Per Mile by Pickup Hour")
plt.show()

spark.stop()
