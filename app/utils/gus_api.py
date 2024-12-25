import logging
from datetime import datetime
from app import client_soap


# Zmienna globalna do przechowywania danych województw
# dane_woj = {}


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


# def inicjalizuj_dane_wojewodztw():
#     """
#     Initializes the province data if it has not already been initialized.
#
#     :return: None
#     """
#     global dane_woj
#     if not dane_woj:  # Jeśli zmienna jest pusta, pobierz dane
#         dane_woj = get_wojewodztwa()
#         if dane_woj:
#             logging.info(f"Załadowano {len(dane_woj)} województw.")
#         else:
#             logging.warning("Nie udało się załadować województw.")
