from flask import Flask, render_template, request, redirect
from flask_google_recaptcha import GoogleReCaptcha
from pathlib import Path
import csv

app = Flask(__name__)

app.config.update({'RECAPTCHA_ENABLED': True,
                   'RECAPTCHA_SITE_KEY':
                       '6LfTefcUAAAAAMsBLYsUbQ-E8FYoFSULI9G5Z0FU',
                   'RECAPTCHA_SECRET_KEY':
                       '6LfTefcUAAAAAGixaKps3vPWtTEba6EV1_qrKIHW',
                    'RECAPTCHA_THEME':
                        'dark'})

recaptcha = GoogleReCaptcha(app=app)

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
def submit_form():
    if request.method == 'POST':
        if recaptcha.verify():
            try:
                data = request.form.to_dict()
                write_to_db(data)
                return redirect('/#thankyou')
            except:
                return 'Did not save to database.'
        else:
            return 'Probably a robot.'
    else:
        return 'Something went wrong'
