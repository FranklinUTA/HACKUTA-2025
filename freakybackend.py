from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# Use a fixed database path so it doesn't reset when switching directories
DB_PATH = os.path.join(os.path.expanduser("~"), "freakyhighscore.db")

# Initialize database and table if they don't exist
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY,
                        highscore INTEGER
                    )''')
        # Only insert the initial row once
        c.execute('INSERT OR IGNORE INTO scores (id, highscore) VALUES (1, 0)')
        conn.commit()

# Route: Get the current highscore
@app.route('/get_highscore', methods=['GET'])
def get_highscore():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT highscore FROM scores WHERE id=1')
            score = c.fetchone()[0]
        return jsonify({'highscore': score})
    except Exception as e:
        print("Error getting highscore:", e)
        return jsonify({'error': str(e)}), 500

# Route: Set (update) the highscore
@app.route('/set_highscore', methods=['POST'])
def set_highscore():
    try:
        new_score = int(request.json.get('score', 0))
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute('SELECT highscore FROM scores WHERE id=1')
            current = c.fetchone()[0]

            if new_score > current:
                c.execute('UPDATE scores SET highscore=? WHERE id=1', (new_score,))
                conn.commit()
                print(f"Highscore updated to {new_score}")
                return jsonify({'highscore': new_score, 'updated': True})
            else:
                print(f"Score {new_score} not higher than {current}")
                return jsonify({'highscore': current, 'updated': False})
    except Exception as e:
        print("Error setting highscore:", e)
        return jsonify({'error': str(e)}), 500

# Run the backend
if __name__ == '__main__':
    init_db()
    print("Freaky Bird backend running")
    print(f"Database file: {DB_PATH}")
    print("Open http://127.0.0.1:5000/get_highscore to test.")
    app.run(debug=True)
