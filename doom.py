#/usr/bin/env python
from flask import Flask, render_template, request, json #type:ignore
import os
import sqlite3

app = Flask(__name__)
path = os.path.dirname(__file__)

mydb = sqlite3.connect("doom.db") #opens database in this thread
cur = mydb.cursor() #creates cursor in database to execute commands
cur.execute("CREATE TABLE IF NOT EXISTS user(username VARCHAR[32] NOT NULL PRIMARY KEY, password VARCHAR[32] NOT NULL)")
cur.execute("CREATE TABLE IF NOT EXISTS current(username VARCHAR[32] NOT NULL, password VARCHAR[32] NOT NULL)")
mydb.commit() #commits the database so it persists between sessions
mydb.close() #closes the database thread

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
def showAndTell():
   username = getUsername()
   return render_template('focus.html', name=username)

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
