#dependencies
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt

# Python SQL toolkit and Object Relational Mapper
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

# create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
base = automap_base()
base.prepare(engine, reflect = True)
# reflect the tables
base.metadata.tables

# too hard to read, so will use inspector
from sqlalchemy import inspect
inspector = inspect(engine)
inspector.get_table_names()

measure_col = inspector.get_columns('measurement')
for i in measure_col:
    print(i['name'], i["type"])

station_col = inspector.get_columns('station')
for i in station_col:
    print(i['name'], i["type"])

# View all of the classes that automap found
base.classes.keys()

# Save references to each table
Measurement = base.classes.measurement
Station = base.classes.station

# Create our session (link) from Python to the DB
session = Session(bind=engine)
base.metadata.create_all(engine)

# Find the most recent date in the data set.
measurement_recent_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first().date
print(measurement_recent_date)

# Design a query to retrieve the last 12 months of precipitation data and plot the results. 
# Starting from the most recent data point in the database. 

# Calculate the date one year from the last date in data set.
one_yr_delta = dt.datetime.strptime(measurement_recent_date, '%Y-%m-%d') - dt.timedelta(days = 365)
print(one_yr_delta)

# Perform a query to retrieve the data and precipitation scores
one_yr_data = session.query(Measurement.date, func.avg(Measurement.prcp)).\
                      filter(Measurement.date >= one_yr_delta).\
                      group_by(Measurement.date).all()

# Save the query results as a Pandas DataFrame and set the index to the date column
prcp_df = pd.DataFrame(one_yr_data, columns=['Date', 'Precipitation'])
prcp_df.set_index('Date', inplace = True)

# Sort the dataframe by date
sorted_prcp_df = prcp_df.sort_index()

# Use Pandas Plotting with Matplotlib to plot the data
plt.figure(figsize = (40,20))
plt.title("Precipitation in the Last Twelve Months", fontsize = 40)
plt.xlabel("Date", fontsize = 40)
plt.ylabel("Inches of Precipitation", fontsize = 40)
plt.xticks(rotation = 45)
plt.bar(sorted_prcp_df.index.values, sorted_prcp_df['Precipitation'])
plt.savefig("Output/Precipitation_Figure.png")
plt.show

# Use Pandas to calculate the summary statistics for the precipitation data
sorted_prcp_df.describe()

# Design a query to calculate the total number stations in the dataset
total_stations = session.query(Station.id).count()

# Design a query to find the most active stations (i.e. what stations have the most rows?)
# List the stations and the counts in descending order.
active_data = session.query(Measurement.station, func.count(Measurement.station)).\
                      group_by(Measurement.station).\
                      order_by(func.count(Measurement.station).desc()).all()

# Using the most active station id from the previous query, calculate the lowest, highest, and average temperature.
active_station = active_data[0][0]
active_station_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
                              filter(Measurement.station == active_station).all()
print(f"Min: {active_station_data[0][0]}, Avg: {active_station_data[0][1]}, Max: {active_station_data[0][2]}")

# Using the most active station id
# Query the last 12 months of temperature observation data for this station
active_station_temp_data = session.query(Measurement.station, Measurement.tobs).\
                                   filter(Measurement.station == active_station).\
                                   filter(Measurement.date >= one_yr_delta).all()

# importing data into pandas
temp_df = pd.DataFrame(active_station_temp_data, columns=['Station', 'Temperature'])
temp_df.set_index('Station', inplace = True)

# plot the results as a histogram
plt.figure(figsize = (10, 8))
plt.title(f"Temperature Counts for Station {active_station} in Past Twelve Months", fontsize = 20)
plt.xlabel("Temperature", fontsize = 20)
plt.ylabel("Counts", fontsize = 20)
plt.hist(temp_df['Temperature'])
plt.savefig("Output/Temperature_Figure.png")
plt.show

# Close Session
session.close()

from flask import Flask, jsonify

app = Flask(__name__)

# index/home route
@app.route("/")
def home():
    print("Server received request for '/' page...")
    return (
        f"Home Page<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end<br/>"
    )

# /api/v1.0/precipitation
@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server received request for '/api/v1.0/precipitation' page...")
    prcp_dict = sorted_prcp_df.to_dict()
    return jsonify(prcp_dict)

# /api/v1.0/stations
@app.route("/api/v1.0/stations")
def stations():
    print("Server received request for '/api/v1.0/stations' page...")
    station_names = [active_data[i][0] for i in range(len(active_data))]
    return jsonify(station_names)

# /api/v1.0/tobs
@app.route("/api/v1.0/tobs")
def tobs():
    print("Server received request for '/api/v1.0/tobs' page...")
    temp_ls = temp_df['Temperature'].to_list()
    return jsonify(temp_ls)

# /api/v1.0/<start>
@app.route("/api/v1.0/<start>")
def query(start):
    print("Server received request for '/api/v1.0/<start>' page...")
    values = sorted_prcp_df.loc[start:]['Precipitation'].to_list()
    output_ls = [min(values), sum(values)/len(values), max(values)]
    return jsonify(output_ls)

# /api/v1.0/<start>/<end>
@app.route("/api/v1.0/<start>/<end>")
def query2(start, end):
    print("Server received request for '/api/v1.0/<start>/<end>' page...")
    values = sorted_prcp_df.loc[start:end]['Precipitation'].to_list()
    output_ls = [min(values), sum(values)/len(values), max(values)]
    return jsonify(output_ls)

if __name__ == "__main__":
    app.run(debug=True)