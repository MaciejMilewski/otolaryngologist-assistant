import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import session, request, abort
from itsdangerous import URLSafeTimedSerializer

import pandas as pd
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from zeep import Client
from zeep.wsse.username import UsernameToken

from config import Config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
dane_woj = {}
parquet_data = {}

# get_streets_from_memory
# get_lista_ulic


# Inicjalizacja zmiennych środowiskowych
load_dotenv()

# Dane SOAP
WSDL_URL = os.getenv('WSDL_URL')
WSDL_USERNAME = os.getenv('WSDL_USERNAME')
WSDL_PASSWORD = os.getenv('WSDL_PASSWORD')

if None in (WSDL_URL, WSDL_USERNAME, WSDL_PASSWORD):
    logging.error("Jedna lub więcej zmiennych środowiskowych WSDL jest pusta.")
    print("Jedna lub więcej zmiennych środowiskowych WSDL jest pusta.")

if WSDL_URL and WSDL_USERNAME and WSDL_PASSWORD:
    token = UsernameToken(username=WSDL_USERNAME, password=WSDL_PASSWORD)
    client_soap = Client(wsdl=WSDL_URL, wsse=token)
else:
    client_soap = None
    logging.error("Nie udało się utworzyć klienta SOAP z powodu brakujących danych uwierzytelniających.")


def setup_logging(app):
    handler = RotatingFileHandler(
        'errors.log', maxBytes=3 * 1024 * 1024, backupCount=5
    )
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    app.logger.addHandler(handler)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    setup_logging(app)


    app.config['SQLALCHEMY_ECHO'] = True  # Włącz logowanie zapytań SQL
    # Konfiguracja ciasteczek sesji
    app.config.update(
      # SESSION_COOKIE_SECURE=True,    # Wymusza HTTPS dla ciasteczek
        SESSION_COOKIE_HTTPONLY=True,  # Blokuje dostęp do ciasteczek z JavaScript
        SESSION_COOKIE_SAMESITE='Lax'  # Zapobiega wysyłaniu ciasteczek w nieautoryzowanych żądaniach cross-site
    )

    try:
        test_response = client_soap.service.PobierzListeWojewodztw(DataStanu=datetime.now().strftime('%Y-%m-%d'))
        if not test_response:
            logging.error("Nie udało się zalogować klienta SOAP.")
        else:
            logging.info("Klient SOAP został poprawnie zalogowany.")
    except Exception as e:
        logging.error(f"Błąd podczas inicjalizacji klienta SOAP: {e}")

    global dane_woj
    if not dane_woj:
        data_stanu = datetime.now().strftime('%Y-%m-%d')
        result = client_soap.service.PobierzListeWojewodztw(DataStanu=data_stanu)
        dane_woj = {woj.WOJ: woj.NAZWA for woj in result}
        if dane_woj:
            logging.info(f"Załadowano dane województw: {len(dane_woj)} rekordów.")
        else:
            logging.warning("Nie udało się załadować danych województw.")

    global parquet_data
    parquet_data = load_parquet_files()

    @login_manager.user_loader
    def load_user(user_id):
        with app.app_context():
            from app.models import User
            return User.query.get(int(user_id))

        # Funkcje CSRF

    def verify_csrf_token():
        """Weryfikuje token CSRF dla żądań POST, PUT, PATCH, DELETE."""
        secret_key = app.config['SECRET_KEY']
        serializer = URLSafeTimedSerializer(secret_key)

        # Pobierz token z sesji i żądania
        session_token = session.get('csrf_token')
        request_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')

        # Sprawdzenie obecności tokenów
        if not session_token or not request_token:
            app.logger.error(f"Brak tokena CSRF. Sesja: {session_token}, Żądanie: {request_token}")
            abort(400, "Brak tokena CSRF lub żądanie jest nieważne")

        if not session_token or not request_token:
            abort(400, description="Brak tokena CSRF lub żądanie jest nieważne")

        try:
            decoded_token = serializer.loads(request_token, max_age=3600)  # 1-godzinna ważność tokena
        except Exception as e:
            abort(400, description="Nieprawidłowy lub przeterminowany token CSRF")

        if session_token != request_token:
            abort(400, description="Token CSRF jest nieprawidłowy")

    @app.before_request
    def verify_csrf():
        """Weryfikacja tokena CSRF dla żądań POST, PUT, PATCH, DELETE."""
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            verify_csrf_token()

    @app.context_processor
    def inject_csrf_token():
        """Dodanie tokena CSRF do kontekstu dla formularzy HTML."""
        return dict(csrf_token=generate_csrf_token())

    def generate_csrf_token():
        """Generuje unikalny token CSRF i zapisuje go do sesji."""
        secret_key = app.config['SECRET_KEY']
        serializer = URLSafeTimedSerializer(secret_key)
        # Generowanie tokena na podstawie unikalnego identyfikatora użytkownika (lub sesji)
        user_identifier = session.get('user_id', 'guest')
        token = serializer.dumps(user_identifier)
        session['csrf_token'] = token
        return token


    # TODO: dodaj blueprinty dla reszty routes
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

# Funkcja dostępna globalnie w pliku __init__.py
def verify_csrf_token():
    from flask import current_app as app  # Użyj kontekstu aplikacji
    token = session.get('csrf_token', None)
    request_token = request.form.get('csrf_token', None)
    if not token or not request_token:
        abort(400, "Brak tokena CSRF lub żądanie jest nieważne")

    secret_key = app.config['SECRET_KEY']
    serializer = URLSafeTimedSerializer(secret_key)
    try:
        serializer.loads(request_token, max_age=3600)
    except Exception:
        abort(400, "Nieprawidłowy lub przeterminowany token CSRF")

    if token != request_token:
        abort(400, "Token CSRF jest nieprawidłowy")
    return True  # Jeśli wszystko jest poprawne


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

    # Iterowanie po plikach w katalogu
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

    # Sprawdzenie, czy liczba wczytanych plików jest zgodna z oczekiwaną
    if loaded_file_count < expected_file_count:
        missing_files_count = expected_file_count - loaded_file_count
        logging.warning(f"Only {loaded_file_count} out of {expected_file_count} expected Parquet files were loaded. "
                        f"{missing_files_count} files are missing.")

    return data
