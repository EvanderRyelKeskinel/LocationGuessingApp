import json
import sqlite3
import geopy
import requests
import math
from flask import Flask, redirect, render_template, request, session, url_for, jsonify
from geopy.distance import geodesic
from hashlib import sha512
import random


app = Flask(__name__)
app.secret_key = "abc"
access_token = "MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1"
def distance(lat1, lng1, lat2, lng2):
	d1 = geodesic((lat1, lng1), (lat2, lng2))
	d = (float(d1.km))
	""" Convert geodesic datatype to float"""
	return d



def points_calc(d):
	points = 10000 * (math.exp(-1 * (d / 1000)) - math.exp(-1 * (20038 / 1000)))
	return round(points)


def create():
	with sqlite3.connect('App.db') as db: #Connect to the App.db database
		cursor = db.cursor() 
		cursor.execute(	"""--sql 
        CREATE TABLE IF NOT EXISTS Users (
        Username TEXT NOT NULL,
        SALT INTEGER, 
        Password TEXT NOT NULL, 
        Highest_solo INTEGER, 
        Highest_mult INTEGER, 
        LobbyID TEXT, 
        InGame INTEGER, 
        Primary Key(Username))
				""") #Creates table 'Users' with several values Username as primary key
		db.commit()
create()


@app.route('/login', methods = ['GET', 'POST']) #Defines a route with /login with both methods
def login():
    if 'username' in session:
        return redirect(url_for('home'))  #directs logged in user to 
    else:
        if request.method == "POST": #POST request
            if len(request.form['un']) > 32: #Check username length
                error = "Username cannot be more than 32 characters"
                return render_template('login.html', error=error) #Display error on screen
        
    
            elif len(request.form['pw']) > 256: #Check password length
                error = "Password cannot be more than 256 characters" 
                return render_template('login.html', error=error) #Display error on screen
            
            else:
                con = sqlite3.connect("App.db") #Connect database
                cur = con.cursor()
                cur.execute("SELECT * FROM Users WHERE Username=?", (request.form['un'],)) #Find all matching usernames
                
                UsernameMatch = len(cur.fetchall()) #No. of matching usernames
                
                con.close() #close connection
                
                if UsernameMatch == 0: #See if user has a matching username in the database
                    error = "invalid credentials" 
                    return render_template('login.html', error=error) #Display error if no match
                
                else:
                    con = sqlite3.connect("App.db")
                    cur = con.cursor()
                    SALT = cur.execute("SELECT SALT FROM Users WHERE Username=?", (request.form['un'],)).fetchone() [0] 
                    #Fetch SALT from matching username record
                    
                    Hashed_password = (sha512((request.form['pw'].encode('utf-8') + str(SALT).encode('utf-8'))).digest())
                    #Hash the input password + SALT
                    
                    cur.execute("SELECT * FROM Users WHERE Username=? AND Password=?", (request.form['un'], Hashed_password,))
                    CredentialsMatch = len(cur.fetchall())
                    print(CredentialsMatch)
                    #Counts number of times both credentials are matching in database

                    cur.close()
                    
                    if CredentialsMatch == 0: #if credentials don't match
                        error = "invalid credentials"
                        return render_template('login.html', error=error)
                    
                    else: # when credentials do match
                        session['username'] = request.form['un']
                        return redirect(url_for('home'))
                        #log user in and redirect them

        else: #GET request
            return render_template('login.html')


@app.route('/', methods = ['GET', 'POST']) #Defines a route with just / for both POST and GET methods
def signup():
    if 'username' in session:
        return redirect(url_for('home')) #redirects to home if user logged in
    
    else:    
        if request.method == "POST": #if a POST request
            con = sqlite3.connect("App.db") #Connect database
            cur = con.cursor()
            cur.execute("SELECT * FROM Users WHERE Username=?", (request.form['un'],)) 
            #Select users who have username matching input username
            
            UsernameMatch = len(cur.fetchall()) #stores number of times Username matches
            con.close() #close connection
            
            if len(request.form['un']) > 32: #if username is more than 32 characters
                error = "Username cannot be more than 32 characters"
                return render_template('signup.html', error=error) #returns error on signup page
            
            elif len(request.form['pw']) > 256: #if password is more than 256 characters
                error = "Password cannot be more than 256 characters"
                return render_template('signup.html', error=error) 

            elif ' ' in request.form['un']: #checks if username contains a space
                error = "Username cannot have spaces"
                return render_template('signup.html', error=error)

            elif len(request.form['un']) == 0 or len(request.form['pw']) == 0: #neither field can be left blank
                error = "Password or username cannot be blank"
                return render_template('signup.html', error=error)
            
            elif UsernameMatch > 0: #if username already exists in the table, should cause an error
                error = "Username Taken" 
                return render_template('signup.html', error=error) 
            
            elif request.form['pw'] != request.form['cpw']: #compare passwords
                error = "Confirm password doesn't match Password"
                return render_template('signup.html', error=error)
            
            else: 
                con = sqlite3.connect("App.db") #Reopen the connection
                cur = con.cursor()
                SALT = random.randint(0, 1000000) #Generates random integer
                cur.execute(""" INSERT INTO Users (Username, SALT, Password) 
                        VALUES (?, ?, ?) """,
                        (request.form['un'], SALT, (sha512((request.form['pw'].encode('utf-8') + str(SALT).encode('utf-8'))).digest()))) 
                        #adds username and hashed password to database
                        #enodes the password and hash into a form that allows it to be hashed
                con.commit() #commit the SQL
                con.close() #Close the connection
                
                session['username'] = request.form['un'] #make a session for the user
            return redirect(url_for('home')) #redirect to home page
        
        else:  #GET request (loading in page)
            return render_template('signup.html')

@app.route('/home')
def home():
    if not('username' in session):
        return redirect(url_for('signup')) #if user not logged in, redirect to signup page
    else:
        return render_template('home.html') #load home page

@app.route('/api/datapoint')
def submitsend(): #function name changed to suite functionality
	point_change = session.get('points')
	image_lat = session.get('latget')
	image_lng = session.get('lngget')
	dictionary = {
		'points': point_change, #points in dict

		'image_lat': image_lat,

		'image_lng': image_lng # coordinates in dict
	}
	return jsonify(dictionary) #returns as JSON object


@app.route('/solo', methods=['GET', 'POST']) #POST request now considered
def solo():
	if request.method == "GET": #Get request
		base = "https://graph.mapillary.com/images?access_token=MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1&fields=id&bbox="
		bbox = "-180,-90,180,90"  #Select full range of possible coordinates 
		x = requests.get(base + bbox, params={'limit': 10}) #Generate image id and limit amount of data retrieved
		parsed_data = json.loads(x.text) #Turn into python dictionary
		global image
		image = parsed_data['data'][0]['id'] #Take first image ID 
		print(image) #id of streetview image
		return render_template('solo.html', image=image) #points sent to html 
	
	elif request.method == "POST": #POST request
		url = f"https://graph.mapillary.com/{image}?access_token={access_token}&fields=id,computed_geometry,detections.value"
		y = requests.get(url, params={'limit': 1}) #to get the coordinates of the generated image
		locations = json.loads(y.text)
		lngget = locations['computed_geometry']['coordinates'][0] #longitude of streetview image
		latget = locations['computed_geometry']['coordinates'][1] #lattitude of streetview image
		print(lngget, latget) #shows coordinates of image
		user_lat = request.args.get('lat') #lattitude that is guessed by the user 
		user_lng = request.args.get('lng') #longitude that is guessed by the user
		dist = distance(latget, lngget, user_lat, user_lng) #distance between the guessed coordinates and the actual coordinates
		print(dist)
		points = points_calc(dist)
		session['latget'] = latget
		session['lngget'] = lngget #Sessions for lat and lng of image
		session['points'] = points # session defined in POST
		print(points)
		
		return render_template('solo.html', image=image, point=points) 
	else:
		raise ValueError("invalid")
		
		
	
if __name__ == "__main__":
    app.run(debug=True)