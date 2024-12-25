import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

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
