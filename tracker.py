import requests
import openpyxl
import schedule
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import date

API_KEY = "DBC92EDA5338436CB8CD4645FF87F501"
import os
import json

# Load saved settings or run setup
def setup():
    if os.path.exists("settings.json"):
        with open("settings.json") as f:
            return json.load(f)
    
    print("👋 Welcome to Amazon Price Tracker!")
    print("Let's get you set up!\n")
    
    settings = {}
    settings["my_asin"] = input("Enter YOUR product ASIN: ")
    settings["my_price"] = float(input("Enter YOUR price: $"))
    settings["email_sender"] = input("Enter your Gmail address: ")
    settings["email_password"] = input("Enter your Gmail app password: ")
    settings["email_receiver"] = input("Enter email to send reports to: ")
    
    competitors = []
    num = int(input("How many competitors do you want to track? "))
    for i in range(num):
        name = input(f"Competitor {i+1} name: ")
        asin = input(f"Competitor {i+1} ASIN: ")
        competitors.append([name, asin])
    
    settings["competitors"] = competitors
    
    with open("settings.json", "w") as f:
        json.dump(settings, f)
    
    print("\n✅ Setup complete! Reports will run every morning at 8AM!")
    return settings

settings = setup()
my_asin = settings["my_asin"]
my_price = settings["my_price"]
competitors = settings["competitors"]
my_asin = "B0DB99PD1B"
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

def send_email():
    sender = "Dylanchomali23@gmail.com"
    receiver = "Dylanchomali24@gmail.com"
    password = "qizv vipj xssg fjyc"
    
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"Amazon Price Report - {date.today()}"
    
    msg.attach(MIMEText("Good morning! Your daily Amazon price report is attached.", "plain"))
    
    with open("price_report.xlsx", "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=price_report.xlsx")
        msg.attach(part)
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
    
    print("📧 Email sent successfully!")

def run_tracker():
    print("🔍 Running price tracker...")
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Price Report"
    # Set column widths
    ws.column_dimensions["A"].width = 15  # Date
    ws.column_dimensions["B"].width = 20  # Seller
    ws.column_dimensions["C"].width = 50  # Product name
    ws.column_dimensions["D"].width = 15  # Price
    ws.column_dimensions["E"].width = 15  # Difference
    ws.column_dimensions["F"].width = 25  # Status
    ws.append(["Date", "Seller", "Product", "Price", "Difference", "Status"])
    ws.append([str(date.today()), "ME", "My Product", my_price, "-", "-"])

    for name, asin in competitors:
        title, price = get_price(asin)
        difference = round(price - my_price, 2)
        status = "We are cheaper!" if my_price < price else "WARNING! They are cheaper!"
        ws.append([str(date.today()), name, title, price, difference, status])
        print(name, "- $", price)

    wb.save("price_report.xlsx")
    send_email()
    print("✅ Report saved and emailed!")

schedule.every().day.at("08:00").do(run_tracker)

print("⏰ Scheduler started! Report will run every day at 8:00 AM")
print("Running once now to test...")
run_tracker()

while True:
    schedule.run_pending()
    time.sleep(60)