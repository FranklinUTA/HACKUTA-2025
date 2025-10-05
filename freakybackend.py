from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "freakyhighscore.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY,
                highscore INTEGER
            )
        ''')
        # Ensure the row exists
        c.execute('SELECT COUNT(*) FROM scores WHERE id=1')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO scores (id, highscore) VALUES (1, 0)')
        conn.commit()

@app.route('/get_highscore', methods=['GET'])
def get_highscore():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT highscore FROM scores WHERE id=1')
        score = c.fetchone()[0]
    return jsonify({'highscore': score})

@app.route('/set_highscore', methods=['POST'])
def set_highscore():
    data = request.get_json()
    new_score = int(data.get('score', 0))

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('SELECT highscore FROM scores WHERE id=1')
        current = c.fetchone()[0]
        if new_score > current:
            c.execute('UPDATE scores SET highscore=? WHERE id=1', (new_score,))
            conn.commit()
            print(f"Updated highscore to {new_score}")
            return jsonify({'highscore': new_score, 'updated': True})
        else:
            print(f"Score {new_score} not higher than {current}")
            return jsonify({'highscore': current, 'updated': False})

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
    app.run(debug=True)
