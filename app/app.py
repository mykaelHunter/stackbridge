"""
StackBridge Internal Orders API
"""
import os
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = 5432
DB_NAME = "stackbridge"
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASS = os.environ.get("DB_PASS", "admin1234")

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/orders", methods=["GET"])
def list_orders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (customer_id, product, quantity, status) VALUES (%s, %s, %s, 'pending') RETURNING id",
        (data["customer_id"], data["product"], data["quantity"])
    )
    order_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": order_id}, 201

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify(row)
    return {"error": "not found"}, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
