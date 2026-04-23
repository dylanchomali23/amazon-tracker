from flask import Flask, render_template, redirect, url_for, request, session
import requests
import json

app = Flask(__name__)
app.secret_key = "amazontrackerkey123"

API_KEY = "DBC92EDA5338436CB8CD4645FF87F501"

my_price = 29.99

competitors = [
    ("ProMix Nutrition", "B0C1M4TRTF"),
    ("Zeal Naturals", "B07XVCD1MY"),
]

def get_price(asin):
    url = "https://api.rainforestapi.com/request"
    params = {
        "api_key": API_KEY,
        "type": "product",
        "asin": asin,
        "amazon_domain": "amazon.com"
    }
    response = requests.get(url, params=params)
    data = response.json()
    try:
        price = data["product"]["buybox_winner"]["price"]["value"]
        title = data["product"]["title"]
        return title, price
    except:
        return "Not found", 0

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    
    results = []
    results.append(("ME", "My Product", my_price, "-", "-"))
    
    for name, asin in competitors:
        title, price = get_price(asin)
        difference = round(price - my_price, 2)
        if my_price < price:
            status = "We are cheaper!"
        else:
            status = "WARNING! They are cheaper!"
        results.append((name, title, price, difference, status))
    
    return render_template("dashboard.html", results=results)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if email == "admin@gmail.com" and password == "admin123":
            session["user"] = email
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid email or password!")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
import os
port = int(os.environ.get("PORT", 5000))
app.run(host="0.0.0.0", port=port)
