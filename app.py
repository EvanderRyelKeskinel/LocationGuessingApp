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
    round_temp = cur.execute("SELECT Round FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() 
    round_count = round_temp [0]
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
        Round INTEGER NOT NULL,
        Stage INTEGER NOT NULL,
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

@app.route('/login', methods = ['GET', 'POST']) #Defines a route with /login with both methods
def login():
    if 'Username' in session:
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
                        session['Username'] = request.form['un']
                        return redirect(url_for('home'))
                        #log user in and redirect them

        else: #GET request
            return render_template('login.html')


@app.route('/', methods = ['GET', 'POST']) #Defines a route with just / for both POST and GET methods
def signup():
    if 'Username' in session:
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
                cur.execute(""" INSERT INTO Users (Username, SALT, Password, Round, Stage) 
                        VALUES (?, ?, ?, 0, 0) """,
                        (request.form['un'], SALT, (sha512((request.form['pw'].encode('utf-8') + str(SALT).encode('utf-8'))).digest()))) 
                        #adds username and hashed password to database
                        #enodes the password and hash into a form that allows it to be hashed
                        #initialises round and stage as 0
                con.commit() #commit the SQL
                con.close() #Close the connection
                
                session['Username'] = request.form['un'] #create a session for the user on signup
            return redirect(url_for('home')) #redirect to home page
        
        else:  #GET request (loading in page)
            return render_template('signup.html')

@app.route('/home')
def home():
    if 'GameID' in session:
        return redirect(url_for('solo'))
    if not('Username' in session):
        return redirect(url_for('signup')) #if user not logged in, redirect to signup page
    else:
        return render_template('home.html') #load home page

@app.route('/api/datapoint')
def submitsend(): #Triggered when submit button clicked
    
    point_change = session.get('points') #points scored in the round
    image_lat = session.get('latget') 
    image_lng = session.get('lngget') 
    #lattitude and longitude of users guess
    
    con = sqlite3.connect("App.db")
    cur = con.cursor()
    points_fetch = cur.execute("SELECT Points FROM Attempts WHERE Username=? AND GameID=?", (session.get('Username'),session.get("GameID"),)).fetchone() 
    #fetch value of Points in game

    if points_fetch != None: #If points is not null 
        total_points = points_fetch [0] 
        cur.execute("""UPDATE Attempts 
                    SET Points = ?
                    WHERE Username = ? AND GameID =?""", (total_points + point_change, session.get("Username"), session.get("GameID"),))
        con.commit()
        #Update points by adding the new value
    else:
        print("Error, Points is null in database") #Error response for debugging purposes
    con.close()
    dictionary = {
		'points': point_change, #points in dict

		'image_lat': image_lat,

		'image_lng': image_lng
          # coordinates in dict
	}
    return jsonify(dictionary) #returns as JSON object




@app.route('/round_data', methods=['POST']) # POST request called when new round started
def roundcount():
    con = sqlite3.connect("App.db")
    cur = con.cursor()
    round_count = cur.execute(f"SELECT Round FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() [0]
    round_temp = round_count + 1 # round is increased by 1
    cur.execute("""UPDATE Users 
                    SET Round = ?
                    WHERE Username = ?""", (round_temp, session.get("Username")))
    con.commit()
    con.close()
    dictionary = {
        'round': round_temp # round placed in a dictionary
    }
    return jsonify(dictionary) #Turned into json object so it can be read by javascript.


@app.route('/stage_count', methods=['POST', 'GET'])  
def stagecount():
    if request.method == "GET": # GET request
        con = sqlite3.connect("App.db")
        cur = con.cursor()
        stage_count = cur.execute("SELECT Stage FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() [0]
        con.close()
        dict = {
            'stage': stage_count
        } #defines a dictionary to be jsonified
        return jsonify(dict)
    
    else: # POST request 
        con = sqlite3.connect("App.db")
        cur = con.cursor()
        stage_count = cur.execute("SELECT Stage FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() [0]
        cur.execute("""UPDATE Users 
                        SET Stage = ?
                        WHERE Username = ?""", (stage_count + 1, session.get("Username"),))
        con.commit()
        con.close()
        return jsonify(stage_count) 

@app.route('/solo', methods=['GET', 'POST']) #POST request now considered
def solo():
    if not('Username' in session):
        return redirect(url_for('signup')) #if user not logged in, redirect to signup page
    elif request.method == "GET": #Get request
        con = sqlite3.connect("App.db")
        cur = con.cursor()
        stage_count = cur.execute(f"SELECT Stage FROM Users WHERE Username=?", (session.get('Username'),)).fetchone()
        round_temp = cur.execute(f"SELECT Round FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() 
        round_count = round_temp [0]
        if round_count == 0:
            GameID = random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10)) # random 10 digit string
            session['GameID'] = GameID
            con = sqlite3.connect("App.db") #Connect database
            cur = con.cursor()
            if 'Region' in session: #If user has clicked solo regional
                Region_Game = session.get('Region')
            else: 
                Region_Game = "Worldwide" #default region setting
            
            
            cur.execute("""INSERT INTO Games (GameID, Mode, Region) 
                            VALUES (?, ?, ?)""", (GameID, "SoloRanked", Region_Game,))
            con.commit() # fill in Games table with generated GameID and mode/region

            cur.execute("""INSERT INTO Attempts (GameID, Username, Points)
                        VALUES (?, ?, ?)""", (GameID, session['Username'], 0,))
            con.commit() # Fill in attempts table with gameID and Username 

            cur.execute("""UPDATE Users 
                    SET Round = ?
                    WHERE Username = ?""", (1, session.get("Username"))) #set round_count to 1
            con.commit()
            con.close() 

            return redirect(url_for('solo')) # reload page
        
        elif round_count < 6: #if game hasn't ended
            image = findImage() 
            if not(image is None):
                return render_template('solo.html', image=image) #show page with image in round
            else:
                API_token = "MLY|7884436731651628|991d31489dc0ba2a68fd9c321c4d2cd1"
                base = f"https://graph.mapillary.com/images?access_token={API_token}&fields=id&bbox="
                
                if 'Region' in session: 
                    con = sqlite3.connect("App.db")
                    cur = con.cursor()
                    value = cur.execute(f"SELECT BoundingBox FROM Regions WHERE Region=?", (session.get('Region'),)).fetchone()
                    bbox = value [0]
                    con.close()
                    #Get the bounding box corresponding to the selected region in the database
                else: 
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
                con = sqlite3.connect("App.db")
                cur = con.cursor()
                cur.execute("""UPDATE Users 
                                SET Round = ?
                                WHERE Username = ?""", (0, session.get("Username"))) 
                cur.execute("""UPDATE Users 
                                SET Stage = ?
                                WHERE Username = ?""", (0, session.get("Username"))) 
                #set round_count to 0
                # set the Stage counter to 0
                con.commit()
                con.close()
                if 'Region' in session:
                    session.pop("Region", None)
                else: #If gamemode is ranked
                    con = sqlite3.connect("App.db")
                    cur = con.cursor()
                    highscore = cur.execute("SELECT Highest_solo FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() [0]
                    #users high score
                    get_pointstotal = points_fetch = cur.execute("SELECT Points FROM Attempts WHERE Username=? AND GameID=?", (session.get('Username'),session.get("GameID"),)).fetchone() 
                    #Users score this round
                    if get_pointstotal != None:
                        total_points = get_pointstotal [0]
                        if total_points > highscore: #Check if points scored in the game is a high score
                            cur.execute("""UPDATE Users 
                                SET Highest_solo = ?
                                WHERE Username = ?""", (total_points, session.get("Username")))  #Set high score to points scored
                            con.commit()
                    else:
                        print("points not found")
                    con.close()
                
                session.pop("GameID", None)
                session.pop("points", None)
                session.pop("latget", None)
                session.pop("lngget", None)
                #Reset all client-side variables 
                return redirect(url_for('home')) #send to home page

    elif request.method == "POST": #POST request
        image = findImage() #Get current image ID
        url = f"https://graph.mapillary.com/{image}?access_token={access_token}&fields=id,computed_geometry,detections.value"
        y = requests.get(url, params={'limit': 1}) #to get the coordinates of the generated image
        locations = json.loads(y.text)
        lngget = locations['computed_geometry']['coordinates'][0] #longitude of streetview image
        latget = locations['computed_geometry']['coordinates'][1] #lattitude of streetview image
         #shows coordinates of image
        user_lat = request.args.get('lat') #lattitude that is guessed by the user 
        user_lng = request.args.get('lng') #longitude that is guessed by the user
        con = sqlite3.connect("App.db")
        cur = con.cursor()
        round_temp = cur.execute(f"SELECT Round FROM Users WHERE Username=?", (session.get('Username'),)).fetchone() 
        round_count = round_temp [0]
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
	


@app.route('/SoloGamemodes', methods=['GET', 'POST']) # GET and POST request
def sologames():
    if 'GameID' in session:
        return redirect(url_for('solo')) #redirects back to game if one is ongoing
    
    if not('Username' in session): # if user not logged in redirect to signup
        return redirect(url_for('signup'))
    else:
        if request.method == "POST": # if post request (data sent)
            session['Region'] = request.form['Region']
            return redirect(url_for('solo'))
        else: #if get request (page loaded)
            return render_template('SoloGamemodes.html') 

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('Username') #removes username from session
    return redirect(url_for('signup')) # redirects to signup page


@app.route('/LeaveGame', methods=["POST"])
def leavegame():
    if request.method == "POST": 
        con = sqlite3.connect("App.db")
        cur = con.cursor()
        cur.execute("""UPDATE Users 
                        SET Round = ?
                        WHERE Username = ?""", (6, session.get("Username"))) #set to 6
        con.commit()
        con.close()
        return "."
    else:
        print("Error from /LeaveGame")
        return "."

@app.route('/leaderboard')
def Leaderboard():
    if not('Username' in session): # if user not logged in redirect to signup
        return redirect(url_for('signup'))
    else: 
        return render_template("leaderboard.html")

@app.route('/ranking')
def ranking():
    con = sqlite3.connect("App.db")
    cur = con.cursor()
    cur.execute("SELECT Highest_solo, Username from Users ORDER BY Highest_solo DESC LIMIT 10") 
    #get ordered pair of username and high score in order of highest score
    rows = cur.fetchall()
    dictionary = {
        'score_first': rows[0][0],
        'name_first': rows[0][1],
        'score_second': rows[1][0],
        'name_second': rows[1][1],
        'score_third': rows[2][0],
        'name_third': rows[2][1],
        'score_fourth': rows[3][0],
        'name_fourth': rows[3][1],
        'score_fifth': rows[4][0],
        'name_fifth': rows[4][1],
    } 
    #store these values in a dictionary
    con.close()
    return jsonify(dictionary) 

if __name__ == "__main__":
    app.run(debug=True)