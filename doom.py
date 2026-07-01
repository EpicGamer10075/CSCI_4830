#/usr/bin/env python
from flask import Flask, render_template, request #type:ignore
import os
import datetime
import time
import sqlite3
import signal
import pynput

app = Flask(__name__)

mydb = sqlite3.connect("doom.db") #opens database in this thread
cur = mydb.cursor() #creates cursor in database to execute commands

'''Structure of tables:
user: {username: string[32], password: string[32]}
current: {username: string[32], password: string[32]}
active_timer: {id: int, duration: int, remaining time: string(datetime), date: string(datetime)}
completed_timers: {id: int, duration: int, focus%: float, date: String(ISOFormat)}
goals: {id: int, username string{32}, start date: string(date), end date: string(date), target_focus_percentage: int}
'''
cur.execute("CREATE TABLE IF NOT EXISTS user(username VARCHAR[32] NOT NULL PRIMARY KEY, password VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS current(username VARCHAR[32] NOT NULL, password VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS active_timer(id INTEGER PRIMARY KEY AUTOINCREMENT, duration int NOT NULL, remaining_time VARCHAR[32] NOT NULL, date VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS completed_timers(id INTEGER PRIMARY KEY AUTOINCREMENT, duration int NOT NULL, focus float(24) NOT NULL, date VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, target_focus_percentage INTEGER NOT NULL)")
res = cur.execute(f"SELECT username, password FROM current")
#print(f"{res.fetchone()!r}")
if f"{res.fetchone()!r}" == "None": #if current is empty (should only happen on first startup)
    cur.execute(f"INSERT INTO current(username, password) VALUES ('Logged Out','')") #insert 'Logged Out' into current
mydb.commit() #commits the database so it persists between sessions
mydb.close() #closes the database thread


#################################################################
# START User_Input
#################################################################
def inputListener():
    def receiveSignal(signalNumber, frame): #detects when SIGILL (crtl+C) is triggered
        print('Received:', signalNumber)
        pynput.keyboard.Listener.stop(listenerK) #stops listenerK
        listenerK.join() #ends listenerK
        pynput.mouse.Listener.stop(listenerM) #stops listenerM
        listenerM.join() #ends listenerM
        os.kill(os.getpid(), signal.SIGTERM) #kills Flask
        return
    
    signal.signal(signal.SIGILL, receiveSignal) #recieves Kill Signal
    signal.signal(signal.SIGINT, receiveSignal) #recieves Int_type Signal

    def on_key_press(key):
        try:
            print('alphanumeric key {0} pressed'.format(key.char))
        except AttributeError:
            print('special key {0} pressed'.format(key))
    listenerK = pynput.keyboard.Listener(on_press=on_key_press) #creates listenerK to listen for key presses
    listenerK.start()

    def on_mouse():
        print("Mouse")
    listenerM = pynput.mouse.Listener(
        on_move=on_mouse,
        on_click=on_mouse,
        on_scroll=on_mouse) #creates listenerK to listen for mouse actions (left/right/middle-click, movement, scrolling)
    listenerM.start()

inputListener()
#################################################################
# END User_Input
#################################################################


def getUsername():
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute(f"SELECT username, password FROM current")
    name = res.fetchone()
    #print(f"Name: {name!r}")
    username = name[0]
    #print("Username:", username)
    
    mydb.commit()
    mydb.close()
    
    return username

@app.route('/')
def home():    
    username = getUsername()
    return render_template('home.html', name=username)

@app.route('/focus')
def focus():
    username = getUsername()

    timerText = updateTime()
    goalText = setGoal()
    completeTimers = setComplete()
    
    return render_template('focus.html', name=username, curTimer=timerText, comTimers=completeTimers, curGoal=goalText)

@app.route('/focus', methods=["POST"]) #executes on form submission
def focusAdd():
    username = getUsername()
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()

    timerText = ""
    if str(request.form.get("tdur")) != "None": #if Focus form was submitted
        timerDur = str(request.form["tdur"]).strip() #duration of timer
        
        duration = int(timerDur)
        timeStart = str(datetime.datetime.now()) #start time of timer
        
        res = cur.execute(f"SELECT id FROM active_timer") #fetch data from current focus timer
        if str(res.fetchone()) != "None": #if current active_timer timer exists, then delete it
            cur.execute(f"DELETE FROM active_timer")
        cur.execute(f'''INSERT INTO active_timer(duration, remaining_time, date) VALUES (
                    {timerDur},
                    {("0"+str(datetime.timedelta(minutes=int(duration/60), seconds=duration%60)))!r},
                    {timeStart!r})''') #inserts data about active_timer timer into active_timer table
        
        #(pulled from updateTime())
        res = cur.execute(f"SELECT id, duration, remaining_time, date FROM active_timer") #load from active_timer table
        name = res.fetchone()

        remTime = datetime.time.fromisoformat(name[2]) #gets remaining time from active_timer table
        remTime = 3600*remTime.hour + 60*remTime.minute + remTime.second #converts into total seconds
        timerText = f"{name[0]},{name[1]},{remTime},{name[3]}"

    else: #if not focus form just submitted
        timerText = updateTime() #update time in it (only needed to do when not focus form submitted)
        
        if str(request.form.get("start_date")) != "None": #if Goal form was submitted
            goalBeg = str(request.form["start_date"]).strip()
            goalEnd = str(request.form["end_date"]).strip()
            goalFoc = str(request.form["target_focus_percentage"]).strip()
            cur.execute(f'''INSERT INTO goals(username, start_date, end_date, target_focus_percentage) VALUES (
                        {username!r},
                        {goalBeg!r},
                        {goalEnd!r},
                        {goalFoc})''')
    
    goalText = setGoal()
    completeTimers = setComplete()
    
    mydb.commit()
    mydb.close()
    return render_template('focus.html', name=username, curTimer=timerText, comTimers=completeTimers, curGoal=goalText, redir=1)

@app.route('/focusComplete') #executes on timer expiration
def focusComplete():
    username = getUsername()

    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    
    res = cur.execute(f"SELECT id, duration, remaining_time, date FROM active_timer") #load active_timer timer from active_timer table
    name = res.fetchone()

    timerDurs = name[1]

    startTime = datetime.datetime.fromisoformat(name[3])
    timerDuration = timerDurs

    cur.execute(f'''INSERT INTO completed_timers(duration, focus, date) VALUES (
                {timerDuration},
                {100.0},
                {str(startTime)!r})''')
    
    cur.execute(f"DELETE FROM active_timer")
    
    goalText = setGoal()
    completeTimers = setComplete()
    
    mydb.commit()
    mydb.close()
    return render_template('focus.html', name=username, curTimer="", comTimers=completeTimers, curGoal=goalText, redir=1)

@app.route('/focusRemove/<elementType>/<elementID>') #remove specified element (elementType = "timer" or "goal")
def focusRemove(elementType, elementID):
    username = getUsername()
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    
    if elementType == "timer": #if Focus form was submitted
        cur.execute(f"DELETE FROM completed_timers WHERE id={elementID}") #delete timer with elementName
    elif elementType == "goal":
        cur.execute(f"DELETE FROM goals WHERE id={elementID}") #delete goal with elementName
    
    timerText = updateTime() #update time in it
    goalText = setGoal()
    completeTimers = setComplete()

    mydb.commit()
    mydb.close()
    return render_template('focus.html', name=username, curTimer=timerText, comTimers=completeTimers, curGoal=goalText, redir=1)

def updateTime(): #updates time in active_timers table, and returns timerText to give to js
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()

    res = cur.execute(f"SELECT id FROM active_timer") #fetch data from current active_timer
    if str(res.fetchone()) == "None": #if current active_timer is empty, then return ""
        mydb.commit()
        mydb.close()
        return ""
    
    res = cur.execute(f"SELECT duration, date FROM active_timer") #load duration & date from active_timer
    name = res.fetchone()

    duration = name[0]
    timeStart = name[1]
    timeDiff = datetime.datetime.now() - datetime.datetime.fromisoformat(timeStart) #difference between now and timeStart
    timeDur = datetime.timedelta(seconds=duration)
    cur.execute(f"UPDATE active_timer SET remaining_time = '0{timeDur - timeDiff}' ") #updates active_timer's remaining time


    res = cur.execute(f"SELECT id, duration, remaining_time, date FROM active_timer") #load from active_timer table
    name = res.fetchone()

    remTime = datetime.time.fromisoformat(name[2]) #gets remaining time from active_timer table
    remTime = 3600*remTime.hour + 60*remTime.minute + remTime.second #converts into total seconds
    timerText = f"{name[0]},{name[1]},{remTime},{name[3]}"
    
    mydb.commit()
    mydb.close()
    return timerText

def setComplete():
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute("SELECT id, duration, focus, date FROM completed_timers")
    completeTimers = ""
    for name in res.fetchall():
        completeTimers += f"{name[0]},{name[1]},{name[2]},{name[3]};"
    mydb.commit()
    mydb.close()
    return completeTimers

def setGoal():
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute("SELECT id, start_date, end_date, target_focus_percentage FROM goals")
    goalText = ""
    for name in res.fetchall():
        goalText += f"{name[0]},{name[1]},{name[2]},{name[3]};"
    mydb.commit()
    mydb.close()
    return goalText    

@app.route('/pwreset')
def pwReset():
    username = getUsername()
    return render_template('pwReset.html', name=username)
@app.route('/pwreset', methods=["POST"])
def pwResetGo():
    username = request.form["username"]
    pwNew    = request.form["pwNew"]
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute(f"SELECT username, password FROM user")
    name = res.fetchall()
    for user in name: #checks through all users in table
        #print(f"User: {user[0]}")
        if user[0] == username: #if user in table matches usernames with provided username
            #print("Username match:", user[0])
            verify = "Reset Password!" #update user and current to have pwNew as their password
            cur.execute(f"UPDATE user SET password = '{pwNew}' WHERE username = '{username}'") 
            break #exit loop, as there can only be one matched username
        else:
            verify = "Invalid Username!"
    mydb.commit()
    mydb.close()
    
    username = getUsername()
    return render_template('pwReset.html', name=username, verify=verify)

@app.route('/pwchange')
def pwChange():
    username = getUsername()
    return render_template('pwChange.html', name=username)
@app.route('/pwchange', methods=["POST"])
def pwChangeGo():
    pwPrev = request.form["pwPrev"]
    pwNew  = request.form["pwNew"]
    username = getUsername()
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute(f"SELECT username, password FROM user")
    name = res.fetchall()
    for user in name: #checks through all users in table
        #print(f"User: {user}")
        if user[0] == username:
            if user[1] == pwPrev: #if user in table matches passwords with pwPrev
                #print("Password match:", user[1])
                verify = "Changed Password!" #update user and current to have pwNew as their password
                cur.execute(f"UPDATE user SET password = '{pwNew}' WHERE username = '{username}'")
                cur.execute(f"UPDATE current SET password = '{pwNew}'")
            else:
                verify = "Invalid Password!" 
            break #exit loop, as there can only be one matched username
    mydb.commit()
    mydb.close()
    
    return render_template('pwChange.html', name=username, verify=verify)

@app.route('/register')
def register():
    username = getUsername()
    return render_template('register.html', name=username)
@app.route('/register', methods=["POST"])
def registerUser():
    username = request.form["username"]
    password = request.form["password"]

    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute(f"SELECT username FROM user")
    name = res.fetchall()
    #print(f'{name!r}')
    if not(username in f'{name!r}'):#if username not in table
        #print(f"Username {username} not in user table")
        #print(f"UPDATE current SET username = '{username}'")
        cur.execute(f"INSERT INTO user(username, password) VALUES ('{username}','{password}')")
        
        cur.execute(f"UPDATE current SET username = '{username}'")
        cur.execute(f"UPDATE current SET password = '{password}'")
        verify = "Registered User!"
    else:
        verify = "Username already registered!" 
    #print(verify)
    mydb.commit() #commits the database so it persists between sessions
    mydb.close()
    
    return render_template('register.html', name=username, verify=verify)

@app.route('/login')
def login():
    username = getUsername()
    return render_template('login.html', name=username, verify="")
@app.route('/login', methods=["POST"])
def loginUser():
    username = request.form["username"]
    password = request.form["password"]
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute(f"SELECT username, password FROM user")
    name = res.fetchall()
    for user in name: #checks through all users in table
        #print(f"User: {user}")
        if user[0] == username:
            if user[1] == password: #if user in table matches passwords with pwPrev
                #print("Password match:", user[1])
                verify = "Logged in as "+username+"!" #update current to provided username and password
                cur.execute(f"UPDATE current SET username = '{username}'")
                cur.execute(f"UPDATE current SET password = '{password}'")
            else:
                verify = "Username or Password incorrect"
            break #exit loop, as there can only be one matched username
        else:
            verify = "Username or Password incorrect"
    mydb.commit()
    mydb.close()
    
    username = getUsername()
    return render_template('login.html', name=username, verify=verify)

@app.route('/logout')
def logout():
    username = getUsername()
    return render_template('logout.html', name=username, verify="")
@app.route('/logout', methods=["POST"])
def logoutUser():  
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    cur.execute(f"UPDATE current SET username = 'Logged Out'")
    cur.execute(f"UPDATE current SET password = ''")
    mydb.commit()
    mydb.close()
    verify = "Logged out"
    
    username = getUsername()
    return render_template('logout.html', name=username, verify=verify)

@app.errorhandler(404)
def error(e):
    username = getUsername()
    return render_template('404.html', name=username)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=15271, debug=True)
