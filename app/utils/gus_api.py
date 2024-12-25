import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from zeep import Client
from zeep.wsse.username import UsernameToken

load_dotenv()

WSDL_URL = os.getenv('WSDL_URL')
WSDL_USERNAME = os.getenv('WSDL_USERNAME')
WSDL_PASSWORD = os.getenv('WSDL_PASSWORD')

if None in (WSDL_URL, WSDL_USERNAME, WSDL_PASSWORD):
    logging.error("Jedna lub więcej zmiennych środowiskowych WSDL jest pusta.")

token = UsernameToken(username=WSDL_USERNAME, password=WSDL_PASSWORD)
client_soap = Client(wsdl=WSDL_URL, wsse=token)


def is_soap_client_logged_in(client):
    """Sprawdza, czy klient SOAP jest zalogowany."""
    try:
        test_response = client.service.PobierzListeWojewodztw(DataStanu=datetime.now().strftime('%Y-%m-%d'))
        return bool(test_response)
    except Exception as error:
        logging.error(f"Klient SOAP nie został poprawnie zalogowany: {error}")
        return False


def get_wojewodztwa():
    try:
        data_stanu = datetime.now().strftime('%Y-%m-%d')
        result = client_soap.service.PobierzListeWojewodztw(DataStanu=data_stanu)
        return {woj.WOJ: woj.NAZWA for woj in result}
    except Exception as error:
        logging.error(f"Błąd podczas pobierania listy województw z API GUS: {error}")
        return {}


# Sprawdź logowanie SOAP
if not is_soap_client_logged_in(client_soap):
    logging.error("Nie udało się zalogować klienta SOAP.")
else:
    logging.info("Klient SOAP został poprawnie zalogowany.")
