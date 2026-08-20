from flask import Flask
import os
import socket

app = Flask(__name__)


@app.route("/")
def home():
    hostname = socket.gethostname()
    environment = os.getenv("APP_ENV", "development")

    return f"""
    <html>
        <head>
            <title>DevOps Containerized Web App</title>
        </head>
        <body>
            <h1>DevOps Containerized Web Application</h1>
            <p>Application is running inside Docker.</p>
            <p>Environment: {environment}</p>
            <p>Container hostname: {hostname}</p>
        </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
