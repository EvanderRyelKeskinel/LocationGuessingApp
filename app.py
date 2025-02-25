import json
import sqlite3
import geopy
import requests
import math
from flask import Flask, redirect, render_template, request, session, url_for, jsonify
from geopy.distance import geodesic
from hashlib import sha512
import random
import string


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

def findImage(): #gets image corresponding to current round number
    con = sqlite3.connect("App.db")
    cur = con.cursor()
    image_search = cur.execute(f"SELECT Image{(round_count)} FROM Games WHERE GameID=?", (session.get('GameID'),)).fetchone()
    con.close()
    if image_search is None:
        return None
    return image_search [0]

def getImage(bbox):
    base = "https://graph.mapillary.com/images?access_token=MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1&fields=id&bbox="
    x = requests.get(base + bbox, params={'limit': 10})
    return "."

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
        Current_LobbyID TEXT,
        InGame INTEGER, 
        FOREIGN KEY(Current_LobbyID) REFERENCES Lobby(LobbyID),
        Primary Key(Username))
                       """) #Creates table 'Users', with primary and foreign keys.
        db.commit()
        
        cursor.execute("""--sql 
        CREATE TABLE IF NOT EXISTS Lobby (
        LobbyID TEXT NOT NULL, 
        Head TEXT,
        FOREIGN KEY(Head) REFERENCES Users(Username),
        Primary Key(LobbyID))
                        """) #Creates table Lobby with primary and foreign keys
        db.commit()
        
        cursor.execute("""--sql
        CREATE TABLE IF NOT EXISTS Games (
        GameID TEXT NOT NULL, 
        Mode TEXT, 
        Region TEXT,
        Image1 INTEGER, LatLong1 TEXT, 
        Image2 INTEGER, LatLong2 TEXT, 
        Image3 INTEGER, LatLong3 TEXT, 
        Image4 INTEGER, LatLong4 TEXT, 
        Image5 INTEGER, LatLong5 TEXT,
        Primary Key(GameID),
        FOREIGN KEY(Region) REFERENCES Regions(Region))            
                        """) #Creates table Games with primary and foreign keys
        db.commit()
        cursor.execute("""--sql
        CREATE TABLE IF NOT EXISTS Multiplayer (
        GameID TEXT NOT NULL,
        LobbyID TEXT NOT NULL,
        Primary key(GameID, LobbyID),
        FOREIGN KEY(GameID) REFERENCES Games(GameID),
        FOREIGN KEY(LobbyID) REFERENCES Lobby(LobbyID))
                        """) #Creates table multiplayer with composite key GameID, LobbyID
        db.commit()
        cursor.execute("""--sql
        CREATE TABLE IF NOT EXISTS Attempts(
        GameID TEXT NOT NULL,
        Username TEXT NOT NULL,     
        Guess1 TEXT,
        Guess2 TEXT,
        Guess3 TEXT,
        Guess4 TEXT,
        Guess5 TEXT,
        Points INTEGER,             
        Primary key(GameID, Username),
        FOREIGN KEY(GameID) REFERENCES Games(GameID),         
        FOREIGN KEY(Username) REFERENCES Users(Username))
                       """) #Creates a table Attempts composite key GameID, Username
        db.commit()
        cursor.execute("""--sql
        CREATE TABLE IF NOT EXISTS Regions(
        Region TEXT NOT NULL,
        BoundingBox TEXT NOT NULL,
        Radius INTEGER NOT NULL,
        Primary key(Region))                
                        """) #Creates table Regions with primary key
        db.commit()
create()

#cursor.execute("""INSERT INTO 'Regions' ('Region', 'BoundingBox', 'Radius') VALUES
    #            ("Worldwide", "-180,-90,180,90", 5000),
    #            ("Ireland_AND_UK", "50.112364,-13.590088,59.160268,1.385071", 250),
    #            ("Central_Africa", "-35.243376,-17.768669,13.473103,52.161026", 2000),
    #           ("North_Africa", "13.478111,-31.902924,34.436646,34.454498", 1500),
    #            ("Europe", "37.222127,-25.845337,69.127602,44.291382", 800),
    #           ("North_Asia", "41.252516,31.102295,77.991763,189.870529", 2000),
    #            ("Central_Asia", "14.093957,44.648438,53.852527,145.722656",2000),
    #           ("SouthEast_Asia", "11.015341,92.473640,29.075375,140.449219",1400),
    #           ("North_America", "14.675268,-167.776337,84.745057,-26.799774",1800),
    #           ("South_America", "-56.946098,-99.758949,13.650324,-29.900322",2000);""" )
    #       db.commit() 



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

		'image_lng': image_lng
          # coordinates in dict
	}
    return jsonify(dictionary) #returns as JSON object

round_count = 0 # initializes round outside the function


@app.route('/round_data', methods=['POST']) # POST request called when new round started
def roundcount():
    global round_count
    round_count = round_count + 1 # round is increased by 1
    
    dictionary = {
        'round': round_count # round placed in a dictionary
    }
    return jsonify(dictionary) #Turned into json object so it can be read by javascript.

stage_count = 0
@app.route('/stage_count', methods=['POST', 'GET'])  
def stagecount():
    global stage_count #makes global so it can initialised
    if request.method == "GET": # GET request
        
        dict = {
            'stage': stage_count
        } #defines a dictionary to be jsonified
        return jsonify(dict)
    
    else: # POST request 
        stage_count = stage_count + 1 # increments by 1
        print(stage_count)
        return jsonify(stage_count) 

@app.route('/solo', methods=['GET', 'POST']) #POST request now considered
def solo():
    global round_count
    if not('username' in session):
        return redirect(url_for('signup')) #if user not logged in, redirect to signup page
    
    elif request.method == "GET": #Get request
        if round_count == 0:
            GameID = random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) # random 10 digit string
            session['GameID'] = GameID
            con = sqlite3.connect("App.db") #Connect database
            cur = con.cursor()

            cur.execute("""INSERT INTO Games (GameID, Mode, Region) 
                            VALUES (?, ?, ?)""", (GameID, "SoloRanked", "Worldwide",)) 
            con.commit() # fill in Games table with generated GameID and mode/region

            cur.execute("""INSERT INTO Attempts (GameID, Username)
                        VALUES (?, ?)""", (GameID, session['username'],))
            con.commit() # Fill in attempts table with gameID and Username 
            con.close()

            round_count = 1 #set round_count to 1
            return redirect(url_for('solo')) # reload page
        
        elif round_count < 6: #if game hasn't ended
            image = findImage()
            if not(image is None):
                return render_template('solo.html', image=image) #show page with image in round
            else:
                base = "https://graph.mapillary.com/images?access_token=MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1&fields=id&bbox="
                bbox = "-180,-90,180,90"  
                x = requests.get(base + bbox, params={'limit': 10}) 
                #Generate image id and limit amount of data retrieved
                
                parsed_data = json.loads(x.text) #Turn into python dictionary
                image = parsed_data['data'][0]['id'] #Take first image ID 
                con = sqlite3.connect("App.db")
                cur = con.cursor()
                cur.execute(f"""UPDATE Games 
                                SET image{round_count} = ?
                                 WHERE GameID = ?""", (image, session.get("GameID"))) # adds image to current game record
                con.commit()
                con.close()
                return render_template('solo.html', image=image) #show page with new image from the new round
        
        else: #if round => 6
                global stage_count 
                stage_count = 0
                # set the stage counter to 0
               
                round_count = 0
                # set the round counter to 0
                
                session.pop("GameID", None)
                session.pop("points", None)
                session.pop("latget", None)
                session.pop("lngget", None)
                return redirect(url_for('home')) #send to home page

    elif request.method == "POST": #POST request
        image = findImage() #Get current image ID
        url = f"https://graph.mapillary.com/{image}?access_token={access_token}&fields=id,computed_geometry,detections.value"
        y = requests.get(url, params={'limit': 1}) #to get the coordinates of the generated image
        locations = json.loads(y.text)
        lngget = locations['computed_geometry']['coordinates'][0] #longitude of streetview image
        latget = locations['computed_geometry']['coordinates'][1] #lattitude of streetview image
        print(latget)
        print(lngget)
         #shows coordinates of image
        user_lat = request.args.get('lat') #lattitude that is guessed by the user 
        user_lng = request.args.get('lng') #longitude that is guessed by the user
        
        con = sqlite3.connect("App.db")
        cur = con.cursor()
        cur.execute(f"""UPDATE Games
                    SET LatLong{round_count} = ?
                    WHERE GameID = ?""", (str(latget) + "," + str(lngget), session.get("GameID"))) #Store image coordinates
        con.commit()

        cur.execute(f"""UPDATE Attempts
                    SET Guess{round_count} = ?
                    WHERE GameID = ?""", (str(user_lat) + "," + str(user_lng), session.get("GameID"))) #Store guess coordinates
        con.commit()
        con.close()

        dist = distance(latget, lngget, user_lat, user_lng) #distance between the guessed coordinates and the actual coordinates
        points = points_calc(dist)
        session['latget'] = latget
        session['lngget'] = lngget #Sessions for lat and lng of image
        session['points'] = points # session defined in POST
        print(points)
        return render_template('solo.html', image=image, points=points) 
    else:
        raise ValueError("invalid")
		
		
	
if __name__ == "__main__":
    app.run(debug=True)