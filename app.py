from flask import Flask, render_template, request, jsonify, session, redirect
from flask_socketio import SocketIO, send
import json
import os

app = Flask(__name__)
app.secret_key = "secretkey123"
socketio = SocketIO(app, cors_allowed_origins="*")

USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# Ensure files exist
for file in [USERS_FILE, MESSAGES_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({} if file == USERS_FILE else [], f)

# Helpers
def load_users():
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def load_messages():
    with open(MESSAGES_FILE) as f:
        return json.load(f)

def save_messages(data):
    with open(MESSAGES_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html", user=session["user"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json
        users = load_users()

        username = data["username"]
        password = data["password"]

        if username in users:
            if users[username]["password"] != password:
                return {"error": "wrong password"}, 400
        else:
            users[username] = {
                "password": password,
                "avatar": data.get("avatar", "https://i.imgur.com/0y0y0y0.png")
            }
            save_users(users)

        session["user"] = username
        return {"success": True}

    return render_template("index.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@socketio.on("message")
def handle_message(msg):
    users = load_users()
    user = session.get("user", "anon")

    message_data = {
        "user": user,
        "avatar": users.get(user, {}).get("avatar", ""),
        "text": msg
    }

    messages = load_messages()
    messages.append(message_data)
    save_messages(messages)

    send(message_data, broadcast=True)

@app.route("/messages")
def get_messages():
    return jsonify(load_messages())

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)