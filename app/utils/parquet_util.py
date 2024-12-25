# Funkcja pobierająca nazwę miejscowości danego województwa z zapisanych danych
# Parametr : 'wojewodztwo', string pełna nazwa województwa złożona z dużych liter
# Parametr : 'city_looking_for', string pełna nazwa miejscowości
import logging
from datetime import datetime

from app import parquet_data, client_soap, dane_woj


def get_streets_from_memory(wojewodztwo, city_looking_for):
    """
    :param wojewodztwo: The regional division to search within.
    :param city_looking_for: The name of the city to find streets for.
    :return: A list of streets found within the specified city and region.
    """
    result = []

    # Pobierz informacje z szukanego województwa
    df = parquet_data[wojewodztwo]

    # Wyszukaj miejscowość
    looking_for_row = df.loc[df['Nazwa'] == city_looking_for]

    # Uzyskaj kod województwa na podstawie długiej nazwy województwa
    kod_wojewodztwa = get_key_by_value(dane_woj, wojewodztwo)

    if not looking_for_row.empty:
        for _, row in looking_for_row.iterrows():
            try:
                powiat = row['Powiat']
                gmina = row['Gmina']
                rodzaj_gminy = row['RodzajGminy']
                symbol_miejscowosci = row['SymbolMiejscowosci']
                ulice = get_lista_ulic(kod_wojewodztwa, powiat, gmina, rodzaj_gminy, symbol_miejscowosci)
                result.extend(ulice)
            except Exception as error_city_looking_for:
                logging.info(f"Błąd pobierania ulic dla {city_looking_for}: {error_city_looking_for}")
    else:
        logging.error(f"Miejscowość '{city_looking_for}' nie została znaleziona w województwie {wojewodztwo}.")
    return result


def get_lista_ulic(wojewodztwa_kod, powiat, gmina, rodzaj_gminy, symbol_miejscowosci):
    """
    :param wojewodztwa_kod: Dwuznakowy symbol województwa
    :param powiat: Dwuznakowy symbol powiatu
    :param gmina: Dwuznakowy symbol gminy
    :param rodzaj_gminy: Jednoznakowy symbol rodzaju gminy
    :param symbol_miejscowosci: Siedmioznakowy identyfikator miejscowości
    :return: Lista pełnych nazw ulic dla danej miejscowości
    """
    # Funkcja pobierająca listę ulic dla danej miejscowości za pomocą API GUS
    # NAZWA FUNKCJI 'PobierzListeUlicDlaMiejscowosci'
    # PARAMETR 'Woj' typu string, dwuznakowy symbol województwa,
    # PARAMETR 'Pow' typu string, dwuznakowy symbol powiatu,
    # PARAMETR 'Gmi' typu string, dwuznakowy symbol gminy,
    # PARAMETR 'Rodz' typu string, jednoznakowy symbol rodzaju gminy,
    # PARAMETR 'msc' typu string, 7-znakowy identyfikator miejscowości,
    # PARAMETR 'czyWersjaUrzedowa' typu bool, domyślnie FALSE
    # PARAMETR 'czyWersjaAdresowa' typu bool, domyślnie TRUE
    # PARAMETR 'DataStanu' ,data w formacie ‘YYYY-MM-DD’

    ulice = []
    state_date = datetime.now().strftime('%Y-%m-%d')

    result = client_soap.service.PobierzListeUlicDlaMiejscowosci(
        wojewodztwa_kod,
        powiat,
        gmina,
        rodzaj_gminy,
        symbol_miejscowosci,
        False,  # czyWersjaUrzedowa
        True,  # czyWersjaAdresowa
        state_date
    )

    if result:
        for street in result:
            nazwa1 = street['Nazwa1']
            nazwa2 = street['Nazwa2'] if street['Nazwa2'] else ''
            pelna_nazwa_ulicy = f"{nazwa1} {nazwa2}".strip()
            ulice.append(pelna_nazwa_ulicy)
    else:
        logging.info(f"Brak ulic dla miejscowości o symbolu {symbol_miejscowosci}.")
    return ulice


def get_key_by_value(d, value):
    """
    :param d: Dictionary to search the key from
    :param value: Value to search for in the dictionary
    :return: The key associated with the specified value in the dictionary, or None if the value is not found
    """
    for key, val in d.items():
        if val == value:
            return key
    return None  # jeśli nie znaleziono wartości
