#/usr/bin/env python
from flask import Flask, render_template, request #type:ignore
import os
import datetime
import time
import sqlite3
import signal
import pynput #type:ignore
import threading

app = Flask(__name__)

mydb = sqlite3.connect("doom.db") #opens database in this thread
cur = mydb.cursor() #creates cursor in database to execute commands

'''Structure of tables:
user: {username: string[32], password: string[32]}
current: {username: string[32], password: string[32]}
active_timer: {id: int, duration: int, remaining time: string(datetime), date: string(datetime)}
break: {id int, break_start int, break_duration int}
distraction: {id: int, duration: int, end_time: string(datetime), cause: string}
completed_timers: {id: int, duration: int, focus%: float, date: String(ISOFormat)}
goals: {id: int, username string{32}, start date: string(date), end date: string(date), target_focus_percentage: int}
'''
cur.execute("CREATE TABLE IF NOT EXISTS user(username VARCHAR[32] NOT NULL PRIMARY KEY, password VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS current(username VARCHAR[32] NOT NULL, password VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS active_timer(id INTEGER PRIMARY KEY AUTOINCREMENT, duration int NOT NULL, remaining_time VARCHAR[32] NOT NULL, date VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS break(id INTEGER PRIMARY KEY AUTOINCREMENT, break_start int NOT NULL, break_duration int NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS distraction(id INTEGER PRIMARY KEY AUTOINCREMENT, duration int NOT NULL, end_time VARCHAR[32] NOT NULL, cause VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS completed_timers(id INTEGER PRIMARY KEY AUTOINCREMENT, duration int NOT NULL, focus float(24) NOT NULL, date VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS goals(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, target_focus_percentage INTEGER NOT NULL)")
cur.execute("DELETE FROM active_timer")
cur.execute("DELETE FROM distraction")
cur.execute("DELETE FROM break")
res = cur.execute(f"SELECT username, password FROM current")
#print(f"{res.fetchone()!r}")
if f"{res.fetchone()!r}" == "None": #if current is empty (should only happen on first startup)
    cur.execute(f"INSERT INTO current(username, password) VALUES ('Logged Out','')") #insert 'Logged Out' into current
mydb.commit() #commits the database so it persists between sessions
mydb.close() #closes the database thread


#################################################################
# START User_Input
#################################################################
def receiveSignal(signalNumber, frame): #detects when SIGILL (crtl+C) is triggered
    #print('Received:', signalNumber)
    global threadEnd
    threadEnd = True #setting this will end the thread
    inputMonitor.join() #ends inputMonitor
    pynput.keyboard.Listener.stop(listenerK) #stops listenerK
    listenerK.join() #ends listenerK
    pynput.mouse.Listener.stop(listenerM) #stops listenerM
    listenerM.join() #ends listenerM
    os.kill(os.getpid(), signal.SIGTERM) #kills Flask
    return

signal.signal(signal.SIGILL, receiveSignal)
signal.signal(signal.SIGINT, receiveSignal)


tester = "init" #use current render_template to change page without reload (DOESN'T WORK)
threadEnd = False #flag to end inputMonitor thread
durAFK = 0.0 #duration without input, in seconds
thresholdAFK = 5*4.0 #normally 5*60

def getAFK(): #spins in place, detecting if user has gone AFK
    global tester
    global threadEnd
    global durAFK
    while not threadEnd:
        if durAFK > thresholdAFK: #if 5 minutes have passed without input, [trigger AFK]
            tester = "AFK"
            #print("AFK")
        #else:
        durAFK += 0.1
        time.sleep(0.1)
    return

def on_key_press(key):
    '''try:
        print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
        print('special key {0} pressed'.format(key))'''
    global durAFK
    durAFK = 0.0 #reset to 0 when key pressed
listenerK = pynput.keyboard.Listener(on_press=on_key_press)
listenerK.start()

def on_mouse():
    #print("Mouse")
    global durAFK
    durAFK = 0.0 #reset to 0 when mouse manipulated (LClick, RC, MC, Scroll, Move)
listenerM = pynput.mouse.Listener(
    on_move=on_mouse,
    on_click=on_mouse,
    on_scroll=on_mouse)
listenerM.start()

inputMonitor = threading.Thread(target=getAFK)
inputMonitor.start() #starts inputMonitor as thread with function getAFK()

@app.route('/process-data', methods=['POST']) #not viewable webpage, just used for fetch requests
def process_data():
    global durAFK
    return str(durAFK > thresholdAFK)

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
    distText = setDistraction()
    
    return render_template('focus.html', name=username, curTimer=timerText, comTimers=completeTimers, curGoal=goalText, curDist=distText)

@app.route('/focus', methods=["POST"]) #executes on form submission
def focusAdd():
    username = getUsername()
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()

    timerText = ""
    if str(request.form.get("tdur")) != "None": #if Focus form was submitted
        timerDur = str(request.form["tdur"]).strip() #duration of timer
        cur.execute("DELETE FROM break") #removes current break if overwriting timer
        if str(request.form.get("bstr")) != "None": #if break exists
            cur.execute(f'''INSERT INTO break(break_start, break_duration) VALUES (
                        {request.form["bstr"]},
                        {request.form["bdur"]})''')

        duration = int(timerDur)
        timeStart = str(datetime.datetime.now()) #start time of timer
        
        res = cur.execute(f"SELECT id FROM active_timer") #fetch data from current active_timer
        if str(res.fetchone()) != "None": #if current active_timer timer exists, then delete it
            cur.execute(f"DELETE FROM active_timer")
        cur.execute(f'''INSERT INTO active_timer(duration, remaining_time, date) VALUES (
                    {timerDur},
                    {("0"+str(datetime.timedelta(minutes=int(duration/60), seconds=duration%60)))!r},
                    {timeStart!r})''') #inserts data about active_timer timer into active_timer table
        
        cur.execute(f"DELETE FROM distraction") #empties distraction table

        #(pulled from updateTime())
        res = cur.execute(f"SELECT id, duration, remaining_time, date FROM active_timer") #load from active_timer table
        name = res.fetchone()

        remTime = datetime.time.fromisoformat(name[2]) #gets remaining time from active_timer table
        remTime = 3600*remTime.hour + 60*remTime.minute + remTime.second #converts into total seconds
        timerText = f"{name[0]},{name[1]},{remTime},{name[3]}"

    else: #if not timer form just submitted
        timerText = updateTime() #update time in it (only needed to do when not timer form submitted)
        
        if str(request.form.get("start_date")) != "None": #if Goal form was submitted
            goalBeg = str(request.form["start_date"]).strip()
            goalEnd = str(request.form["end_date"]).strip()
            goalFoc = str(request.form["target_focus_percentage"]).strip()
            cur.execute(f'''INSERT INTO goals(username, start_date, end_date, target_focus_percentage) VALUES (
                        {username!r},
                        {goalBeg!r},
                        {goalEnd!r},
                        {goalFoc})''')
        
        elif str(request.form.get("dname")) != "None": #if Distraction form was submitted
            distName = str(request.form["dname"]).strip()
            distDur = str(request.form["ddur"]).strip()
            cur.execute(f'''INSERT INTO distraction(duration, cause, end_time) VALUES (
                        {distDur!r},
                        {distName!r},
                        {str(datetime.datetime.now())!r})''')
    
    goalText = setGoal()
    completeTimers = setComplete()
    distText = setDistraction()
    
    mydb.commit()
    mydb.close()
    return render_template('focus.html', name=username, curTimer=timerText, comTimers=completeTimers, curGoal=goalText, curDist=distText, redir=1)

@app.route('/focusComplete/<forceStop>') #executes on timer expiration, or forcestop
def focusComplete(forceStop):
    print(forceStop)
    username = getUsername()

    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    
    res = cur.execute(f"SELECT id, duration, remaining_time, date FROM active_timer") #load active_timer timer from active_timer table
    name = res.fetchone()

    startTime = datetime.datetime.fromisoformat(name[3])
    timerDuration = name[1]

    timerDurs = []
    res = cur.execute(f"SELECT break_start, break_duration FROM break") #gets break_start and break_duration from break
    names = res.fetchall()
    if len(names) > 0: #if break exists
        name = names[0]
        timerDurs.append(name[0]) #first is time from timer_start to break_start, equal to break_start
        timerDurs.append(name[1]) #second is duration from break_start to break end, eqaul to break_duration
        timerDurs.append(timerDuration - name[0] - name[1]) #final is duration from break end to timer end, equal to timer_duration - (break_start + break_duration)
    else:
        timerDurs.append(timerDuration)

    def checkOverlap(focusStart, focusDur, distEnd, distDur): #gets overlap between a focus timer and a distraction
        if forceStop == "true":
            focusEnd = datetime.datetime.now()
        else:
            focusEnd = focusStart + datetime.timedelta(minutes=int(focusDur/60), seconds=focusDur%60) #creates end datetime of focus timer
        distStart = distEnd - datetime.timedelta(minutes=int(distDur/60), seconds=distDur%60) #creates start datetime of distraction
        
        #clamp distraction within focus
        if distStart < focusStart:
            distStart = focusStart
        if distEnd > focusEnd:
            distEnd = focusEnd
        if distStart > focusEnd: #also clamps start of distraction by end of timer, only needed on forcestop
            distStart = focusEnd
        
        if distStart < distEnd: #clamping doesn't affect other bound, so if whole dist outside focus, then this fails
            return (distEnd - distStart).total_seconds() #return overlap betewen focus and distraction
        return 0 #if no overlap, return 0
    
    timeDistracted = 0.0 #total time distracted
    
    res = cur.execute("SELECT duration, end_time FROM distraction")
    for name in res.fetchall():
        #distraction += f"{name[0]},{name[1]},{name[2]},{name[3]};"
        startFocus = 0 #start of each focus timer, past startTime
        for b in range(0, len(timerDurs), 2):
            timeDistracted += checkOverlap(
                startTime + datetime.timedelta(minutes=int(startFocus/60), seconds=startFocus%60),
                int(timerDurs[b]),
                datetime.datetime.fromisoformat(name[1]),
                int(name[0])) #increments timeDistracted by overlap between current Focus and Distraction
            if b+1 < len(timerDurs): #if not at final focus timer
                startFocus += int(timerDurs[b]) + int(timerDurs[b+1]) #increments startFocus by current Focus and next Break durations
            else:
                startFocus += int(timerDurs[b]) #increments startFocus by current/final Focus

    #print("timerDuration:",timerDuration)
    #print("timerDuration:",str(datetime.datetime.now() - startTime))
    if forceStop == "true":
        timerDuration = (datetime.datetime.now() - startTime).seconds

    cur.execute(f'''INSERT INTO completed_timers(duration, focus, date) VALUES (
                {timerDuration},
                {100 * (1 - (timeDistracted/timerDuration)):.2f},
                {str(startTime)!r})''')
    
    cur.execute(f"DELETE FROM active_timer")
    cur.execute(f"DELETE FROM distraction")
    cur.execute(f"DELETE FROM break")

    goalText = setGoal()
    completeTimers = setComplete()
    distText = setDistraction()
    
    mydb.commit()
    mydb.close()
    return render_template('focus.html', name=username, curTimer="", comTimers=completeTimers, curGoal=goalText, curDist=distText, redir=1)

@app.route('/focusRemove/<elementType>/<elementID>') #remove specified element (elementType = "timer" or "goal")
def focusRemove(elementType, elementID):
    username = getUsername()
    
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    
    if elementType == "timer": #if timer form was submitted
        cur.execute(f"DELETE FROM completed_timers WHERE id={elementID}") #delete timer with elementName
    elif elementType == "goal":
        cur.execute(f"DELETE FROM goals WHERE id={elementID}") #delete goal with elementName
    
    timerText = updateTime() #update time in it
    goalText = setGoal()
    completeTimers = setComplete()
    distText = setDistraction()

    mydb.commit()
    mydb.close()
    return render_template('focus.html', name=username, curTimer=timerText, comTimers=completeTimers, curGoal=goalText, curDist=distText, redir=1)

def updateTime(): #updates time in active_timers table, and returns timerText to give to js
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()

    res = cur.execute(f"SELECT id FROM active_timer") #fetch data from current active_timer
    if str(res.fetchone()) == "None": #if current active_timer is empty, then return ""
        #mydb.commit()
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
    #mydb.commit()
    mydb.close()
    return completeTimers

def setGoal():
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute("SELECT id, start_date, end_date, target_focus_percentage FROM goals")
    goalText = ""
    for name in res.fetchall():
        goalText += f"{name[0]},{name[1]},{name[2]},{name[3]};"
    #mydb.commit()
    mydb.close()
    return goalText

def setDistraction(): #DISTRACTION
    mydb = sqlite3.connect("doom.db")
    cur = mydb.cursor()
    res = cur.execute("SELECT id, duration, end_time, cause FROM distraction")
    distText = ""
    for name in res.fetchall():
        distText += f"{name[0]},{name[1]},{name[2]},{name[3]};"
    #mydb.commit()
    mydb.close()
    return distText

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

'''
To-Do:
    Change all file accessing to database accessing:
        [X] Focus
        [X] Complete
        [X] Goal
    Comment out stuff related to later Milestones:
        [X] Break
        [X] Distraction
        [X] AFK
        Stats (not included yet)
        Reminders
        Polish
[X] Add button to remove focus goal
'''
