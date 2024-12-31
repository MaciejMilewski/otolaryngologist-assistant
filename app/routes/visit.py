import logging
from datetime import date, datetime
from io import BytesIO
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, abort, jsonify, send_file, flash, redirect
from flask_login import login_required, current_user

from jinja2 import TemplateNotFound

from app import db, parquet_data, dane_woj
from app.models import Procedure, Patient, Visit, Audiogram
from app.utils.const import place
from app.utils.parquet_util import get_streets_from_memory

from app.utils.utils import (ogolne_items, orl_items, validate_request_badania, validate_request_structure_main,
                             validate_request_szept, zalecenia, generate_pdf, prepare_audiogram_data, save_visit_to_db)

from typing import List, Optional

ALLOWED_FIELDS = {'pesel', 'surname'}  # Definicja dozwolonych kolumn -field- dla szukania w bazie danych


def get_data_to_autocomplete(query: str, field: str) -> Optional[List[List]]:
    if field not in ALLOWED_FIELDS:
        raise ValueError("Invalid -field- parameter in autocomplete")
    try:
        # Otwórz nową sesję
        # Dynamiczne filtrowanie za pomocą getattr
        result = db.session.query(Patient).filter(getattr(Patient, field).like(f"{query}%")).all()
        # Zwrócenie tylko pożądanych pól
        fields_to_return = ['id', 'first_name', 'surname', 'pesel', 'gender', 'state', 'city', 'street',
                            'apartment_number']
        # Konwersja wyników na listę krotek z wszystkimi kolumnami
        return [[getattr(row, field) for field in fields_to_return] for row in result]
    except Exception as e:
        print(f"Problem z bazą danych i danymi pobieranymi dla autocomplete: {e}")
        return []


visit_bp = Blueprint('visit', __name__)


@visit_bp.route('/visit', methods=['GET'])
@login_required
def main_form():
    try:
        zabiegi = db.session.query(Procedure).all()
        return render_template('visit.html', user=current_user.login, zabiegi=zabiegi)
    except TemplateNotFound:
        return abort(404)


@visit_bp.route('/generuj', methods=['POST'])
@login_required
def generuj():
    try:
        dane = request.form

        # zabiegi = ' '.join(dane.getlist('selectZabiegi')).lstrip()
        zabiegi = dane.getlist('selectZabiegi')
        ogolne = validate_request_badania(ogolne_items, dane)
        laryngologiczne = validate_request_badania(orl_items, dane)
        orl = validate_request_structure_main(dane)
        szept = validate_request_szept(dane)
        zaleca = zalecenia(dane)

        today = date.today().strftime("%d-%m-%Y")

        wojewodztwo_default = '22'  # Domyślne województwo - "POMORSKIE" (kod '22')

        # Sprawdź, czy dane województwa są wczytane poprawnie
        if 'POMORSKIE' in parquet_data:
            miejscowosc_choices = parquet_data["POMORSKIE"]['Nazwa'].tolist()  # Wczytaj miejscowości
        else:
            miejscowosc_choices = []  # Pusta lista, jeśli nie zostały wczytane

        default_miejscowosc = "Pruszcz Gdański"

        # Pobierz ulice dla domyślnej miejscowości
        ulica_choices = get_streets_from_memory("POMORSKIE", default_miejscowosc)

        return render_template('visit_result.html', today=today, wywiad=dane['wywiad'], ogolne=ogolne,
                               laryngolog=laryngologiczne, data_szeptu=dane.get('data_badania'),
                               orl=orl, szept=szept, zabiegi=zabiegi, zalecenia=zaleca, UL_250=dane.get('UL_250'),
                               UL_500=dane.get('UL_500'), UL_1000=dane.get('UL_1000'), UL_2000=dane.get('UL_2000'),
                               UL_3000=dane.get('UL_3000'), UL_4000=dane.get('UL_4000'), UL_6000=dane.get('UL_6000'),
                               UL_8000=dane.get('UL_8000'), UP_250=dane.get('UP_250'), UP_500=dane.get('UP_500'),
                               UP_1000=dane.get('UP_1000'), UP_2000=dane.get('UP_2000'), UP_3000=dane.get('UP_3000'),
                               UP_4000=dane.get('UP_4000'), UP_6000=dane.get('UP_6000'), UP_8000=dane.get('UP_8000'),
                               data_audiogramu=dane.get('data_badania_audiogramu'),
                               place=place,
                               woj=dane_woj,
                               woj_default=wojewodztwo_default,
                               cities=miejscowosc_choices,
                               city_default=default_miejscowosc,
                               streets=ulica_choices)

    except TemplateNotFound:
        return abort(404)


@visit_bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('query', '').strip()
    field = request.args.get('field', '').strip()

    try:
        results = get_data_to_autocomplete(query, field)
        if results:
            results = [list(row) for row in results]  # Konwersja tupli na listy
        else:
            results = []
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    return jsonify(results)


@visit_bp.route('/get_miejscowosci', methods=['POST'])
def get_miejscowosci():
    """
    Fetches a list of localities (miejscowosci) for a given voivodeship code and returns them as pairs of (index, name).

    :return: A JSON object containing a list of localities.
    """
    # Obsługa JSON i form-urlencoded
    if request.is_json:
        data = request.get_json()  # Pobieranie danych JSON
        kody_wojewodztwa = data.get('wojewodztwo')
    else:
        kody_wojewodztwa = request.form.get('wojewodztwo')  # Pobieranie danych form-urlencoded

    if not kody_wojewodztwa:
        return jsonify({"error": "Brak województwa"}), 400

    name_wojewodztwa = dane_woj.get(kody_wojewodztwa, '')

    # Pobierz tylko kolumnę 'Nazwa' z danych dla wybranego województwa
    if name_wojewodztwa in parquet_data:
        miejscowosci = parquet_data[name_wojewodztwa]['Nazwa'].tolist()  # Wyciągnięcie tylko kolumny 'Nazwa'
    else:
        miejscowosci = []

    # Zwróć listę miejscowości jako pary (index, nazwa)
    miejscowosci_pary = [(i, miejscowosc) for i, miejscowosc in enumerate(miejscowosci)]

    return jsonify({'miejscowosci': miejscowosci_pary})


@visit_bp.route('/get_ulice', methods=['POST'])
def get_ulice():
    """
    Handles the '/get_ulice' route to fetch street names via AJAX based on provided province and locality codes.
    :return: JSON response containing a list of street names and a status code. If the required province or locality
     codes are missing, it returns a 400 status. If no streets are found for the locality, it returns an empty list with
     a 200 status.
    """
    kod_wojewodztwa = request.form.get('wojewodztwo') or (request.get_json() or {}).get('wojewodztwo')

    if not kod_wojewodztwa:
        print(f"/get_ulice : Brak kodów województwa aby szukać ulic!")
        return jsonify({'ulice': []}), 400

    kod_wojewodztwa = kod_wojewodztwa.strip()

    miejscowosc = request.form.get('miejscowosc') or (request.get_json() or {}).get('miejscowosc')

    if not miejscowosc:
        print("/get_ulice : Brak miejscowości aby szukać ulic!")
        return jsonify({'ulice': []}), 400

    miejscowosc = miejscowosc.strip()

    name_wojewodztwa = dane_woj.get(kod_wojewodztwa, '')  # dict.get(key,'') zwraca wartość klucza albo ''

    result = get_streets_from_memory(name_wojewodztwa, miejscowosc)

    if result:
        return jsonify({'ulice': result}), 200  # Zwracamy wynik w formacie JSON i status 200
    else:
        return jsonify({'ulice': []}), 200  # Zwracamy pustą listę ulic, ale status OK


@visit_bp.route('/drukuj', methods=['POST'])
@login_required
def drukuj():
    dane = request.form
    try:
        save_visit_to_db(dane, current_user.id)

        pdf = generate_pdf(dane)

        buffer = BytesIO(pdf)
        buffer.seek(0)

        return send_file(buffer, mimetype='application/pdf',
                         download_name=f"{dane.get("first_name")}_{dane.get("surname")}.pdf",
                         as_attachment=True)
    except IntegrityError as e:
        logging.error(f"Błąd podczas generowania PDF: {str(e)}")
        return redirect('/visit')
    except Exception as e:
        logging.error(f"Nieoczekiwany błąd podczas generowania PDF: {str(e)}")
        return redirect('/visit')


@visit_bp.route('/zapis', methods=['POST'])
@login_required
def zapis_wizyty_do_bazy():
    dane = request.form
    try:
        save_visit_to_db(dane, current_user.id)
        flash("Zapisano pomyślnie dane wizyty w bazie danych!", "success")
        return redirect('/visit')
    except IntegrityError as e:
        flash(f"Błąd zapisu bazy danych: {e}", "danger")
        return redirect('/visit')
    except Exception as e:
        flash(f"Nieoczekiwany błąd: {e}", "danger")
        return redirect('/visit')
