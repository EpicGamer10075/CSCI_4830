#!/usr/bin/env python3

from flask import Flask, render_template, request #type:ignore
import os
import datetime

app = Flask(__name__)
path = os.path.dirname(__file__)

@app.route('/')
def todo():
   rFile = open(path+"\\todo.txt", "r")
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

   finalID = int(open(path+"\\todo.txt", "r").read().split("\n")[-2].split(" ")[0]) #gets int id of last task in todo.txt

   aFile = open(path+"\\todo.txt", "a")
   aFile.write(str(finalID+1)+" "+str(datetime.datetime.now()).split(" ")[0]+" ") #nextID, CreationTimestamp (only date, not time)
   aFile.write("C ") #CompetionTimestamp: C as a placeholder for later replacement, and to indicate incomplete
   aFile.write(str(dueDate)+" "+str(description)+"\n") #DueDate, Description

   return render_template('todo_list.html', data="", redir=1)

@app.route('/mark_complete/<task_id>')
def complete(task_id):
   rFile = open(path+"\\todo.txt", "r")
   lines = rFile.read().split("\n")
   wFile = open(path+"\\todo.txt", "w")
   for l in range(len(lines)-1): #for all tasks in todo.txt
      line = lines[l]
      if line.split(" ")[0] == task_id: #if id matches task_id
         wFile.write(line.replace("C", str(datetime.datetime.now()).split(" ")[0], 1)); #change C to current date
      else:
         wFile.write(line) #else, just keep the task the same
      wFile.write("\n");
   
   return render_template('todo_list.html', data="", redir=1)

@app.route('/delete_task/<task_id>')
def delete(task_id):
   rFile = open(path+"\\todo.txt", "r")
   lines = rFile.read().split("\n")
   wFile = open(path+"\\todo.txt", "w")
   for l in range(len(lines)-1): #for all tasks in todo.txt
      if lines[l].split(" ")[0] != task_id: #if id doesn't match task_id, keep task in file
         wFile.write(lines[l]+"\n"); #else, task will be removed from file
   
   return render_template('todo_list.html', data="", redir=1)

@app.errorhandler(404)
def error(e):
   return render_template('404.html')

@app.errorhandler(500)
def error(e):
   return render_template('500.html')

if __name__ == '__main__':
   app.run(debug=False, host="0.0.0.0", port="15271")