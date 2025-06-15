from flask import Flask, redirect, request, session, url_for
import requests
import os
import json
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecret")

CLIENT_ID = "Ov23liCsuI0ZYut356f6"
CLIENT_SECRET = "74d315cac217cc4de85c396329efe1c58c49e7a3"
REDIRECT_URI = "http://localhost:5000/callback"

@app.route("/")
def home():
    return '<a href="/login">Войти через GitHub</a>'

@app.route("/login")
def login():
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    )
    return redirect(github_auth_url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_url = "https://github.com/login/oauth/access_token"
    token_data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Accept": "application/json"}
    token_response = requests.post(token_url, data=token_data, headers=headers)
    token_json = token_response.json()
    access_token = token_json.get("access_token")

    if not access_token:
        return "Ошибка авторизации."

    session["access_token"] = access_token

    # Получаем данные пользователя
    user_url = "https://api.github.com/user"
    headers = {"Authorization": f"token {access_token}"}
    user_response = requests.get(user_url, headers=headers)
    user_data = user_response.json()
    login = user_data["login"]

    # Работа с users.json
    users_file = Path("storage/users.json")
    users = {}
    if users_file.exists():
        with users_file.open("r", encoding="utf-8") as f:
            users = json.load(f)

    if login not in users:
        users[login] = {
            "id": user_data["id"],
            "access_token": access_token,
            "role": "observer"
        }
    else:
        users[login]["access_token"] = access_token

    with users_file.open("w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

    # session.json
    session_file = Path("storage/session.json")
    with session_file.open("w", encoding="utf-8") as f:
        json.dump({
            "current_user": login,
            "role": users[login]["role"],
            "access_token": access_token
        }, f, indent=2, ensure_ascii=False)

    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    access_token = session.get("access_token")
    if not access_token:
        return redirect(url_for("login"))

    user_url = "https://api.github.com/user"
    headers = {"Authorization": f"token {access_token}"}
    user_response = requests.get(user_url, headers=headers)
    user_data = user_response.json()
    login = user_data["login"]

    # Загрузка users
    users_file = Path("storage/users.json")
    users = {}
    if users_file.exists():
        with users_file.open("r", encoding="utf-8") as f:
            users = json.load(f)

    role = users.get(login, {}).get("role", "неизвестно")

    return f"<h2>Привет, {login}!</h2><p>ID: {user_data['id']}</p><p>Роль: {role}</p>"

if __name__ == "__main__":
    app.run(debug=True)