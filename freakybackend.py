from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect('freakyhighscore.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY,
                        highscore INTEGER
                    )''')
        c.execute('INSERT OR IGNORE INTO scores (id, highscore) VALUES (1, 0)')
        conn.commit()

@app.route('/get_highscore', methods=['GET'])
def get_highscore():
    with sqlite3.connect('freakyhighscore.db') as conn:
        c = conn.cursor()
        c.execute('SELECT highscore FROM scores WHERE id=1')
        score = c.fetchone()[0]
    return jsonify({'highscore': score})

@app.route('/set_highscore', methods=['POST'])
def set_highscore():
    new_score = int(request.json.get('score', 0))
    with sqlite3.connect('freakyhighscore.db') as conn:
        c = conn.cursor()
        c.execute('SELECT highscore FROM scores WHERE id=1')
        current = c.fetchone()[0]
        if new_score > current:
            c.execute('UPDATE scores SET highscore=? WHERE id=1', (new_score,))
            conn.commit()
            return jsonify({'highscore': new_score, 'updated': True})
    return jsonify({'highscore': current, 'updated': False})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
