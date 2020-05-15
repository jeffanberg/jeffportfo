from flask import Flask, render_template, request, redirect
from pathlib import Path
from functools import wraps
import csv, requests, json

app = Flask(__name__)


def check_recaptcha(f):
    """
    Checks Google reCAPTCHA.

    :param f: view function
    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.recaptcha_is_valid = None

        if request.method == 'POST':
            data = {
                'secret': '6LfTefcUAAAAAGixaKps3vPWtTEba6EV1_qrKIHW',
                'response': request.form.get('g-recaptcha-response'),
                'remoteip': request.access_route[0]
            }
            r = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=data
            )
            result = r.json()

            if result['success']:
                request.recaptcha_is_valid = True
            else:
                request.recaptcha_is_valid = False
                return('Please try again and confirm the Google ReCaptcha.', 'error')

        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/<string:page_name>.html')
def req_page(page_name):
    if Path('templates/' + page_name + '.html').exists():
        return render_template(page_name + '.html')
    else:
        return 'Page not found!'


def write_to_db(data):
    with open('contact_database.csv', mode='a', newline='') as c_db:
        email = data['email']
        name = data['name']
        message = data['message']
        csv_writer = csv.writer(c_db, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([email, name, message])
    return 'Entry made to database'


@app.route('/submit_form', methods=['POST', 'GET'])
@check_recaptcha
def submit_form():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            write_to_db(data)
            return redirect('/#thankyou')
        except:
            return 'Did not save to database.'
    else:
        return 'Something went wrong.'

