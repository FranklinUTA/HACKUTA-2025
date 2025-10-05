from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
db_file = "freakybird.db"

# --- Initialize database and table ---
def init_db():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    # Create table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS highscore (
            id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL
        )
    ''')
    # Ensure there is always one row for highscore
    c.execute('SELECT * FROM highscore WHERE id=1')
    if c.fetchone() is None:
        c.execute('INSERT INTO highscore (id, score) VALUES (1, 0)')
    conn.commit()
    conn.close()

init_db()

# --- Get highscore ---
@app.route('/get_highscore', methods=['GET'])
def get_highscore():
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT score FROM highscore WHERE id=1')
    score = c.fetchone()[0]
    conn.close()
    return jsonify({'highscore': score})

# --- Set highscore ---
@app.route('/set_highscore', methods=['POST'])
def set_highscore():
    data = request.get_json()
    new_score = data.get('score', 0)
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('SELECT score FROM highscore WHERE id=1')
    current_score = c.fetchone()[0]
    if new_score > current_score:
        c.execute('UPDATE highscore SET score = ? WHERE id=1', (new_score,))
        conn.commit()
    conn.close()
    return jsonify({'highscore': max(current_score, new_score)})

if __name__ == '__main__':
    app.run(debug=True)
