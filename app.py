from flask import Flask, jsonify, request, render_template, redirect

import sqlite3
from datetime import datetime

app = Flask(__name__)

def initialdb():
    with sqlite3.connect('workout.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS entries
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      date TEXT,
                      exercise TEXT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                      set INTEGER,
                      reps INTEGER,
                      weight REAL,
                      notes TEXT)''')  # Added missing comma
        conn.commit()
        conn.close()

@app.route('/')
def index():
    with sqlite3.connect('workout.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM entries ORDER BY date DESC, timestamp DESC")

        entries = c.fetchall()
        return render_template('index.html', entries=entries)
    conn.close()

@app.route('/add', methods=['POST'])
def add_entry():
    with sqlite3.connect('workout.db') as conn:
        c = conn.cursor()
        date = request.form['date']
        exercise = request.form['exercise']
        set = request.form['set']
        repts = request.form['reps']
        weight = request.form['weight']
        notes = request.form['notes']
        c.execute("INSERT INTO entries (date, exercise, set, reps, weight, notes) VALUES(?,?,?,?,?,?,?)" )
        conn.commit()
        conn.close()
        return redirect('/')
if __name__ == '__main__':
    initialdb()
    app.run(debug=True)
    

        
        

    
    
    



