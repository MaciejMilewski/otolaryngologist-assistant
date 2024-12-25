import logging
from datetime import datetime
from app import client_soap


def is_soap_client_logged_in():
    """Sprawdza, czy klient SOAP jest zalogowany."""
    try:
        test_response = client_soap.service.PobierzListeWojewodztw(DataStanu=datetime.now().strftime('%Y-%m-%d'))
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
