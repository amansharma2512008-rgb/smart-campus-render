import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- PASTE YOUR NEW NEON DATABASE LINK HERE ---
NEON_URL = "postgresql://neondb_owner:npg_XHS5oqa7jGiv@ep-muddy-wave-amdry2e1-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_db_connection():
    return psycopg2.connect(NEON_URL)

# This automatically builds the fresh database table the first time it runs
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                id SERIAL PRIMARY KEY,
                sensor_id TEXT NOT NULL,
                temp REAL NOT NULL,
                hum REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")

init_db()

# The POST route: Receives data from your ESP32
@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    data = request.get_json()
    if not data:
         return jsonify({"error": "No JSON provided"}), 400
         
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO telemetry (sensor_id, temp, hum) VALUES (%s, %s, %s)",
            (data.get('sensor_id', 'ESP32'), data.get('temp'), data.get('hum'))
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Data saved to Neon!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# The GET route: Sends data to your Streamlit dashboard
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
