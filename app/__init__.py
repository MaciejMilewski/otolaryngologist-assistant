import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, session, request, abort
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from zeep import Client
from zeep.wsse.username import UsernameToken

import app
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
region_data = {}
parquet_data = {}

# Inicjalizacja zmiennych środowiskowych
load_dotenv()

# Dane SOAP
WSDL_URL = os.getenv('WSDL_URL')
WSDL_USERNAME = os.getenv('WSDL_USERNAME')
WSDL_PASSWORD = os.getenv('WSDL_PASSWORD')

if None in (WSDL_URL, WSDL_USERNAME, WSDL_PASSWORD):
    logging.error("One or more WSDL environment variables are empty.")

if WSDL_URL and WSDL_USERNAME and WSDL_PASSWORD:
    token = UsernameToken(username=WSDL_USERNAME, password=WSDL_PASSWORD)
    client_soap = Client(wsdl=WSDL_URL, wsse=token)
else:
    client_soap = None
    logging.error("Failed to create SOAP client due to missing credentials.")


def setup_logging(app):
    # Rotacje do 5 plików po 3 MB wielkości
    handler = RotatingFileHandler(
        'errors.log', maxBytes=3 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    app.logger.addHandler(handler)
    # konfiguracja globalnego loggera
    logging.basicConfig(
        level=logging.WARNING,  # Globalny poziom logów
        handlers=[handler]  # Ten sam handler lokalny dla loggera aplikacji
    )


def generate_csrf_token():
    """Generuje unikalny token CSRF i zapisuje go do sesji."""
    secret_key = Config.SECRET_KEY
    serializer = URLSafeTimedSerializer(secret_key)
    # Generowanie tokena na podstawie unikalnego identyfikatora użytkownika (lub sesji)
    user_identifier = session.get('user_id', 'guest')
    token = serializer.dumps(user_identifier)
    session['csrf_token'] = token
    return token


def verify_csrf_token():
    """Weryfikuje token CSRF dla żądań POST, PUT, PATCH, DELETE."""
    # Pobranie klucza sekretnego
    secret_key = Config.SECRET_KEY
    if not secret_key:
        logging.error("SECRET_KEY is not configured.")
        abort(500, "Internal Server Error")

    serializer = URLSafeTimedSerializer(secret_key)

    # Pobranie tokenu z sesji i żądania
    session_token = session.get('csrf_token')
    request_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')

    # Sprawdzenie, czy tokeny są obecne
    if not session_token or not request_token:
        logging.warning("Missing CSRF token.")
        abort(400, description="Invalid or missing CSRF token.")

    try:
        # Dekodowanie tokena z żądania i sesji przy użyciu serializera
        decoded_request_token = serializer.loads(request_token, max_age=3600)  # ważność: 1 godzina
        decoded_session_token = serializer.loads(session_token, max_age=3600)

        # Sprawdzenie, czy token z sesji i żądania są zgodne
        if decoded_request_token != decoded_session_token:
            logging.warning("CSRF token mismatch.")
            abort(400, description="Invalid CSRF token.")
    except SignatureExpired:
        logging.warning("The CSRF token has expired.")
        abort(400, description="Invalid or expired CSRF token.")
    except BadSignature:
        logging.warning("The CSRF token is invalid or tampered.")
        abort(400, description="Invalid CSRF token.")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    #setup_logging(app)

    app.config['SQLALCHEMY_ECHO'] = True  # Włącz logowanie zapytań SQL
    app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken']

    # Konfiguracja ciasteczek sesji
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,  # Blokuje dostęp do ciasteczek z JavaScript
        SESSION_COOKIE_SAMESITE='Lax'  # Zapobiega wysyłaniu ciasteczek w nieautoryzowanych żądaniach cross-site
    )

    try:
        test_response = client_soap.service.PobierzListeWojewodztw(DataStanu=datetime.now().strftime('%Y-%m-%d'))
        if not test_response:
            logging.error("Failed to authenticate SOAP client.")
        else:
            logging.info("SOAP client has been successfully authenticated.")
    except Exception as e:
        logging.error(f"Error initializing SOAP client. {e}")

    global region_data
    if not region_data:
        data_stanu = datetime.now().strftime('%Y-%m-%d')
        result = client_soap.service.PobierzListeWojewodztw(DataStanu=data_stanu)
        region_data = {woj.WOJ: woj.NAZWA for woj in result}
        if region_data:
            logging.info(f"Load Voivodeships data: {len(region_data)} records.")
        else:
            logging.warning("Failed to load Voivodeships data.")

    global parquet_data
    parquet_data = load_parquet_files()

    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            from app.models import User
            return User.query.get(int(user_id))

    @app.before_request
    def verify_csrf():
        """Weryfikacja tokena CSRF dla żądań POST, PUT, PATCH, DELETE."""
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            verify_csrf_token()
            logging.info(f"CSRF token verified for {request.method} request.")

    @app.context_processor
    def inject_csrf_token():
        """Dodanie tokena CSRF do kontekstu dla formularzy HTML."""
        return dict(csrf_token=generate_csrf_token())

    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.start import start_bp
    app.register_blueprint(start_bp)

    from app.routes.visit import visit_bp
    app.register_blueprint(visit_bp)

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)

    from app.routes.medical_certificate import medical_certificate_bp
    app.register_blueprint(medical_certificate_bp)

    from app.routes.antibiotic import antibiotic_bp
    app.register_blueprint(antibiotic_bp)

    from app.routes.patient import patient_bp
    app.register_blueprint(patient_bp)

    from app.routes.instruction import instruction_bp
    app.register_blueprint(instruction_bp)

    from app.routes.procedure import procedure_bp
    app.register_blueprint(procedure_bp)

    from app.routes.schedule import schedule_bp
    app.register_blueprint(schedule_bp)

    return app


def load_parquet_files(directory='app/static/parquet', expected_file_count=16):
    """
    :param directory: The directory to search for Parquet files.
    :type directory: str
    :param expected_file_count: The expected number of Parquet files to be loaded.
    :type expected_file_count: int
    :return: A dictionary where keys are region names derived from file names, and values are the loaded Parquet files as DataFrames.
    :rtype: dict
    """
    data = {}
    loaded_file_count = 0

    for filename in os.listdir(directory):
        if filename.endswith('.parquet'):
            try:
                file_path = os.path.join(directory, filename)
                region_name = filename.split('.')[0]
                data[region_name] = pd.read_parquet(file_path)
                loaded_file_count += 1
            except FileNotFoundError as error_filename:
                logging.error(f"File {filename} not found. Error: {error_filename}")
            except Exception as error_os:
                logging.error(f"Error loading file {filename}: {error_os}")

    # Checking if the number of loaded files matches the expected count
    if loaded_file_count < expected_file_count:
        missing_files_count = expected_file_count - loaded_file_count
        logging.warning(f"Only {loaded_file_count} out of {expected_file_count} expected Parquet files were loaded. "
                        f"{missing_files_count} files are missing.")

    return data
