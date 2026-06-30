from flask import Flask

app = Flask(__name__)


@app.get("/")
def health():
    return {
        "service": "{{SERVICE_NAME}}",
        "status": "running"
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port={{PORT}}
    )
