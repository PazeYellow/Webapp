from flask import Flask, request, jsonify, session, redirect
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
    return page()

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
                "avatar": data.get("avatar") or "https://i.imgur.com/0y0y0y0.png"
            }
            save_users(users)

        session["user"] = username
        return {"success": True}

    return page()

@app.route("/messages")
def get_messages():
    return jsonify(load_messages())

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

def page():
    return """
<!DOCTYPE html>
<html>
<head>
<title>Chat</title>
<style>
body { font-family: Arial; background:#111; color:white; }
#messages { height:300px; overflow-y:scroll; border:1px solid #333; padding:10px; }
.msg { display:flex; gap:10px; margin:5px 0; align-items:center; }
input, button { margin:5px; padding:8px; }
</style>
</head>
<body>

<div id="loginBox">
<h2>Login</h2>
<input id="username" placeholder="username">
<input id="password" type="password" placeholder="password">
<input id="avatar" placeholder="avatar URL">
<button onclick="login()">Enter</button>
</div>

<div id="chatBox" style="display:none;">
<h2>Global Chat</h2>
<div id="messages"></div>

<input id="msg" placeholder="message">
<button onclick="sendMsg()">Send</button>
</div>

<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<script>
const socket = io();

function login(){
  fetch("/login", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({
      username: username.value,
      password: password.value,
      avatar: avatar.value
    })
  }).then(r=>r.json()).then(d=>{
    if(!d.error){
      loginBox.style.display="none";
      chatBox.style.display="block";
      loadMessages();
    }
  })
}

function sendMsg(){
  socket.send(msg.value);
  msg.value="";
}

socket.on("message",(data)=>{
  addMessage(data);
});

function addMessage(data){
  const div=document.createElement("div");
  div.className="msg";
  div.innerHTML = `
    <img src="${data.avatar}" width="30" height="30">
    <b>${data.user}:</b> ${data.text}
  `;
  messages.appendChild(div);
}

function loadMessages(){
  fetch("/messages").then(r=>r.json()).then(data=>{
    data.forEach(addMessage);
  });
}
</script>

</body>
</html>
"""

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
