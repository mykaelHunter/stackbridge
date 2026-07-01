from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, StackBridge!"

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/ready')
def ready():
    return jsonify({"status": "ready"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

@app.route('/ready')
def ready():
    return jsonify({"status": "ready"})
