from flask import Flask, render_template, request, make_response, jsonify
from pathlib import Path
from functools import wraps
import csv, requests, json, html, os

app = Flask(__name__)
# Limit incoming request payload to 1MB to prevent memory exhaustion DoS attacks
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

def check_recaptcha(f):
    """
    Checks Google reCAPTCHA.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.recaptcha_is_valid = None

        if request.method == 'POST':
            # For JSON endpoints and Form endpoints
            recaptcha_response = request.form.get('g-recaptcha-response') or request.json.get('g-recaptcha-response') if request.is_json else request.form.get('g-recaptcha-response')
            
            secret = os.environ.get('RECAPTCHA_SECRET_KEY', '')
            if not secret:
                print("WARNING: RECAPTCHA_SECRET_KEY environment variable is missing.")

            data = {
                'secret': secret,
                'response': recaptcha_response,
                'remoteip': request.access_route[0]
            }
            try:
                r = requests.post(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data=data
                )
                result = r.json()
            except:
                result = {'success': False}

            if result.get('success'):
                request.recaptcha_is_valid = True
            else:
                request.recaptcha_is_valid = False
                return jsonify({'status': 'error', 'message': 'Please confirm the Google ReCaptcha.'}), 400

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
    # Replace newlines and limit length
    text = str(text).replace('\n', ' ').replace('\r', '')[:2000]
    # Prevent CSV Injection
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
def submit_form():
    try:
        data = request.json if request.is_json else request.form.to_dict()
        
        # Validation
        if len(data.get('name', '')) > 200 or len(data.get('email', '')) > 200:
            return jsonify({'status': 'error', 'message': 'Name or email is too long.'}), 400
            
        write_to_db(data)
        return jsonify({'status': 'success', 'message': 'Entry made to database'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'Did not save to database.'}), 500

