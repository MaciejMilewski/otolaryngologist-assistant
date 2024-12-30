from datetime import date, datetime
from io import BytesIO
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, render_template, request, abort, jsonify, send_file, flash, redirect
from flask_login import login_required, current_user

from jinja2 import TemplateNotFound

from app import db, parquet_data, dane_woj
from app.models import Procedure, Patient, Visit
from app.utils.const import place
from app.utils.parquet_util import get_streets_from_memory

from app.utils.utils import (ogolne_items, orl_items, validate_request_badania, validate_request_structure_main,
                             validate_request_szept, zalecenia, generate_pdf)

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


@visit_bp.route('/drukuj', methods=['GET', 'POST'])
@login_required
def drukuj():
    # Generowanie PDF
    pdf = generate_pdf(request.form)

    # Zapisanie PDF w pamięci
    pdf_data = pdf.output(dest='S').encode('latin1')
    buffer = BytesIO(pdf_data)
    buffer.seek(0)

    # Zwrócenie pliku PDF jako odpowiedź
    return send_file(buffer, mimetype='application/pdf',
                     download_name=f"{request.form['first_name']}_{request.form['surname']}.pdf",
                     as_attachment=True)



@visit_bp.route('/zapis', methods=['POST'])
@login_required
def zapis_wizyty_do_bazy():

    dane = request.form

    gender = 'M' if int(dane.get("pesel")[10]) % 2 else "K"

    # 'hiddenResultInput' - zwraca id pacjenta, który jest już zapisany w tabeli 'patient' - przez autocomplete !
    hidden_result_input = dane.get("hiddenResultInput", "")

    try:
        if hidden_result_input == "":
            # sprawdzić po 'peselu' czy zapisywany aktualnie pacjent jest już w tabeli 'patient' ?
            result = db.session.execute(db.select(Patient.id).filter(Patient.pesel == dane.get("pesel"))).first()

            # 1. jeżeli NIE, to zapisać jego dane w tabeli 'pacjent' (name,pesel,adres)
            if result is None:
                new_patient = Patient(first_name=dane.get("first_name"),
                                      surname=dane.get("surname"),
                                      pesel=dane.get("pesel"),
                                      gender=gender,
                                      state=dane.get("wojewodztwo"),
                                      city=dane.get("city_select"),
                                      street=dane.get("street"),
                                      apartment_number=dane.get("home_numer"))
                db.session.add(new_patient)
                db.session.commit()
                patient_saved_id = db.session.execute(
                    db.select(Patient.id).filter(Patient.pesel == dane.get("pesel"))
                ).scalar()
                patient_id = patient_saved_id
            else:
                patient_id = result[0]
        else:
            patient_id = dane.get("hiddenResultInput")

        # Obsługa daty audiogramu i usunięcie zbędnych pól, jeśli brak danych
        # Inicjalizacja pól audiogramu domyślnie jako None
        ul_250 = ul_500 = ul_1000 = ul_2000 = ul_3000 = ul_4000 = ul_6000 = ul_8000 = None
        up_250 = up_500 = up_1000 = up_2000 = up_3000 = up_4000 = up_6000 = up_8000 = None
        data_audiogramu = None

        if dane.get("data_audiogramu"):
            # Pobierz dane audiogramu
            data_audiogramu = datetime.strptime(dane.get("data_audiogramu"), "%Y-%m-%d")
            ul_250 = dane.get('UL__250')
            ul_500 = dane.get('UL__500')
            ul_1000 = dane.get('UL__1000')
            ul_2000 = dane.get('UL__2000')
            ul_3000 = dane.get('UL__3000')
            ul_4000 = dane.get('UL__4000')
            ul_6000 = dane.get('UL__6000')
            ul_8000 = dane.get('UL__8000')
            up_250 = dane.get('UP__250')
            up_500 = dane.get('UP__500')
            up_1000 = dane.get('UP__1000')
            up_2000 = dane.get('UP__2000')
            up_3000 = dane.get('UP__3000')
            up_4000 = dane.get('UP__4000')
            up_6000 = dane.get('UP__6000')
            up_8000 = dane.get('UP__8000')

            # Sprawdzenie, czy jakakolwiek wartość audiogramu jest niewypełniona
            czy_audiogram_ma_dane = any([
                data_audiogramu,
                ul_250, ul_500, ul_1000, ul_2000, ul_3000, ul_4000, ul_6000, ul_8000,
                up_250, up_500, up_1000, up_2000, up_3000, up_4000, up_6000, up_8000
            ])

            if not czy_audiogram_ma_dane:
                # Jeśli brak danych, zerujemy datę audiogramu i wszystkie pola
                data_audiogramu = None
                ul_250 = None
                ul_500 = None
                ul_1000 = None
                ul_2000 = None
                ul_3000 = None
                ul_4000 = None
                ul_6000 = None
                ul_8000 = None
                up_250 = None
                up_500 = None
                up_1000 = None
                up_2000 = None
                up_3000 = None
                up_4000 = None
                up_6000 = None
                up_8000 = None

        # 3. zapisać resztę danych w tabeli 'Visit'

        if patient_id is None:
            flash("Nie można zapisać wizyty, ponieważ nie udało się znaleźć pacjenta.", "danger")
            return redirect('/visit')

        print("zabiegi:", dane.get('zabieg2'))
        new_visit = Visit(
            user_id=current_user.id,
            patient_id=patient_id,
            diagnosis=dane.get('diagnoza'),
            location=dane.get('siteZapis'),
            interview=dane.get('wywiad'),
            general_info=dane.get('ogolne'),
            orl=dane.get('orl'),
            examination=dane.get('laryngolog'),
            recommendations=dane.get('zalecenie'),
            whisper_test=dane.get('szepty'),
            nfz_info=dane.get('kody_nfz'),
            audiogram_date=data_audiogramu,
            examination_date=date.today(),
            routine=dane.get('zabiegi'),
            ul_250=ul_250,
            ul_500=ul_500,
            ul_1000=ul_1000,
            ul_2000=ul_2000,
            ul_3000=ul_3000,
            ul_4000=ul_4000,
            ul_6000=ul_6000,
            ul_8000=ul_8000,
            up_250=up_250,
            up_500=up_500,
            up_1000=up_1000,
            up_2000=up_2000,
            up_3000=up_3000,
            up_4000=up_4000,
            up_6000=up_6000,
            up_8000=up_8000)

        db.session.add(new_visit)
        db.session.commit()
        flash("Zapisano pomyślnie dane wizyty w bazie danych!", "success")
        return redirect('/visit')
    except IntegrityError as e:
        db.session.rollback()
        flash(f"Błąd zapisu bazy danych: {e}", "danger")
        return redirect('/visit')
