from flask import Flask
app = Flask(__name__)
@app.route("/")
def index():
    return "PQ-TLS Demo App: Secure file transfer/chat coming soon!"
