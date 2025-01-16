import logging

from datetime import datetime, timedelta
from io import BytesIO

from bs4 import BeautifulSoup
import pandas as pd

from flask import Blueprint, render_template, abort, request, jsonify, redirect, url_for, send_file
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

from app import parquet_data, region_data, db

from app.utils.const import typ_badan, place
from app.utils.medical_certificate_util import pdf_orzeczenie_lekarskie, pdf_zaswiadczenie, save_medical_certificate
from app.utils.parquet_util import get_streets_from_memory
from fpdf import FPDF

from app.utils.utils import create_plot, process_grouped_data, fetch_data_range_from_db, handle_form_request

medical_certificate_bp = Blueprint('medical_certificate', __name__)




@medical_certificate_bp.route('/medical_certificate', methods=['GET'])
@login_required
def medical_certificate_main():
    try:
        voivvoivodeship_default = '22'  # Domyślne województwo - "POMORSKIE" (kod '22')

        if 'POMORSKIE' in parquet_data:
            city_list = parquet_data["POMORSKIE"]['Nazwa'].tolist()
        else:
            city_list = []

        default_city = "Pruszcz Gdański"

        streets_list = get_streets_from_memory("POMORSKIE", default_city)

        return render_template('medical_certificate.html',
                               user=current_user.login,
                               typ=typ_badan,
                               place=place,
                               woj=region_data,
                               woj_default=voivvoivodeship_default,
                               cities=city_list,
                               city_default=default_city,
                               streets=streets_list,
                               today=datetime.now().strftime('%Y-%m-%d'))
    except TemplateNotFound:
        return abort(404)


@medical_certificate_bp.route('/save', methods=['POST'])
def save():
    try:
        form_data = request.form.to_dict()
        save_medical_certificate(form_data)

        return redirect(url_for('medical_certificate.medical_certificate_main'))

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error when saving medical certificate: {e}")
        return "Error when saving medical certificate.", 500


@medical_certificate_bp.route('/medical_certificate_pdf', methods=['POST'])
def medical_certificate_pdf():
    try:
        data = request.form.to_dict()

        save_medical_certificate(data)

        if data['typ'] == '11':
            pdf = pdf_orzeczenie_lekarskie(data)
        else:
            pdf = pdf_zaswiadczenie(data)

        pdf_data = pdf.output(dest='S').encode('latin1')  # Zwraca dane jako ciąg bajtów
        pdf_buffer = BytesIO(pdf_data)
        pdf_buffer.seek(0)

        # Wysyłanie PDF jako pliku do pobrania
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            download_name=f"{data['first_name']}_{data['surname']}.pdf",
            as_attachment=True
        )
    except Exception as error_building:
        logging.error(f"Error generating PDF: {str(error_building)}")
        return jsonify({'błąd': 'Nie udało się wygenerować PDF'}), 500


@medical_certificate_bp.route('/raport', methods=['GET', 'POST'])
@login_required
def raport():
    """
    Handles GET and POST requests to generate a report based on user input or default date ranges.
    Supports filtering by selected types and date ranges.

    :return: Rendered HTML template including a data table and possibly a plot.
    """
    # Funkcja pomocnicza do inicjalizacji dat
    def initialize_dates():
        days_offset = -120
        default_end_date = datetime.today().strftime("%Y-%m-%d")
        default_start_date = (datetime.today() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        return request.form.get("start_date", default_start_date), request.form.get("end_date", default_end_date)

    selected_types = handle_form_request()

    # Inicjalizacja zakresu dat
    start_date, end_date = initialize_dates()

    # Pobranie danych z bazy
    data = fetch_data_range_from_db(start_date, end_date)

    if not data:
        return render_template(
            'medical_certificate_raport.html',
            typ=typ_badan,
            alert_message="No data available",
            table_html="",
            sum_text="",
            selected_types=selected_types,
            start_date=start_date,
            end_date=end_date,
            plot="{}"
        )

    # Utworzenie Data Frame z pobranych danych
    df = pd.DataFrame(data, columns=[
        "created_at", "first_name", "surname", "city", "info", "type", "is_able_to_work"
    ])

    # Przetworzenie danych do tabeli i wykresu
    grouped_data = process_grouped_data(df, selected_types, start_date, end_date)

    # Generowanie HTML tabeli
    table_html = grouped_data.to_html(classes='data table', header=True, index=False, border=0, justify='center')

    # Tworzenie JSON wykresu
    graph_json = create_plot(df, selected_types)

    return render_template(
        'medical_certificate_raport.html',
        table_html=table_html,
        typ=typ_badan,
        selected_types=selected_types,
        start_date=start_date,
        end_date=end_date,
        data=graph_json
    )


@medical_certificate_bp.route('/generate_pdf_for_raport', methods=['POST'])
@login_required
def generate_pdf_for_raport():
    """
    Generates a PDF report based on the provided HTML table and selected test types within a specified date range.
    """
    # Pobierz dane z zapytania
    table_html = request.form.get('table_html', '')
    selected_types = request.form.getlist("selected_types")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")

    # Słownik do mapowania typów badań na nazwy
    typ_badan_dict = {badanie['id']: badanie['name'] for badanie in typ_badan}


    # Generowanie opisu wybranych typów badań
    if selected_types and selected_types != ['all']:
        badania_pdf = ", ".join(typ_badan_dict.get(typ, f"Typ {typ}") for typ in selected_types)
    else:
        badania_pdf = "wszystkie rodzaje badań !"

    # Parsowanie HTML za pomocą BeautifulSoup
    soup = BeautifulSoup(table_html, 'html.parser')

    # Znajdź indeksy kolumn "MIASTO" i "INFO"
    headers = [header.text.strip() for header in soup.find_all('th')]
    columns_to_remove = [headers.index("MIASTO"), headers.index("INFO")]

    # Usuń nagłówki kolumn "MIASTO" i "INFO"
    headers = [header for i, header in enumerate(headers) if i not in columns_to_remove]

    # Przetwórz wiersze i pomiń komórki odpowiadające "MIASTO" i "INFO"
    rows = [
        [cell.text.strip() for i, cell in enumerate(row.find_all('td')) if i not in columns_to_remove]
        for row in soup.find_all('tr')
    ]

    # Tworzenie pliku PDF za pomocą FPDF
    pdf = FPDF()
    pdf.add_page()

    # Dodanie czcionki TrueType
    pdf.add_font('DejaVu', '', './Fonts/DejaVuSans.ttf', uni=True)
    pdf.add_font('DejaVu-Bold', '', './Fonts/DejaVuSans-Bold.ttf', uni=True)

    # Ustawienie czcionki podstawowej
    pdf.set_font("DejaVu", size=10)

    # Dodanie logo i tytułu
    pdf.image('app/static/img/butterfly.png', 10, 8, 24, 24)
    pdf.set_font("DejaVu-Bold", size=18)
    pdf.cell(0, 10, "Raport", ln=True, align='C')  # Tytuł na środku
    pdf.ln(3)

    # Dodanie informacji o zakresie dat i typach badań
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, f"Zakres dni od {start_date} do {end_date}", ln=True, align='C')
    pdf.cell(0, 10, f"Typy badań: {badania_pdf}", ln=True, align='C')

    # Dodanie odstępu przed tabelą
    pdf.ln(7)

    # Tabela - nagłówki
    pdf.set_font("DejaVu-Bold", size=10)
    pdf.set_fill_color(60, 120, 180)  # Niebieski odcień dla nagłówków
    pdf.set_text_color(255, 255, 255)  # Biały tekst
    pdf.set_draw_color(50, 50, 50)  # Obramowanie ciemnoszare
    pdf.set_line_width(0.4)

    # Usunięcie pustych wierszy z `rows`
    filtered_rows = [row for row in rows if row]  # Filtruje puste wiersze

    # Pobierz szerokość strony PDF (domyślnie A4 w FPDF)
    page_width = pdf.w - 2 * pdf.l_margin  # Szerokość strony minus marginesy

    # Obliczanie szerokości kolumn
    if filtered_rows:
        max_col_widths = [max(len(str(cell)) for cell in col) + 2 for col in zip(*([headers] + filtered_rows))]
    else:
        max_col_widths = [len(header) + 2 for header in headers]  # Gdy brak danych w wierszach

    # Przeliczenie szerokości kolumn na procenty i dostosowanie do szerokości strony
    total_max_width = sum(max_col_widths)
    col_widths = [(page_width * w / total_max_width) for w in max_col_widths]

    # Debugowanie
    # print("Page Width:", page_width)
    # print("Column Widths:", col_widths)

    # Rysowanie nagłówków
    pdf.set_font("DejaVu-Bold", size=10)
    pdf.set_fill_color(60, 120, 180)    # Niebieskie tło
    pdf.set_text_color(255, 255, 255)   # Biały tekst
    pdf.set_draw_color(50, 50, 50)      # Obramowanie
    pdf.set_line_width(0.4)

    for idx, header in enumerate(headers):
        pdf.cell(col_widths[idx], 10, header, border=1, align='C', fill=True)
    pdf.ln()

    # Rysowanie wierszy
    pdf.set_font("DejaVu", size=10)     # Reset tekstu na czarny
    pdf.set_text_color(0, 0, 0)         # Czarny tekst
    for row_idx, row in enumerate(filtered_rows):
        fill_color = (245, 245, 245) if row_idx % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*fill_color)
        for col_idx, cell in enumerate(row):
            pdf.cell(col_widths[col_idx], 10, cell, border=1, align='C', fill=True)
        pdf.ln()

    # Zapisz plik PDF w pamięci
    pdf_data = pdf.output(dest='S')
    # Konwersja str na bytes za pomocą kodowania latin1
    pdf_bytes = pdf_data.encode('latin1')

    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)

    # Zwróć plik PDF jako odpowiedź
    return send_file(buffer, mimetype='application/pdf', download_name="raport.pdf", as_attachment=True)