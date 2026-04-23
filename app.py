from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import json
from datetime import date

app = Flask(__name__)
app.secret_key = "amazontrackerkey123"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)

API_KEY = "DBC92EDA5338436CB8CD4645FF87F501"

# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    my_asin = db.Column(db.String(50), default="")
    my_price = db.Column(db.Float, default=0.0)
    competitors = db.Column(db.Text, default="[]")
    cached_results = db.Column(db.Text, default="[]")
    last_updated = db.Column(db.String(50), default="")

with app.app_context():
    db.create_all()

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
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    today = str(date.today())

    # Only fetch new prices if not already fetched today
    if user.last_updated != today:
        competitors = json.loads(user.competitors)
        results = []
        results.append(("ME", "My Product", user.my_price, "-", "-"))
        for comp in competitors:
            title, price = get_price(comp["asin"])
            difference = round(price - user.my_price, 2)
            status = "We are cheaper!" if user.my_price < price else "WARNING! They are cheaper!"
            results.append((comp["name"], title, price, difference, status))
        user.cached_results = json.dumps(results)
        user.last_updated = today
        db.session.commit()
    else:
        results = json.loads(user.cached_results)

    return render_template("dashboard.html", results=results, user=user, date=today)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists!")
            return redirect(url_for("signup"))
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        session["user_id"] = new_user.id
        return redirect(url_for("settings"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("home"))
        flash("Invalid email or password!")
    return render_template("login.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    if request.method == "POST":
        user.my_asin = request.form["my_asin"]
        user.my_price = float(request.form["my_price"])
        competitors = []
        names = request.form.getlist("comp_name")
        asins = request.form.getlist("comp_asin")
        for name, asin in zip(names, asins):
            if name and asin:
                competitors.append({"name": name, "asin": asin})
        user.competitors = json.dumps(competitors)
        db.session.commit()
        return redirect(url_for("home"))
    competitors = json.loads(user.competitors)
    return render_template("settings.html", user=user, competitors=competitors)

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)