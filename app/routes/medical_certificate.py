import json
import logging
import logging
import os
from datetime import datetime, date, timedelta
from io import BytesIO
import plotly.graph_objects as go

import pandas as pd
import plotly
from flask import Blueprint, render_template, abort, request, jsonify, redirect, url_for, send_file
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound
from sqlalchemy.exc import SQLAlchemyError

from app import parquet_data, dane_woj, db
from app.models import Patient, MedicalCertificate
from app.utils.const import typ_badan, place
from app.utils.medical_certificate_util import pdf_orzeczenie_lekarskie, pdf_zaswiadczenie, save_medical_certificate
from app.utils.parquet_util import get_streets_from_memory

medical_certificate_bp = Blueprint('medical_certificate', __name__)


@medical_certificate_bp.route('/medical_certificate', methods=['GET'])
@login_required
def medical_certificate_main():
    try:
        wojewodztwo_default = '22'  # Domyślne województwo - "POMORSKIE" (kod '22')

        if 'POMORSKIE' in parquet_data:
            miejscowosc_choices = parquet_data["POMORSKIE"]['Nazwa'].tolist()
        else:
            miejscowosc_choices = []

        default_miejscowosc = "Pruszcz Gdański"

        ulica_choices = get_streets_from_memory("POMORSKIE", default_miejscowosc)
        return render_template('medical_certificate.html',
                               user=current_user.login,
                               typ=typ_badan,
                               place=place,
                               woj=dane_woj,
                               woj_default=wojewodztwo_default,
                               cities=miejscowosc_choices,
                               city_default=default_miejscowosc,
                               streets=ulica_choices,
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
        logging.error(f"Błąd podczas zapisywania orzeczenia lekarskiego: {e}")
        return "Wystąpił błąd podczas przetwarzania zapytania.", 500


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
        pdf_buffer = BytesIO(pdf_data)  # Umieszcza dane w obiekcie BytesIO
        pdf_buffer.seek(0)  # Ustaw wskaźnik na początek bufora

        # Wysyłanie PDF jako pliku do pobrania
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            download_name=f"{data['first_name']}_{data['surname']}.pdf",
            as_attachment=True
        )
    except Exception as error_building:
        logging.error(f"Błąd podczas generowania PDF: {str(error_building)}")
        return jsonify({'błąd': 'Nie udało się wygenerować PDF'}), 500


def today_offset(offset_days=0):
    """
    :param offset_days: Number of days to offset from the current date. Defaults to 0.
    :return: The current date and time offset by the specified number of days.
    """
    return datetime.now() + timedelta(days=offset_days)

def fetch_data_range_from_db(begin_date, end_date):
    """
    Fetches data about patients and their medical certificates from the database within a given date range.

    :param begin_date: The start of the date range for which data is to be fetched.
    :param end_date: The end of the date range for which data is to be fetched.
    :param session: The SQLAlchemy session object.
    :return: A list of tuples containing data fetched from the database.
             Each tuple consists of (created_at, first_name, surname, city, info, type, is_able_to_work).
             Returns an empty list if an error occurs.
    """
    try:
        # Pobieranie danych z tabel połączonych kluczem patient_id
        results = (
            db.session.query(
                MedicalCertificate.created_at,
                Patient.first_name,
                Patient.surname,
                Patient.city,
                MedicalCertificate.info,
                MedicalCertificate.type,
                MedicalCertificate.is_able_to_work
            )
            .join(Patient, Patient.id == MedicalCertificate.patient_id)
            .filter(MedicalCertificate.created_at.between(begin_date, end_date))
            .all()
        )
        return results
    except SQLAlchemyError as db_error:
        logging.error(f"Database error: {db_error}")
        return []
    except Exception as unexpected_error:
        logging.error(f"Unexpected error: {unexpected_error}")
        return []


def process_grouped_data(df, selected_types, start_date=None, end_date=None):
    """
    Processes the DataFrame to prepare data for creating a Plotly chart.

    :param df: DataFrame containing the data to be processed.
    :param selected_types: List of types to filter the data by. If "all" is in the list, all types are included.
    :param start_date: Optional start date to filter the data by created_at.
    :param end_date: Optional end date to filter the data by created_at.
    :return: DataFrame with grouped and aggregated data, including a summary row.
    """
    # Filtrujemy dane na podstawie zakresu dat
    if start_date:
        df = df[df['created_at'] >= start_date]
    if end_date:
        df = df[df['created_at'] <= end_date]

    # Filtrujemy typy badań
    if "all" in selected_types:
        grouped = df.groupby(["created_at", "first_name", "surname", "city", "info"]).agg(
            num_examinations=("created_at", "size"),
            able_to_work=("is_able_to_work", "sum")
        ).reset_index()
    else:
        selected_types_int = [int(t) for t in selected_types]
        grouped = df[df["type"].isin(selected_types_int)].groupby(
            ["created_at", "first_name", "surname", "city", "info"]
        ).agg(
            num_examinations=("created_at", "size"),
            able_to_work=("is_able_to_work", "sum")
        ).reset_index()

    # Obliczamy sumy
    total_examinations = grouped["num_examinations"].sum()
    total_able_to_work = grouped["able_to_work"].sum()

    # Zmieniamy nazwy kolumn na bardziej czytelne
    grouped = grouped.rename(columns={
        'created_at': 'DATA',
        'first_name': 'IMIĘ',
        'surname': 'NAZWISKO',
        'city': 'MIASTO',
        'info': 'INFO',
        'num_examinations': 'ILOŚĆ',
        'able_to_work': 'PRACA T/N'
    })

    # Dodajemy wiersz podsumowania
    summary_row = pd.DataFrame({
        'DATA': ['SUMA'],
        'IMIĘ': ['-'],
        'NAZWISKO': ['-'],
        'MIASTO': ['-'],
        'INFO': ['-'],
        'ILOŚĆ': [total_examinations],
        'PRACA T/N': [total_able_to_work]
    })

    return pd.concat([grouped, summary_row], ignore_index=True)


def create_plot(df, selected_types):
    """
    :param df: DataFrame containing the data to be plotted. It should at least have columns 'created' and 'type'.
    :param selected_types: List of integers representing the types to filter data before plotting.
                           Use ["all"] to include all types.
    :return: A JSON string representing the Plotly figure.
    """
    df = pd.DataFrame(df)

    # Filtrujemy dane na podstawie `selected_types`
    if "all" not in selected_types:
        # Konwersja `selected_types` string do typu int, aby dopasować do typu kolumny 'type'
        selected_types = [int(t) for t in selected_types]
        # Filtrowanie, usuwamy wiersze w których typ nie występuje w selected_types
        df = df[df['type'].isin(selected_types)]

    # Dodajemy kolumnę zliczającą wystąpienia
    df['count'] = 1

    # Pivot table for plotting
    pivot_df = df.pivot_table(index='created', columns='type', values='count', aggfunc='sum', fill_value=0)

    # Przekształcenie indeksu na listę unikalnych wartości daty jako kategorie
    dates = pivot_df.index.tolist()

    # Odwrócenie kolejności kolumn w `pivot_df`
    reversed_columns = pivot_df.columns[::-1]

    # Create Plotly stacked bar chart
    fig = go.Figure()

    for column in reversed_columns:
        fig.add_trace(
            go.Bar(
                x=dates,  # dates - typ category, poprzednio było pivot_df.index,
                y=pivot_df[column],
                name=f"Typ {column}",
                hovertemplate=f"Typ {column}, data: %{{x}}<br>Ilość: %{{y}}<extra></extra>",
                showlegend=True  # Wymusza wyświetlanie legendy
            )
        )

    fig.update_layout(
        barmode='stack',
        title='Rys. Badania wykonane w szukanym okresie.',
        xaxis=dict(
            title='Daty',
            type='category',  # Ustawienie osi X jako kategoria
            tickangle=-45  # Kąt nachylenia etykiet
        ),
        yaxis=dict(title='Ilość badań')
    )

    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


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

    # Pobieranie wybranych typów badań z formularza
    selected_types = request.form.getlist("selected_types")
    if "all" in selected_types or not selected_types:
        selected_types = ["all"]

    # Inicjalizacja zakresu dat
    start_date, end_date = initialize_dates()

    # Pobranie danych z bazy
    data = fetch_data_range_from_db(start_date, end_date)

    if not data:
        return render_template(
            'medical_certificate_raport.html',
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
        selected_types=selected_types,
        start_date=start_date,
        end_date=end_date,
        plot=graph_json
    )