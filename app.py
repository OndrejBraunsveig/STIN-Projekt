from flask import Flask, render_template, request, redirect, url_for, session
import requests

import datetime
import random
import string
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcd'
sender_email = "braunsveigondrej@gmail.com"

@app.route('/', methods=['GET', 'POST'])
def login():
    with open('data/accounts.json', 'r') as file:
        accounts = json.load(file)
    if request.method == 'POST':
        # Send code form
        if 'email' in request.form.keys():
            for account in accounts:
                if request.form['email'] == account['email'] and request.form['passwd'] == account['passwd']:
                    code = ''.join(random.choice(string.ascii_letters) for i in range(8))
                    session['current_acc'] = account
                    send_mail(code)
                    session['code'] = code
                    return render_template('index.html', message='Verification code has been sent to your email')
            return render_template('index.html', message='Incorrect email or password!')
        # Login form
        if request.form['code'] == session.get('code'):
            return redirect(url_for('account', number=session.get('current_acc')['account_number']))
        return render_template('index.html', message='Wrong verification code!')
    # Remove verification code validity on webserver start
    session['code'] = ""
    return render_template('index.html')

@app.route('/account/<number>', methods=['GET', 'POST'])
def account(number):
    with open('data/accounts.json', 'r') as file:
        accounts = json.load(file)
    for loaded_account in accounts:
        if loaded_account['account_number'] == int(number):
            account = loaded_account
    if request.method == 'POST':
        # Deposit form
        if 'dep_amount' in request.form.keys():
            # Check if exchange rates in database are current and if not, download current ones and parse them into json
            if are_rates_outdated():
                download_rates()
                parse_rates()
            amount = int(request.form['dep_amount'])
            if amount >= 0:
                account = deposit(amount, request.form['currency'], int(number))
        # Send payment form
        elif 'send_amount' in request.form.keys():
            # Check if exchange rates in database are current and if not, download current ones and parse them into json
            if are_rates_outdated():
                download_rates()
                parse_rates()
            amount = int(request.form['send_amount'])
            if amount >= 0:
                account = send_payment(amount, request.form['currency'], int(number), int(request.form['receiver']))
        else:
            return redirect(url_for('login'))
    history = list(account['history'].values())
    history.reverse()
    sliced_history = history[:10]
    return render_template('account.html', jmeno=number, balances=list(account['balances'].items()),
                            transaction_history=sliced_history
                            )

def send_mail(code):
    # Set up the email parameters
    password = "kcawyfghdwfamlxy"
    subject = "Verification code"

    # Create a multipart message and set headers
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = session.get('current_acc')['email']
    msg["Subject"] = subject

    # Add body to the email
    msg.attach(MIMEText(code, "plain"))

    # Create SMTP session
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls() # Secure the connection
        server.login(sender_email, password) # Login with email and password
        text = msg.as_string()
        server.sendmail(sender_email, session.get('current_acc')['email'], text)

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
        "year": today.year,
        "CZK": 1
    }
    for line in lines:
        line = line.replace(',', '.')
        line = line.strip()
        split_line = line.split('|')
        dictionary[split_line[3]] = float(split_line[4])/float(split_line[2])
    with open('data/exchange_rates.json', 'w') as file:
        file.write(json.dumps(dictionary, indent=4))

def download_rates():
    url = 'https://www.cnb.cz/cs/financni-trhy/devizovy-trh/kurzy-devizoveho-trhu/kurzy-devizoveho-trhu/denni_kurz.txt'
    req = requests.get(url, allow_redirects=True)
    open('data/denni_kurz.txt', 'wb').write(req.content)

def deposit(amount, currency, to):
    with open('data/accounts.json', 'r') as file:
        accounts = json.load(file)
    with open('data/exchange_rates.json', 'r') as file:
        rates = json.load(file)
    today = datetime.datetime.today()
    time = f"{today.day}.{today.month}.{today.year} {today.hour}:{today.minute}:{today.second}"
    for account in accounts:
        if account['account_number'] == to:
            if currency in rates.keys():
                if currency in account['balances'].keys():
                    account['balances'][currency] = account['balances'][currency]+amount
                else:
                    account['balances'][currency] = amount
                account['history'][time] = f"+{amount} {currency}"
                with open('data/accounts.json', 'w') as file:
                    file.write(json.dumps(accounts, indent=4))
            return account
        
def send_payment(amount, currency, by, to):
    # Load data from json files
    with open('data/accounts.json', 'r') as file:
        accounts = json.load(file)
    with open('data/exchange_rates.json', 'r') as file:
        rates = json.load(file)
    today = datetime.datetime.today()
    time = f"{today.day}.{today.month}.{today.year} {today.hour}:{today.minute}:{today.second}"
    # Find account in database and do action based on bilances present on the account
    for account in accounts:
        if account['account_number'] == by:
            if currency in rates.keys():
                if currency in account['balances'].keys():
                    if account['balances'][currency]*1.1 > amount:
                        minus = amount
                        if amount > account['balances'][currency]:
                            amount = (account['balances'][currency]-amount)*1.1
                            minus = account['balances'][currency]-amount
                        account['balances'][currency] = account['balances'][currency]-minus
                        account['history'][time] = f"{to}: -{minus:.2f} {currency}"
                        with open('data/accounts.json', 'w') as file:
                            file.write(json.dumps(accounts, indent=4))
                        return account
                in_czk = amount*rates[currency]
                if account['balances']['CZK']*1.1 > in_czk:
                    minus = in_czk
                    if in_czk > account['balances']['CZK']:
                        in_czk = (account['balances']['CZK']-in_czk)*1.1
                        minus = account['balances']['CZK']-in_czk
                    account['balances']['CZK'] = account['balances']['CZK']-minus
                    account['history'][time] = f"{to}: -{minus:.2f} CZK"
                    with open('data/accounts.json', 'w') as file:
                        file.write(json.dumps(accounts, indent=4))
            return account
                
if __name__ == '__main__':
    app.run(debug=True)

