import logging
from datetime import datetime
from app import client_soap

# Zmienna globalna do przechowywania danych województw - region_data = {}

def is_soap_client_logged_in():
    """Sprawdza, czy klient SOAP jest zalogowany."""
    try:
        test_response = client_soap.service.PobierzListeWojewodztw(DataStanu=datetime.now().strftime('%Y-%m-%d'))
        return bool(test_response)
    except Exception as error:
        logging.error(f"The SOAP client was not logged in correctly: {error}")
        return False


def get_provinces():
    try:
        data_stanu = datetime.now().strftime('%Y-%m-%d')
        result = client_soap.service.PobierzListeWojewodztw(DataStanu=data_stanu)
        return {woj.WOJ: woj.NAZWA for woj in result}
    except Exception as error:
        logging.error(f"Error while downloading the list of voivodeships from the Central Statistical Office API: {error}")
        return {}

