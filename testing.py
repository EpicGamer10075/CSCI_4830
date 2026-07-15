import pytest #type:ignore
import doom
import requests #type:ignore
import sqlite3

def funcTimer() -> int:
	requests.post("http://127.0.0.1:15271/focus", data = {"tdur":10})
	mydb = sqlite3.connect("doom.db")
	cur = mydb.cursor()
	result = cur.execute(f"SELECT duration FROM active_timer").fetchone()[0]
	cur.execute(f"DELETE FROM active_timer")
	mydb.close()
	return result

def funcBreak(td, bs, bd) -> int:
	requests.post("http://127.0.0.1:15271/focus", data = {"tdur":td, "bstr":bs, "bdur":bd})
	mydb = sqlite3.connect("doom.db")
	cur = mydb.cursor()
	tdur = cur.execute(f"SELECT duration FROM active_timer").fetchone()[0]
	bstr, bdur = cur.execute(f"SELECT break_start, break_duration FROM break").fetchone()
	cur.execute(f"DELETE FROM active_timer")
	mydb.close()
	return (tdur, bstr, bdur)

def funcGoal() -> str:
	requests.post("http://127.0.0.1:15271/focus", data = {"start_date":"2026-07-14", "end_date":"2026-07-16", "target_focus_percentage":75})
	mydb = sqlite3.connect("doom.db")
	cur = mydb.cursor()
	result = cur.execute(f"SELECT start_date, end_date, target_focus_percentage FROM goals").fetchall()[-1]
	mydb.close()
	return result

def test_doom():
	assert funcTimer() == 10
	assert funcGoal() == ('2026-07-14', '2026-07-16', 75)
	assert funcBreak(10, 5, 3) == (10, 5, 3)
	assert funcBreak(10, 5, 13) == (10, 5, 3) #checks bounds for break form