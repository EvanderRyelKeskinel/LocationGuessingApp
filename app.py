import json
import sqlite3
import geopy
import requests
import math
from flask import Flask, redirect, render_template, request, session, url_for, jsonify
from geopy.distance import geodesic


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
	with sqlite3.connect('login.db') as db:
		cursor = db.cursor()
		cursor.execute(	"""--sql
				 	CREATE TABLE IF NOT EXISTS Users(
						Username text,
						Password text,
						Primary Key(Username))
				""")
		db.commit()
	print('CREATE')
create()

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		con = sqlite3.connect('login.db')
		cur = con.cursor()
		cur.execute("SELECT * FROM users WHERE username=? AND password=?",
					(request.form['un'],request.form['pw']))
		match = len(cur.fetchall())
		con.close()
		if match == 0:
			return "wrong username and password"
		else:
			return "welcome " + request.form['un']
	else:
		return render_template('login.html')


@app.route('/', methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        con = sqlite3.connect("login.db")
        cur = con.cursor()
        cur.execute(""" INSERT INTO users (username, password)
                VALUES (?, ?) """,
                (request.form['un'], request.form['pw']))
        con.commit()
        con.close()
        return 'signup successful'
    else: # GET request
        return render_template('signup.html')

@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/api/datapoint')
def point_change():
	point_change = session.get('points')
	dictionary = {
		'points': point_change
	}
	return jsonify(dictionary)


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
		user_lat = request.args.get('lat') #lattitude that is guessed by the user 
		user_lng = request.args.get('lng') #longitude that is guessed by the user
		dist = distance(latget, lngget, user_lat, user_lng) #distance between the guessed coordinates and the actual coordinates
		print(dist)
		points = points_calc(dist)
		session['points'] = points # session defined in POST
		print(points)
		
		return render_template('solo.html', image=image, point=points) 
	else:
		raise ValueError("invalid")
		
		
	
if __name__ == "__main__":
    app.run(debug=True)