from flask import Flask, render_template, request, redirect, url_for
import requests

import datetime
import re
import random
import string
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
email = "braunsveigondrej@gmail.com"
passwd = "letadlo123"

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'email' in request.form.keys():
            if email == request.form['email'] and passwd == request.form['passwd']:
                code = ''.join(random.choice(string.ascii_letters) for i in range(8))
                with open('code.txt', 'w') as file:
                    file.write(code)
                send_mail(code)
                return render_template('index.html', message='Verification code has been sent to your email')
            else:
                return render_template('index.html', message='Incorrect email or password!')
        else:
            with open('code.txt', 'r') as file: 
                temp = file.readline()
            if temp == request.form['code']:
                return redirect(url_for('account', username=email))
            return render_template('index.html', message='Wrong verification code!')
    # Check if exchange rates in database are current and if not, download current ones and parse them into json
    if are_rates_outdated():
        download_rates()
        parse_rates()
    # Remove verification code validity on webserver start
    with open('code.txt', 'w') as file:
        file.write("")
    return render_template('index.html')

@app.route('/account/<username>', methods=['GET', 'POST'])
def account(username):
    if request.method == 'POST':
        return redirect(url_for('login'))
    return render_template('account.html', jmeno=username)

def send_mail(code):
    # Set up the email parameters
    password = "kcawyfghdwfamlxy"
    subject = "Verification code"

    # Create a multipart message and set headers
    msg = MIMEMultipart()
    msg["From"] = email
    msg["To"] = email
    msg["Subject"] = subject

    # Add body to the email
    msg.attach(MIMEText(code, "plain"))

    # Create SMTP session
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls() # Secure the connection
        server.login(email, password) # Login with email and password
        text = msg.as_string()
        server.sendmail(email, email, text)

def are_rates_outdated():
    with open('data/exchange_rates.json', 'r') as file:
        dictionary = json.load(file)
    today = datetime.datetime.now()
    if dictionary['month'] == today.month and dictionary['year'] == today.year:
        dic_total_min = dictionary['hour']*60+dictionary['minute']
        today_total_min = today.hour*60+today.minute
        if today.day-dictionary['day'] == 0:
            if (dic_total_min-(14*60+30))*(today_total_min-(14*60+30)) > 0:
                return False
        if today.day-dictionary['day'] == 1:
            if (dic_total_min-(14*60+30))*(today_total_min-(14*60+30)) < 0:
                return False
    return True


def parse_rates():
    with open('data/denni_kurz.txt', 'r') as file:
        file.readline()
        file.readline()
        lines = file.readlines()
    today = datetime.datetime.now()
    dictionary = {
        "minute": today.minute,
        "hour": today.hour,
        "day": today.day,
        "month": today.month,
        "year": today.year
    }
    for line in lines:
        line = line.replace(',', '.')
        line = line.strip()
        split_line = line.split('|')
        dictionary[split_line[3]] = float(split_line[4])/float(split_line[2])
    with open('data/exchange_rates.json', 'w') as file:
        json.dump(dictionary, file)

def download_rates():
    url = 'https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt'
    req = requests.get(url, allow_redirects=True)
    open('data/denni_kurz.txt', 'wb').write(req.content)

if __name__ == '__main__':
    app.run(debug=True)

