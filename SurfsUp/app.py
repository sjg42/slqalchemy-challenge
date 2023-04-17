# Import the dependencies.
"""
    Flask is a library that allows for us to develop local servers and
    serve data!!
    1. start and stop the server
    2. define endpoints - index will be the home route
"""
# 1. import Flask and jsonify
        # jsonify allows for dictionaries to be parsed as jsons
from flask import Flask, jsonify

import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine

#################################################
# Database Setup
#################################################

#create engine to hawaii.sqlite
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################

#Create an app, passing the argument __name__
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

#---------------------------
#Home Route
#---------------------------
@app.route('/')
def home():
    #print all of the available routes
    return(f"This is the homepage!<br>"
           f"Current routes include: <br>"
           f"/api/v1.0/precipitation <br>"
           f"/api/v1.0/stations <br>"
           f"/api/v1.0/tobs <br>"
           f"/api/v1.0/start (where start is a date in format YYYY-MM-DD) <br>"
           f"/api/v1.0/start/end (where start and end are dates in format YYYY-MM-DD)")


#---------------------------
#Precipitation Route
#---------------------------

@app.route('/api/v1.0/precipitation')
def prcp():
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)

    #latest_date in the Measurement DB is 2017-08-23
    latest_date = dt.date(2017,8,23)
    
    #calculate the date one year before the last date in the DB
    one_year_ago = latest_date - dt.timedelta(days = 365)

    #Perform query to retrieve the dates and precip scores from Measurement DB
    #Only get precip scores from the last year
    #Order in ascending order
    results = session.query(Measurement.date,Measurement.prcp).\
        filter(Measurement.date>=one_year_ago).\
        order_by(Measurement.date.asc())


    #Store results into a List of dictionaries
    resultsDict={}

    for res in results:
        #Add prcp value to resultsDict
        #Check if date is already there,
        # if yes, add to list of values on that date
        # if no, create new key-value pair
        if res.date in resultsDict:
            resultsDict[res.date].append(res.prcp)
        else:
            resultsDict[res.date] = [res.prcp]
    
    # Close session
    session.close()
        
    #return a Jsonified resultsList
    return jsonify(resultsDict)


#---------------------------
#Station Route
#---------------------------
@app.route('/api/v1.0/stations')
def stations_list():
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)

    #query for the stations
    results = session.query(Station.id, Station.station)
    
    #Store stations in a stations_list
    stationList = []
    for res in results:
        #Store id 
        stationDict = {
            'id': res.id,
            'Station Name': res.station
        }
        stationList.append(stationDict)
    
    # Close session
    session.close()

    return jsonify(stationList)



#---------------------------
#Temperature Observations (TOBS) Route
#---------------------------
@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)

    latest_date = dt.date(2017,8,23) #latest date in Measurement DB
    
    #calculate the date one year before the last date in the DB
    one_year_ago = latest_date - dt.timedelta(days = 365)

    #query to get most active station, and save as most_active)
    station_count = session.query(Measurement.station,func.count(Measurement.station)).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).all()
    (most_active, count) = station_count[0]

    
    #Store query of dates and temp obs from the
    # most active station from the last year
    results = session.query(Measurement.date,Measurement.tobs).\
        filter(Measurement.station == most_active).\
        filter(Measurement.date>=one_year_ago).all()

    tempsList = []
    for res in results:
        tempsDict = {
            "Date":res.date,
            "Observed Temperature": res.tobs
        }
        tempsList.append(tempsDict)

    # Close session
    session.close()

    #return the most active station's temperature observations from the last year
    return (jsonify(tempsList))


#---------------------------
#Start Route
#---------------------------
@app.route('/api/v1.0/<start>')
def start_report(start):
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)
    
    latest_date = dt.date(2017,8,23) #latest date in Measurement DB
    earliest_date = dt.date(2010,1,1) #earliest date in Measurement DB
    try:
        #turn date into a dt
        #start should be string formatted 'YYYY-MM-DD'
        #year: characters 1-4 of string (indexes 0:4)
        #month: characters 6-7 of string (indexes 5-7)
        #day: characters 9-10 of string (indexes 8:)
        (year,month,day) = (int(start[0:4]), int(start[5:7]),int(start[8:]))
        date = dt.date(year, month, day)

        #check if date is valid
        if date>latest_date or date<earliest_date:
            return (f"Date is outside the valide range. <br>"
                    f"Date must be between 2010-01-01 and 2017-08-23.")
        
        else:
            #session.query for the min, max, and avg of the temps from
            #date - latest_date
            #returns list of tuple with format (min,max,avg)
            results = session.query(func.min(Measurement.tobs),
                                    func.max(Measurement.tobs),
                                    func.avg(Measurement.tobs)).\
                                    filter(Measurement.date>=date).all()
            #store results of query
            (minimum,maximum,average) = results[0]

            # Close session
            session.close()

            return (f"The following is a summary of observed temperature date from {date} to {latest_date}. <br>"
                    f"Minimum Observed temp: {minimum} deg F <br>"
                    f"Maximum Observed temp: {maximum} deg F <br>"
                    f"Average Observed temp: {average:.2f} deg F")
    except ValueError:
        # Close session
        session.close()

        return("Provided date was not in the correct format. <br>"
               "Enter date in the format YYYY-MM-DD.")


#---------------------------
#Start/End Route
#---------------------------

@app.route('/api/v1.0/<start>/<end>')
def start_end_report(start,end):
    # Create our session (link) from Python to the DB
    session = Session(bind=engine)
    
    latest_date = dt.date(2017,8,23) #latest date in Measurement DB
    earliest_date = dt.date(2010,1,1) #earliest date in Measurement DB
    try:
        #turn dates into a dt
        #dates should be string formatted 'YYYY-MM-DD'
        #year: characters 1-4 of string (indexes 0:4)
        #month: characters 6-7 of string (indexes 5-7)
        #day: characters 9-10 of string (indexes 8:)
        (s_year,s_month,s_day) = (int(start[0:4]), int(start[5:7]),int(start[8:]))
        s_date = dt.date(s_year, s_month, s_day)

        (e_year,e_month,e_day) = (int(end[0:4]), int(end[5:7]),int(end[8:]))
        e_date = dt.date(e_year, e_month, e_day)

        #check if dates are valid
        if s_date>latest_date or s_date<earliest_date:
            # Close session
            session.close()

            return (f"Start Date is outside the valide range. <br>"
                    f"Date must be within 2010-01-01 and 2017-08-23.")
        
        if e_date>latest_date or e_date<earliest_date:
            # Close session
            session.close()
            
            return (f"End Date is outside the valide range. <br>"
                    f"Date must be between {s_date} and 2017-08-23.")
        
        else:
            #session.query for the min, max, and avg of the temps from
            #s_date - e_date
            #returns list of tuple with format (min,max,avg)
            results = session.query(func.min(Measurement.tobs),\
                                    func.max(Measurement.tobs),\
                                    func.avg(Measurement.tobs)).\
                                    filter(Measurement.date<=e_date).\
                                    filter(Measurement.date>=s_date).all()
            #store results of query
            (minimum,maximum,average) = results[0]

            # Close session
            session.close()

            return (f"The following is a summary of observed temperature date from {s_date} to {e_date}. <br>"
                    f"Minimum Observed temp: {minimum} deg F <br>"
                    f"Maximum Observed temp: {maximum} deg F <br>"
                    f"Average Observed temp: {average:.2f} deg F")
    except ValueError:
        # Close session
        session.close()
        
        return("One or both of the provided dates were not in the correct format. <br>"
               "Enter dates in the format YYYY-MM-DD.")


# give the default name of the application so that we can start it from
# our command line
if __name__ == "__main__":
    app.run(debug=True) # module used to start the development server
            # to stop the server, use ctrl+c or cmd+c