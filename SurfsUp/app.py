# Import the dependencies.
import numpy as np
import re
import datetime as dt
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists  

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with = engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Welcome to my Home API:<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"Temperature imput in YYYY-MM-DD:/api/v1.0/<start_date><br/>"
        f"Tepmerature imput in start dateYYYY-MM-DD/end dateYYYY-MM-DD:/api/v1.0/<date_start>/<date_end><br/>)"
    )

#################################################
# Flask Routes
#################################################

#Precipitation route 
# Returns json with the date as the key and the value as the precipitation 
# Only returns the jsonified precipitation data for the last year in the database

@app.route("/api/v1.0/precipitation")
def precipitation():
# Create session (link) from Python to the DB
    session = Session(engine)

    Latest_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    for date in Latest_date:
        the_date = pd.to_datetime(date)  

    last_year_date = dt.date(the_date.year-1,the_date.month,the_date.day)
    one_year = session.query(Measurement.date,Measurement.prcp).\
                               filter(Measurement.date >= last_year_date).all()
    session.close()
    rain_dc = []
    for date, prcp in one_year:
        dt_dict = {}
        dt_dict[date] = prcp 
        rain_dc.append(dt_dict)
    return jsonify(rain_dc)                                
                                                                         
# Stations route 
#Return a JSON list of stations from the dataset
@app.route("/api/v1.0/stations") 
def stations():
    # Create session (link) from Python to the DB
    session = Session(engine)

    # Query Stations
    stations = session.query(Station.station,Station.name,Station.latitude,Station.longitude,
                             Station.elevation).all()
    session.close()
    station_list = []
    for station,name,latitude,longitude,elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"]= name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        station_list.append(station_dict)

    return jsonify(station_list)

# Tobs route
# Returns jsonified data for the most active station (USC00519281)
# Only returns the jsonified data for the last year of data 

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    latest_date = (session.query(Measurement.date).order_by(Measurement.date.desc()).first())
    
    latest_date = str(latest_date)
    latest_date = re.sub("'|,", "",latest_date)
    last_date = dt.datetime.strptime(latest_date, '(%Y-%m-%d)')
    query_start_date = dt.date(last_date.year, last_date.month, last_date.day) - dt.timedelta(days=366)

    station_data = (session.query(Measurement.station, func.count(Measurement.station))
                             .group_by(Measurement.station)
                             .order_by(func.count(Measurement.station).desc())
                             .all())
    
    station_final = station_data[0][0]
    

    results = (session.query(Measurement.station, Measurement.date, Measurement.tobs,Measurement.prcp)
                      .filter(Measurement.date >= query_start_date)
                      .filter(Measurement.station == station_final)
                      .all())

    tobs_list = []
    for result in results:
        tobs_dict = {}
        tobs_dict["Date"] = result[1]
        tobs_dict["Station"] = result[0]
        tobs_dict["Temperature"] = int(result[2])
        tobs_dict["Prcp"] = result[3]
        tobs_list.append(tobs_dict)

    return jsonify(tobs_list)


# start route 
# Accepts the start date as a parameter from the URL
#Returns the min, max, and average temperatures calculated from the given start date to the end of the dataset

@app.route("/api/v1.0/<start_date>")
def start_date(start_date):
    session = Session(engine)

    temp=[   func.min(Measurement.tobs), 
             func.max(Measurement.tobs), 
             func.avg(Measurement.tobs)]

    most_active_st=session.query(*temp).\
                    filter(Measurement.date >= start_date).all()
                       
    session.close()

    station_temp = []
    for min,max,avg in most_active_st:
        temp_dict = {}
        temp_dict["Minimum"]= min
        temp_dict["Maximum"]= max
        temp_dict["Average"]= avg
        station_temp.append(temp_dict)


    return jsonify(station_temp)

# start/end route
# Accepts the start and end dates as parameters from the URL
# Returns the min, max, and average temperatures calculated from the given start date to the given end date

@app.route("/api/v1.0/<date_start>/<date_end>")
def date_start(date_start,date_end):
    session = Session(engine)

    temp=[   func.min(Measurement.tobs), 
             func.max(Measurement.tobs), 
             func.avg(Measurement.tobs)]

    date_change=session.query(*temp).\
                    filter(Measurement.date >= date_start).\
                        filter(Measurement.date <= date_end).all()
                       
    session.close()

    date_change_list = []
    for min,max,avg in date_change:
        year_dict = {}
        year_dict["Minimum"]= min
        year_dict["Maximum"]= max
        year_dict["Average"]= avg
        date_change_list.append(year_dict)


    return jsonify(date_change_list)

if __name__ =='__main__':
    app.run(debug=True)