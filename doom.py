#/usr/bin/env python
from flask import Flask, render_template, request, json #type:ignore
import os

app = Flask(__name__)
path = os.path.dirname(__file__)

@app.route('/')
def home():
   rFile = open(path+"\\current.txt", "r")
   username = rFile.read().split('\n')[0]
   return render_template('home.html', name=username)

@app.route('/showAndTell')
def showAndTell():
   rFile = open(path+"\\current.txt", "r")
   username = rFile.read().split('\n')[0]
   return render_template('showtell.html', name=username)

@app.route('/pwreset')
def pwReset():
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   return render_template('pwReset.html', name=username)
@app.route('/pwreset', methods=["POST"])
def pwResetGo():
   username = request.form["username"]
   pwNew    = request.form["pwNew"]
   rFile = open(path+"\\users.txt", "r")
   lines = rFile.read().split('\n')
   rFile.close()
   flag = False
   wFile = open(path+"\\users.txt", "w")
   for i in range(0, len(lines)-1, 2): #checks through all lines of users.txt
      wFile.write(lines[i]+"\n")
      if lines[i] == username and not flag: #if current username matches username in file (and username not already found in file
         flag = True                          #sets flag and breaks from loop if username is found in file
         verify = "Changed Password!"        #verify the password was correct, and was changed
         wFile.write(pwNew+"\n")             #change password
      else:                                 #if current username doesn't match username in file
         wFile.write(lines[i+1]+"\n")         #keep password the same
   if not flag:                           #if username not found in file (regarless if its password was changed or not)
      verify = "Invalid Username!"          #verify the username was invalid
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   return render_template('pwReset.html', name=username, verify=verify)

@app.route('/pwchange')
def pwChange():
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   return render_template('pwChange.html', name=username)
@app.route('/pwchange', methods=["POST"])
def pwChangeGo():
   pwPrev = request.form["pwPrev"]
   pwNew  = request.form["pwNew"]
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   rFile = open(path+"\\users.txt", "r")
   lines = rFile.read().split('\n')
   rFile.close()
   flag = False
   wFile = open(path+"\\users.txt", "w")
   for i in range(0, len(lines)-1, 2): #checks through all lines of users.txt
      wFile.write(lines[i]+"\n")
      if lines[i] == username and not flag: #if current username matches username in file (and username not already found in file
         flag = True                          #sets flag and breaks from loop if username is found in file
         if lines[i+1] == pwPrev:             #if current password matches password in file
            verify = "Changed Password!"        #verify the password was correct, and was changed
            wFile.write(pwNew+"\n")             #change password
         else:                                #if current password doesn't match password in file
            verify = "Incorrent Password!"      #verify the password was incorrect
            wFile.write(lines[i+1]+"\n")        #keep password the same
      else:                                 #if current username doesn't match username in file
         wFile.write(lines[i+1]+"\n")         #keep password the same
   if not flag:                           #if username not found in file (regarless if its password was changed or not)
      verify = "Invalid Username!"          #verify the username was invalid
   return render_template('pwChange.html', name=username, verify=verify)

@app.route('/register')
def register():
   rFile = open(path+"\\current.txt", "r")
   username = rFile.read().split('\n')[0]
   return render_template('register.html', name=username)
@app.route('/register', methods=["POST"])
def registerUser():
   username = request.form["username"]
   password = request.form["password"]
   rFile = open(path+"\\users.txt", "r")
   flag = False
   lines = rFile.read().split('\n')
   for i in range(0, len(lines), 2): #checks through all lines of file
      if lines[i] == username:
         flag = True #sets flag and breaks from loop if username is found in file
         verify = "Username already registered!" 
         break
   if not flag:
      aFile = open(path+"\\users.txt", "a") #writes new username and password to file if link isn't already in file
      aFile.write(username+"\n")
      aFile.write(password+"\n")
      aFile.close()
      verify = "Registered User!"
   
   rFile = open(path+"\\current.txt", "r")
   username = rFile.read().split('\n')[0]
   return render_template('register.html', name=username, verify=verify)

@app.route('/login')
def login():
   rFile = open(path+"\\current.txt", "r")
   username = rFile.read().split('\n')[0]
   return render_template('login.html', name=username,  verify="")
@app.route('/login', methods=["POST"])
def loginUser():
   username = request.form["username"]
   password = request.form["password"]
   rFile = open(path+"\\users.txt", "r")
   flag = False
   lines = rFile.read().split('\n')
   for i in range(0, len(lines)-1, 2): #checks through all lines of file
      if (lines[i] == username) & (lines[i+1] == password):
         flag = True #sets flag and breaks from loop if username is found in file
         verify = "Logged in as "+username+"!" 
         wFile = open(path+"\\current.txt", "w") #writes new username and password to indicate current user
         wFile.write(username+"\n")
         wFile.write(password+"\n")
         wFile.close()
         break
   if not flag:
      verify = "Username or Password incorrect"
   
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   return render_template('login.html', name=username, verify=verify)

@app.route('/logout')
def logout():
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   return render_template('logout.html', name=username, verify="")
@app.route('/logout', methods=["POST"])
def logoutUser():
   wFile = open(path+"\\current.txt", "w") #writes Logged Out to current to indicate no current user
   wFile.write("Logged Out\nNull")
   wFile.close()
   verify = "Logged out"
   username = open(path+"\\current.txt", "r").read().split('\n')[0]
   return render_template('logout.html', name=username, verify=verify)

@app.errorhandler(404)
def error(e):
   return render_template('404.html')

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=15271, debug=True)