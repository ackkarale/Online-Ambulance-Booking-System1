import datetime
from json import decoder
import geocoder

import re
from geopy import distance
import webbrowser
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
import json
from flask_sqlalchemy import SQLAlchemy
from geopy import distance

def nearestAmbulanceUsers(lat, lon):
    # Retrieve ambulance users from the database
    ambulance_users = AmbulanceUser.query.all()
    # Calculate distances to all ambulance users
    distances = []
    for user in ambulance_users:
        user_lat = user.latitude
        user_lon = user.longitude
        if user_lat is not None and user_lon is not None:
            dist = distance.distance((lat, lon), (user_lat, user_lon)).km
            distances.append((user, dist))
    
    # Sort distances to find the top 4 nearest ambulance users
    sorted_distances = sorted(distances, key=lambda x: x[1])[:4]
    
    # Return the top 4 nearest ambulance users
    nearest_users = [user for user, dist in sorted_distances]
    return nearest_users



# Locations = nearChargingStations(0,0)
# for i in Locations:
#     print(i)



app = Flask(__name__)
# create the extension
db = SQLAlchemy()
# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ambulancebooking.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# initialize the app with the extension
db.init_app(app)
app.app_context().push()

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'


# Creating the Database


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    name = db.Column(db.String(50))
    address = db.Column(db.String(70))
    phone = db.Column(db.Integer)
    role=db.Column(db.String(10))


class AmbulanceUser(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    password = db.Column(db.String(50))
    name = db.Column(db.String(50))
    address = db.Column(db.String(70))
    phone = db.Column(db.Integer)
    latitude=db.Column(db.Float)
    longitude=db.Column(db.Float)
    role=db.Column(db.String(10))

class BookAmbulance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId=db.Column(db.Integer)
    ambulanceId=db.Column(db.Integer)
    latitude=db.Column(db.Float)
    longitude=db.Column(db.Float)
    date=db.Column(db.String(80))
    status=db.Column(db.String(20))

db.create_all()

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

'''
@login_manager.user_loader
def load_user(user_name):
    return AmbulanceUser.query.get(int(user_name))'''


@login_manager.user_loader
def load_user(user_id):
    return AmbulanceUser.query.get(int(user_id))


@app.route('/')
def home():
    user_role = None
    if current_user.is_authenticated:
        if current_user.role == "Driver":
            user_role = "Driver"
        elif current_user.role == "User":
            user_role = "User"
    return render_template('index.html', user_role=user_role)



# @app.route("/login", methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form.get('username')
#         password = request.form.get('password') 
#         # Check if it's a regular User
#         regular_user = User.query.filter_by(username=username).first()
#         if regular_user and regular_user.password == password and regular_user.role=="User":  # Assuming you have a method to check passwords
#             # User loader for User table
#             @login_manager.user_loader
#             def load_user(user_id):
#                 # Try loading from User table
#                 return User.query.get(int(user_id))

#             login_user(regular_user)
#             return redirect(url_for('home'))
#         elif regular_user:
#             flash("Wrong Password")

#          # Check if it's a MedicalStore user
#         ambulanceuser = AmbulanceUser.query.filter_by(username=username).first()
#         if ambulanceuser and ambulanceuser.password==password and ambulanceuser.role=="Driver":  # Assuming you have a method to check passwords
#             print("Store User")
#             login_user(ambulanceuser)
#             if current_user.is_authenticated:

#                 return redirect(url_for('home'))
#         elif ambulanceuser:
#             flash("Wrong Password")
        
#         # If username is not found in either table
#         flash("Invalid Username")
    
#     return render_template("login.html")
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check in the User table
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            @login_manager.user_loader
            def load_user(user_id):
                return User.query.get(int(user_id))
            login_user(user)
            return redirect(url_for('home'))

        # Check in the AmbulanceUser table
        ambulance_user = AmbulanceUser.query.filter_by(username=username, password=password).first()
        if ambulance_user:
            @login_manager.user_loader
            def load_user(user_id):
                return AmbulanceUser.query.get(int(user_id))
            login_user(ambulance_user)
            return redirect(url_for('home'))

        flash("Invalid username or password", 'error')
    
    return render_template('login.html')







@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address')
        phone_No = request.form.get('phone')
        newUser  = User(
            username=username,
            password=password,
            name=name,
            address=address,
            phone=phone_No,
            role="User"
        )
        db.session.add(newUser)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/ambulanceregistration', methods=['GET','POST'])
def ambulanceRegister():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name')
        address = request.form.get('address')
        phone_No = request.form.get('phone')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')        

        pattern = r"LatLng\(([-+]?\d+\.\d+),\s*([-+]?\d+\.\d+)\)"
        # Search for the pattern in the input string
        match = re.search(pattern, latitude)

        # Extract latitude and longitude values if the pattern is found
        if match:
            latitude = float(match.group(1))
            longitude = float(match.group(2))
            
        newAmbulanceUser= AmbulanceUser(
            username=username,
            password=password,
            name=name,
            address=address,
            phone=phone_No,
            latitude=latitude,
            longitude=longitude,
            role="Driver"
        )
        db.session.add(newAmbulanceUser)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('ambulanceRegistration.html')

lat = 0
long = 0
@app.route('/process/<string:userinfo>', methods=['GET', 'POST'])
def process(userinfo):
    userinfo = json.loads(userinfo)
    print(f"User type :: {userinfo['values']}")
    global lat, long
    lat, long = (userinfo['values'][7:-1]).split(',')

    return redirect(url_for('location'))

@app.route('/location', methods=['GET','POST'])
def location():
    # print(lat, long)
    nearLocations = []
    if request.method == "POST":
        nearLocations = nearestAmbulanceUsers(lat, long)
        print(nearLocations)
    return render_template('Location.html', nearestAmbulancedricers=nearLocations, nearLocationsLen=len(nearLocations))


@app.route('/map', methods=['POST'])
def map():
    if request.method == 'POST':
        # Get the latitude and longitude of the destination (ambulance driver)
        dest_lat_str = request.form.get('dest_lat')
        dest_long_str = request.form.get('dest_long')

        # Check if latitude and longitude values are provided
        if dest_lat_str is not None and dest_long_str is not None:
            try:
                D_lat = float(dest_lat_str)
                D_long = float(dest_long_str)

                # Fetching current driver's latitude and longitude
                current_driver = AmbulanceUser.query.filter_by(id=current_user.id).first()  # Assuming you have a current_user object representing the logged-in user
                if current_driver:
                    driver_lat = current_driver.latitude
                    driver_long = current_driver.longitude

                    # Open Google Maps with directions from current location to destination
                    map_url = f"https://www.google.com/maps/dir/{driver_lat},{driver_long}/{D_lat},{D_long}"
                    webbrowser.open(map_url)

                    return jsonify({"success": True, "message": "Map opened successfully"})
                else:
                    return jsonify({"success": False, "error": "Current driver not found"})
            except ValueError:
                # Handle the case where latitude or longitude values are not valid numbers
                error_message = "Error: Destination latitude or longitude is not a valid number"
                print(error_message)
                return jsonify({"success": False, "error": error_message})
        else:
            error_message = "Error: Destination latitude or longitude not provided"
            print(error_message)
            return jsonify({"success": False, "error": error_message})

    # If the method is not POST or there's an issue, redirect to the page showing bookings
    return redirect(url_for('location'))
@app.route("/bookAmbulance", methods=["GET", 'POST'])
def bookAmbulance():
    if request.method == 'POST':
        current_date = datetime.datetime.now().date()    
# Format the current date
        formatted_date = current_date.strftime("%Y-%m-%d")
        ambulanceId = request.form.get("driverId")

        newBooking = BookAmbulance(
            userId=current_user.id,
            ambulanceId=ambulanceId,
            latitude=lat,
            longitude=long,
            date=formatted_date,
            status="Pending"
        )

        db.session.add(newBooking)
        db.session.commit()
    return redirect(url_for('home'))

@app.route("/status/<int:statusCode>/<int:bookingId>", methods=['GET','POST'])
def changeStatus(statusCode, bookingId):
    if request.method == 'POST':
        if statusCode == 0:
            booking = BookAmbulance.query.filter_by(id=bookingId).first()
            if booking:
                booking.status = "Approve"
                db.session.commit()
                # return "Status changed successfully"
                return redirect(url_for("bookings"))
            
            else:
                return "Booking not found", 404
        else:
            booking = BookAmbulance.query.filter_by(id=bookingId).first()
            if booking:
                booking.status = "disApprove"
                db.session.commit()
                return redirect(url_for("bookings"))

            else:
                return "Booking not found", 404
    else:
        return "Only POST requests are allowed for this route", 405




@app.route("/bookings")
def bookings():
    if current_user.role=="User":
        booking = BookAmbulance.query.filter_by(userId=current_user.id).all()
    else:
        booking = BookAmbulance.query.filter_by(ambulanceId=current_user.id).all()
    print(booking)

    return render_template("bookings.html", bookings=booking)



@app.route('/about')
def about():
    return render_template('about.html')




@app.route('/contact')
def contact():
    return render_template('contact.html')



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)




