from flask import Flask, session
import pytest
import app as m_app

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'abcd'
    app.config['TESTING'] = True

    app.route('/', methods=['GET', 'POST'])(m_app.login)
    app.route('/account/<username>', methods=['GET', 'POST'])(m_app.account)

    with app.test_client() as client:
        yield client


def test_login(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Login" in response.data

    response = client.post('/', data={'email': 'test@example.com', 'passwd': 'password'})
    assert response.status_code == 200
    assert b"Incorrect email or password!" in response.data

    response = client.post('/', data={'code': 'invalid_code'})
    assert response.status_code == 200
    assert b"Wrong verification code!" in response.data

    response = client.post('/', data={'email': 'braunsveigondrej@gmail.com', 'passwd': 'letadlo123'})
    assert response.status_code == 200
    assert b"Verification code has been sent to your email" in response.data

    code = session.get('code')
    response = client.post('/', data={'code': code})
    assert response.status_code == 302
    assert response.headers['Location'] == '/account/braunsveigondrej@gmail.com'

def test_account(client):
    response = client.get('/account/test@example.com')
    assert response.status_code == 200
    
    response = client.post('/account/test@example.com')
    assert response.status_code == 302
    assert response.headers['Location'] == '/'

def test_parse_rates():
    m_app.parse_rates()

def test_download_rates():
    m_app.download_rates()