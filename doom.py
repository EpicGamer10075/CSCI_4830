#!/usr/bin/env python3

from flask import Flask, render_template, request #type:ignore
import os
import datetime

app = Flask(__name__)
path = os.path.dirname(__file__)

@app.route('/')
def todo():
   rFile = open(path+"\\database.txt", "r")
   rData = rFile.read()
   return render_template('todo_list.html', data=rData, redir=0)

@app.route('/add',  methods=["POST"])
def add():
   dueDate = str(request.form["date"]).strip()
   description = str(request.form["description"]).strip()
   try:
      datetime.datetime.strptime(dueDate, "%Y-%m-%d") #validation for correct date
   except ValueError or TypeError:
      return render_template('todo_list.html', data="", redir=1) #automatically returns if invalid

   finalID = int(open(path+"\\database.txt", "r").read().split("\n")[-2].split(" ")[0]) #gets int id of last task in database.txt

   aFile = open(path+"\\database.txt", "a")
   aFile.write(str(finalID+1)+" "+str(datetime.datetime.now()).split(" ")[0]+" ") #nextID, CreationTimestamp (only date, not time)
   aFile.write("C ") #CompetionTimestamp: C as a placeholder for later replacement, and to indicate incomplete
   aFile.write(str(dueDate)+" "+str(description)+"\n") #DueDate, Description

   return render_template('todo_list.html', data="", redir=1)

@app.errorhandler(404)
def error(e):
   return render_template('404.html')

@app.errorhandler(500)
def error(e):
   return render_template('500.html')

if __name__ == '__main__':
   app.run(debug=False, host="0.0.0.0", port="15271")
