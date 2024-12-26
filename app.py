import json
import sqlite3
import geopy
import requests
import math
from flask import Flask, redirect, render_template, request, session, url_for
from geopy.distance import geodesic


app = Flask(__name__)
app.secret_key = 'abc123'

def distance(lat1, lng1, lat2, lng2):
	d1 = geodesic((lat1, lng1), (lat2, lng2))
	d = (float(d1.km))
	""" Convert geodesic datatype to float"""
	return d


def points(d):
	points = 10000 * (math.exp(-1 * (d / 1000)) - math.exp(-1 * (20038 / 1000)))
	return points

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
	

@app.route('/latlong')
def latlong():
	lat = request.args.get('lat')
	lng = request.args.get('lng')
	if lat and lng: """runs if we have values for lat and lng"""
	session['lat'] = lat
	session['lng'] = lng
	
	return redirect(url_for('solo'))




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

@app.route('/solo')
def solo():
	base = "https://graph.mapillary.com/images?access_token=MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1&fields=id&bbox="
	bbox1 = "-6.3872,50.3966,1.7623,55.8113"
	bbox = "-180,-90,180,90" 
	x = requests.get(base + bbox, params={'limit': 10})
	parsed_data = json.loads(x.text)
	print(parsed_data)
	image = parsed_data['data'][0]['id']
	print(image)
	access_token = "MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1"
	url = f"https://graph.mapillary.com/{image}?access_token={access_token}&fields=id,computed_geometry,detections.value"
	y = requests.get(url, params={'limit': 1})
	locations = json.loads(y.text)
	lngget = locations['computed_geometry']['coordinates'][0]
	latget = locations['computed_geometry']['coordinates'][1]
	lat = session.get('lat', None)
	lng = session.get('lng', None)
	print(lat)
	dist = distance(latget, lngget, lat, lng)
	print(dist)
	point = points(dist)
	
	
	return render_template('solo.html', image=image)
	
if __name__ == "__main__":
    app.run(debug=True)