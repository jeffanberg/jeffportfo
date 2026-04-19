from flask import Flask, render_template, request, make_response, jsonify
from pathlib import Path
from functools import wraps
import csv, requests, json, html, os, re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")

EMAIL_REGEX = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://www.google.com/recaptcha/ https://www.gstatic.com/; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "frame-src https://www.google.com/recaptcha/ https://recaptcha.google.com; "
        "connect-src 'self';"
    )
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

def check_recaptcha(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.recaptcha_is_valid = None

        if request.method == 'POST':
            recaptcha_response = (request.json or {}).get('g-recaptcha-response') if request.is_json else request.form.get('g-recaptcha-response')

            api_key = os.environ.get('RECAPTCHA_API_KEY', '')
            if not api_key:
                print("WARNING: RECAPTCHA_API_KEY environment variable is missing.")

            data = {
                "event": {
                    "token": recaptcha_response,
                    "expectedAction": "contact_form_submit",
                    "siteKey": "6Lf6M5wsAAAAAGlDdkkzhT2eQpWZLkPXLwLgnrxN"
                }
            }
            try:
                r = requests.post(
                    f"https://recaptchaenterprise.googleapis.com/v1/projects/recaptcha-migrated-72bf259d309/assessments?key={api_key}",
                    json=data
                )
                result = r.json()
                print(f"reCAPTCHA Enterprise API response: {json.dumps(result, indent=2)}")
            except Exception as e:
                print(f"reCAPTCHA Enterprise API request failed: {e}")
                result = {}

            token_props = result.get('tokenProperties', {})
            is_valid = token_props.get('valid', False)
            action = token_props.get('action', '')
            score = result.get('riskAnalysis', {}).get('score', 0.0)

            if is_valid and score >= 0.5 and action == 'contact_form_submit':
                request.recaptcha_is_valid = True
            else:
                request.recaptcha_is_valid = False
                print(f"reCAPTCHA Enterprise failed. Valid: {is_valid}, Score: {score}, Action: {action}")
                return jsonify({'status': 'error', 'message': 'Automated submission detected. Please try again later.'}), 400

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
        return 'Page not found!', 404

def sanitize_csv_field(text):
    if not text:
        return ''
    text = str(text).replace('\n', ' ').replace('\r', '')[:2000]
    if text and text[0] in ['=', '+', '-', '@']:
        text = "'" + text
    return text

def write_to_db(data):
    with open('contact_database.csv', mode='a', newline='', encoding='utf-8') as c_db:
        email = sanitize_csv_field(data.get('email', ''))
        name = sanitize_csv_field(data.get('name', ''))
        message = sanitize_csv_field(data.get('message', ''))
        csv_writer = csv.writer(c_db, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow([email, name, message])
    return True

@app.route('/submit_form', methods=['POST'])
@check_recaptcha
@limiter.limit("5 per minute")
def submit_form():
    try:
        data = request.json if request.is_json else request.form.to_dict()

        if len(data.get('name', '')) > 200 or len(data.get('email', '')) > 200:
            return jsonify({'status': 'error', 'message': 'Name or email is too long.'}), 400

        if not EMAIL_REGEX.match(data.get('email', '')):
            return jsonify({'status': 'error', 'message': 'Invalid email address.'}), 400

        write_to_db(data)
        return jsonify({'status': 'success', 'message': 'Entry made to database'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Did not save to database.'}), 500
