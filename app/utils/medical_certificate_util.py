from datetime import datetime, date

from flask import request
from fpdf import FPDF

from app import db
from app.models import Patient, MedicalCertificate
from app.utils.const import typ_messages, typ_messages_no
from app.utils.utils import pesel2birth, walidacja_pesela


def initialize_pdf():
    """Ustawienia wstępne dla PDF."""
    pdf = FPDF(format=(110, 220))  # Rozmiar strony DL
    pdf.add_page()
    pdf.add_font('DejaVu', '', './Fonts/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu-Bold', '', './Fonts/DejaVuSans-Bold.ttf', uni=True)
    return pdf


def add_header(pdf, what_place):
    """Dodaje nagłówek z datą i miejscem."""
    data_stanu = datetime.now().strftime('%Y-%m-%d')
    pdf.set_font('DejaVu', size=10)
    pdf.cell(0, 10, f"{what_place}, dnia {data_stanu}", ln=True, align='R')
    pdf.ln(5)


def add_title(pdf, title):
    """Dodaje tytuł dokumentu."""
    pdf.set_font('DejaVu-Bold', size=14)
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(8)


def add_personal_data(pdf, data, birth=None):
    """Dodaje dane osobowe."""
    pdf.set_font('DejaVu-Bold', size=10)
    pdf.cell(0, 10, "Dane osobowe:", ln=True, align='L')
    pdf.set_font('DejaVu', size=10)
    pdf.cell(0, 10, f"Nazwisko i imię: {data['first_name'].upper()} {data['surname'].upper()}", ln=True)
    pdf.multi_cell(0, 10, f"Data urodzenia: {birth or '??-??-????'}")
    if data['street']:
        pdf.multi_cell(0, 10, f"Adres zamieszkania: {data['city_select'].upper()}, ul. {data['street'].upper()} {data['home_numer']}")
    else:
        pdf.multi_cell(0, 10, f"Adres zamieszkania: {data['city_select'].upper()} {data['home_numer']}")
    pdf.ln(5)


def add_signature(pdf):
    """Dodaje sekcję podpisu."""
    pdf.set_font('DejaVu-Bold', size=8)
    pdf.cell(0, 10, "Podpis i pieczątka:", ln=True, align='R')
    pdf.ln(2)


def pdf_zaswiadczenie(data):
    """Generuje PDF zaświadczenia."""
    pdf = initialize_pdf()
    add_header(pdf, data['place'])
    add_title(pdf, "ZAŚWIADCZENIE")

    # Dane osobowe bez daty urodzenia i dowodu osobistego
    pdf.set_font('DejaVu-Bold', size=10)
    pdf.cell(0, 10, "Dane osobowe:", ln=True, align='L')
    pdf.set_font('DejaVu', size=10)
    pdf.cell(0, 10, f"{data['first_name'].upper()} {data['surname'].upper()}", ln=True)

    if data['street']:
        pdf.multi_cell(0, 10, f"{data['city_select'].upper()}, ul. {data['street'].upper()} {data['home_numer']}")
    else:
        pdf.multi_cell(0, 10, f"{data['city_select'].upper()} {data['home_numer']}")

    pdf.ln(5)

    # Treść zaświadczenia
    pdf.set_font('DejaVu', size=11)
    if data['zdolny'] == '1':
        pdf.multi_cell(0, 10, typ_messages.get(data['typ'], "Nieznany typ badania."))
    else:
        pdf.multi_cell(0, 10, typ_messages_no.get(data['typ'], "Nieznany typ badania."))
    pdf.ln(10)

    # Uwagi
    pdf.set_font('DejaVu-Bold', size=10)
    pdf.cell(0, 10, "Uwagi:", ln=True)
    pdf.line(10, pdf.get_y(), 100, pdf.get_y())
    pdf.set_font('DejaVu', size=10)
    pdf.multi_cell(0, 10, data.get('add_information', '+').upper())
    pdf.ln(15)

    add_signature(pdf)

    return pdf


def pdf_orzeczenie_lekarskie(data):
    """Generuje PDF orzeczenia lekarskiego."""
    pdf = initialize_pdf()
    add_header(pdf, data['place'])
    add_title(pdf, "ZAŚWIADCZENIE")

    # Obsługa daty urodzenia
    birth = '??-??-????'
    if walidacja_pesela(data['pesel']):
        birth = pesel2birth(data['pesel'])

    add_personal_data(pdf, data, birth)

    # Rozpoznania
    pdf.set_font('DejaVu-Bold', size=10)
    pdf.cell(0, 10, "Rozpoznania:", ln=True, align='L')
    pdf.set_font('DejaVu', size=10)
    pdf.multi_cell(0, 10, f"{data.get('add_information', 'BRAK').upper()}")
    pdf.ln(5)

    # Cel wydania
    pdf.set_font('DejaVu-Bold', size=10)
    pdf.cell(0, 10, "Cel wydania zaświadczenia:", ln=True, align='L')
    pdf.set_font('DejaVu', size=10)
    pdf.multi_cell(0, 8, "Na wniosek powyżej wymienionej osoby.")
    pdf.ln(7)

    add_signature(pdf)

    # Dodatkowe informacje
    pdf.set_font('DejaVu', size=7)
    pdf.multi_cell(0, 6, "(1) Wypełniać w przypadkach uzasadnionych.")
    pdf.multi_cell(0, 6,
                   "(2) W zaświadczeniu nie należy zamieszczać rozpoznania, jeżeli z uwagi na cel "
                   "wydania zaświadczenia nie jest to konieczne, bądź też zamieszczanie rozpoznania "
                   "stanowiłoby naruszenie tajemnicy zawodowej.")
    return pdf


def get_search_params():
    """
    :return: A dictionary containing search parameters extracted from the form request.
    :rtype: dict
    """
    return {
        'lastname': request.form.get('lastname'),
        'start_date': request.form.get('start_date'),
        'end_date': request.form.get('end_date'),
        'typ_badania': request.form.get('typ'),
        'zdolny': 1 if request.form.get('zdolny') else 0,
        'all_type': 1 if request.form.get('all_type') else 0
    }


def convert_row_to_dict(row):
    """
    :param row: A row of data, represented as a list or tuple.
    :return: A dictionary where the keys are column names and the values are the corresponding elements from the input row.
    """
    return {
        'id': row[0],
        'created': row[1],
        'type': row[2],
        'firstname': row[3],
        'lastname': row[4],
        'gender': row[5],
        'stan': row[6],
        'city': row[7],
        'street': row[8],
        'number': row[9],
        'able_to_work': row[10],
        'info': row[11],
        'month': row[12],
        'year': row[13]
    }


def get_request_data(key):
    """
    :param key: Key to extract from the JSON request data.
    :return: Value associated with the key in the JSON request data.
    :raises ValueError: If the specified key is not found in the request data.
    """
    data = request.get_json()
    if not data or key not in data:
        raise ValueError(f"Brakuje klucza: {key}")
    return data[key]


def save_medical_certificate(data, user_id):
    """
    Zapisuje pacjenta oraz orzeczenie lekarskie w bazie danych.

    :param user_id:
    :param data: Słownik zawierający dane formularza.
    :return: Słownik z informacjami o pacjencie i orzeczeniu lub wyjątek w razie błędu.
    """
    try:
        pesel = data.get('pesel')
        first_name = data.get('first_name')
        surname = data.get('surname')
        wojewodztwo = data.get('wojewodztwo')
        city = data.get('city_select')
        street = data.get('street')
        home_number = data.get('home_numer')
        typ = data.get('typ')
        place = data.get('place')
        additional_info = data.get('add_information')
        zdolny = bool(int(data.get('zdolny', 0)))  # Przekonwertuj zdolny na boolean

        # Sprawdzenie, czy pacjent istnieje w bazie
        patient = Patient.query.filter_by(pesel=pesel).first()

        if not patient:
            gender = 'M' if int(pesel[10]) % 2 else "K"
            patient = Patient(
                first_name=first_name,
                surname=surname,
                pesel=pesel,
                gender=gender,
                state=wojewodztwo,
                city=city,
                street=street,
                apartment_number=home_number
            )
            db.session.add(patient)
            db.session.commit()  # Zapisz, aby pacjent miał ID

        # Zapisz orzeczenie
        certificate = MedicalCertificate(
            patient_id=patient.id,
            created_at=date.today(),
            type=typ,
            info=additional_info,
            location=place,
            user_id=user_id,
            is_able_to_work=zdolny,
            month=datetime.today().month,
            year=datetime.today().year
        )
        db.session.add(certificate)
        db.session.commit()

        return {"patient": patient, "certificate": certificate}
    except Exception as e:
        db.session.rollback()
        raise e
