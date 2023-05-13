from flask import Flask, render_template, request, redirect, url_for
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

def parse_rates():
    with open('data/denni_kurz.txt', 'r') as file:
        file.readline()
        file.readline()
        lines = file.readlines()
    today = datetime.datetime.now()
    dictionary = {
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



def check_rates():
    with open('data/denni_kurz.txt', 'r') as file:
        line = file.readline()
    date = list(map(int, re.split(r'[. ]', line)[:3]))
    today = datetime.datetime.now()


if __name__ == '__main__':
    app.run(debug=True)

