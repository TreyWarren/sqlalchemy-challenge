
# Dependencies
# ⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺
import numpy as np
import datetime as dt
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

# Database Setup
# ⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺
# Create engine
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# Reflect an existing database into a new model
Base = automap_base()
# Reflect the tables
Base.prepare(engine, reflect=True)
# Save reference to the tables
Measurement = Base.classes.measurement
Station = Base.classes.station

# Flask Setup
# ⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺
app = Flask(__name__)

# Flask Routes
# ⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺

# Home Page: List all routes that are available
@app.route("/")
def welcome():
    return (
        f"<h1>Honolulu's Climate API</h1><hr>"
        f"<h3>Available Routes:</h3>"
        f"<h4>Daily Precipitation by Station</h4>"
        f"<a href='/api/v1.0/precipitation'>/api/v1.0/precipitation</a>"
        f"<br/><br/><br/>"
        f"<h4>A List of all Stations and their Locations</h4>"
        f"<a href='/api/v1.0/stations'>/api/v1.0/stations</a>"
        f"<br/><br/><br/>"
        f"<h4>Previous Year's Temperature Observations for the Most Active Station</h4>"
        f"<a href='/api/v1.0/tobs'>/api/v1.0/tobs</a>"
        f"<br/><br/><br/>"
        f"<h4>The Min, Max, and Average Temperatures for the Most Active Station</h4>"
        f"<h5>From a Start Date (earliest data: 2010-01-01)</h5>"
        f"/api/v1.0/(start date)"
        f"<h5>From a Range of Start Date to End Date (most recent data: 2017-08-23)</h5>"
        f"/api/v1.0/(start date)/(end date)"
    )

# _______________________________________________________________________________________
# Convert the query results to a dictionary using date as the key and prcp as the value
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query for the dates and precipitation values
    results = session.query(Measurement.station, 
                            Measurement.date, 
                            Measurement.prcp).all() 
                            """The directions say nothing about the most recent year though 
                                a classmate mentioned the rubric erroneously mentions it.
                                If asked for, this could be acomplished by simply adding:
                                .filter(Measurement.date >= date requested )"""
    # Close session
    session.close()

    # Return the JSON dictionary
    date_prcp_dict = {}
    station_date_prcp_dict = {}
    
    for station, date, prcp in results:
            date_prcp_dict.update({date:prcp})
            station_date_prcp_dict.update({station:date_prcp_dict})

    return jsonify(station_date_prcp_dict)

# _______________________________________________________________________________________
# Return a JSON list of stations from the dataset
@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query all stations
    results = session.query(Station.station, Station.name).all()
    # Close session
    session.close()

    # Return the JSON dictionary
    stations_list = {}

    for station, name in results:
        stations_list.update({station:name})
    
    return jsonify(stations_list)

# _______________________________________________________________________________________
# Query the dates and temperature observations of the most active station 
# for the last year of data
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # Find year benchmarks and most active station
    final_date = session.query(Measurement.date)\
            .order_by(Measurement.date.desc()).first()[0]

    start_date = (dt.datetime.strptime(final_date,'%Y-%m-%d') 
              - dt.timedelta(days=365)).strftime('%Y-%m-%d')

    most_active_station = session.query(Measurement.station, 
                                        func.count(Measurement.station))\
                         .group_by(Measurement.station)\
                         .filter(Measurement.date >= start_date)\
                         .order_by(func.count(Measurement.station).desc())[0][0]
    
    # Query all temperature observations 
    results = session.query(Measurement.date, Measurement.tobs)\
             .filter(Measurement.station == most_active_station)\
             .filter(Measurement.date >= start_date).all()

    # Close session
    session.close()

    # Return the JSON dictionary
    recent_year_temperature = {}

    for date, tobs in results:
        recent_year_temperature.update({date:tobs})
    
    return jsonify(recent_year_temperature)

# _______________________________________________________________________________________
# Return a JSON list of the minimum, maximum, and average temperatures

# When given the start only, calculate TMIN, TAVG, and TMAX for all dates 
# greater than and equal to the start date.
@app.route("/api/v1.0/<start>")
def calc_temps_start(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # Query min, max, and average temperatures
    results = session.query(func.min(Measurement.date),
                            func.max(Measurement.date),
                            func.min(Measurement.tobs),
                            func.max(Measurement.tobs),
                            func.avg(Measurement.tobs))\
             .filter(Measurement.date >= start).all()
    
    # Close session
    session.close()    

    # Return the JSON dictionary
    temperature_list = {}
    
    for s_date, e_date, min, max, avg in results:
        temperature_list.update({"Beginning Date":s_date})
        temperature_list.update({"End Date":e_date})
        temperature_list.update({"TAVG":avg})
        temperature_list.update({"TMAX":max})
        temperature_list.update({"TMIN":min})

    if start < s_date:
        return jsonify({'error':'please note that we only have data from 2010-01-01 to 2017-08-23'},\
                        temperature_list)
    else:
        return jsonify(temperature_list)


# When given the start and the end date, calculate the TMIN, TAVG, and TMAX 
# for dates between the start and end date inclusive.
@app.route("/api/v1.0/<start>/<end>")
def calc_temps(start, end):
    # Create our session (link) from Python to the DB
    session = Session(engine)
    
    # Query min, max, and average temperatures
    results = session.query(func.min(Measurement.date),
                            func.max(Measurement.date),
                            func.min(Measurement.tobs),
                            func.max(Measurement.tobs),
                            func.avg(Measurement.tobs))\
             .filter(Measurement.date >= start)\
             .filter(Measurement.date <= end).all()
    
    # Close session
    session.close()    

    # Return the JSON dictionary
    temperature_list = {}
    
    for s_date, e_date, min, max, avg in results:
        temperature_list.update({"Beginning Date":s_date})
        temperature_list.update({"End Date":e_date})
        temperature_list.update({"TAVG":avg})
        temperature_list.update({"TMAX":max})
        temperature_list.update({"TMIN":min})

    if start > end:
        return jsonify({'error':'please enter a valid date range (/api/v1.0/start/end)'})
    if start < s_date or end > e_date:
        return jsonify({'error':'please note that we only have data from 2010-01-01 to 2017-08-23'},\
                        temperature_list)
    else:
        return jsonify(temperature_list)

# Run the app and development mode
# ⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺⎺
if __name__ == '__main__':
    app.run(debug=True)
