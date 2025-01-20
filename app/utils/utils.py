import ast
import logging
import os
import json
from datetime import datetime, date, timedelta
import plotly.graph_objects as go
import plotly
import pandas as pd
from fpdf import FPDF
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.models import MedicalCertificate
from flask import request
from app import db
from app.models import Schedule, Audiogram, Visit, Patient

ogolne_items = ['diabetes', 'hipertensio', 'arytmia', 'infarctus', 'heart failure', 'pacemaker', 'udar',
                'antykoagulanty', 'lipemia', 'sterydy', 'astma', 'tarczyca', 'kidney failure', 'dna',
                'zakrzepica', 'psoriasis', 'alergia', 'smokers', 'rzs', 'gerd', 'epilepsja', 'migrena',
                'depresja', 'schizofrenia', 'parkinson', 'sm', 'alzheimer', 'uczulenie', 'prostata',
                'guz_prostaty', 'guz_piersi', 'guz_pulmonum', 'guz_jelit', 'anaemia', 'przeszczep',
                'radio-chemia', 'cancer']

orl_items = ['hypoacusis', 'tinnitus', 'glue_ear', 'otitis', 'otosclerosis', 'menier', 'otitis_chronica',
             'perlak', 'post_pistons', 'operatio_auris', 'otitis_reccurens', 'rinithis', 'polekowy',
             'epistaxis', 'deviatio_septi', 'polypus_nasi', 'sinusitis', 'post_polipectomii', 'post_muko',
             'post_septi', 'post_fess', 'post_sinuses', 'adenoid', 'tonsilitis', 'hypertonsilitis',
             'tonsilitis_chronica', 'post_adenotomii', 'post_adenotonsils', 'post_tonsils', 'sleep_apnea',
             'rinithis_chronica', 'sjogren', 'torbiel', 'noduli_vocali', 'polypus_vocale', 'paresis_vacales',
             'paresis_iatrogenic', 'occupational_disease', 'post_larynx', 'cleft_palate']


# Funkcja zwraca wagę po oczyszczeniu z tekstu
def parse_weight(weight):
    try:
        return float(weight.replace(',', '.'))
    except (ValueError, AttributeError):
        return None


def validate_event_collision(user_id, start_date, end_date, exclude_event_id=None):
    if isinstance(start_date, str):
        start_date = datetime.fromisoformat(start_date)
    if isinstance(end_date, str):
        end_date = datetime.fromisoformat(end_date)

    if end_date <= start_date:
        return False, "Data zakończenia musi być po dacie rozpoczęcia."

    if start_date < datetime.now():
        return False, "Nie można ustawić wydarzenia w przeszłości."

    overlapping_events = Schedule.query.filter(
        Schedule.user_id == user_id,
        Schedule.id != exclude_event_id,  # Wyklucza edytowany event
        Schedule.start_date <= end_date.date(),
        Schedule.end_date >= start_date.date(),
        (Schedule.start_time <= end_date.time()) & (Schedule.end_time >= start_date.time())
    ).all()

    if overlapping_events:
        return False, "Kolizja czasowa z innym wydarzeniem."

    return True, None


def validate_request_badania(lista, data_request):
    result = []
    for item in lista:
        if data_request.get(item):
            result.append(data_request[item])

    return ', '.join(result) if len(result) > 0 else ''


def validate_request_szept(data_request):
    ul = data_request.get('szept_UL')
    up = data_request.get('szept_UP')

    if len(ul) == 0 and 0 == len(up):
        return ''

    temp = ''

    if len(ul) > 0:
        temp = f'szept ucha lewego :  {ul} [metry], '
    if len(up) > 0:
        temp += f'szept ucha prawego :  {up} [metry]. '

    return temp


def validate_request_structure_main(data_request):
    result = 'Stan ogólny : '
    result += "".join([data_request['general_condition'], '. '])
    result += 'Mimika twarzy : '
    result += "".join([data_request['facial_expressions'], '. '])
    result += 'Oczopląs samoistny : '
    result += "".join([data_request['spontaneous_nystagmus'], '. '])
    result += 'Skóra : '
    result += "".join([data_request['skin'], '. '])
    result += 'Węzły chłonne : '
    result += "".join([data_request['lymph_nodes_general_condition'], '. '])

    lymph_nodes_left = ['lymph_nodes_left_side_I', 'lymph_nodes_left_side_II', 'lymph_nodes_left_side_III',
                        'lymph_nodes_left_side_IV', 'lymph_nodes_left_side_V', 'lymph_nodes_left_side_VI',
                        'lymph_nodes_left_side_VII', 'lymph_nodes_left_side_VIII']
    lymph_nodes_right = ['lymph_nodes_right_side_I', 'lymph_nodes_right_side_II', 'lymph_nodes_right_side_III',
                         'lymph_nodes_right_side_IV', 'lymph_nodes_right_side_V', 'lymph_nodes_right_side_VI',
                         'lymph_nodes_right_side_VII', 'lymph_nodes_right_side_VIII']

    if data_request['lymph_nodes_general_condition'] != 'niewyczuwalne i niebolesne':
        if len(validate_request_badania(lymph_nodes_left, data_request)):
            result += 'Strona lewa szyi region : '
            result += validate_request_badania(lymph_nodes_left, data_request)
            result += '. '
        if len(validate_request_badania(lymph_nodes_right, data_request)):
            result += ' Strona prawa szyi region : '
            result += validate_request_badania(lymph_nodes_right, data_request)
            result += '. '

    parotis = ['parotis_good', 'parotis_left_submandibularis_big', 'ranula_left', 'mumps', 'ranula_right',
               'parotis_left_tumor', 'parotis_right_submandibularis_big', 'parotis_right_tumor']

    temp = validate_request_badania(parotis, data_request)

    if len(temp) > 0:
        result += ' Ślinianki : '
        result += temp

    throat = ['throat', 'throat_infection', 'throat_chronica', 'throat_afty', 'throat_fungis', 'throat_leukoplakia',
              'throat_tumor', 'throat_frenulum_tongue']

    temp = validate_request_badania(throat, data_request)

    if len(temp) > 0:
        result += '. Gardło : '
        result += temp

    tooth = ['tooth', 'tooth_paradontic', 'tooth_decay', 'tooth_artificial']

    temp = validate_request_badania(tooth, data_request)

    if len(temp) > 0:
        result += '. Uzębienie : '
        result += temp

    tonsils = ['tonsils', 'tonsils_infection', 'tonsils_hypertrofia', 'tonsils_hypertrofia_asymetria', 'tonsils_angin',
               'tonsils_chronica', 'mononukleoza', 'tonsils_cancer', 'tonsils_brodawczak', 'tonsils_post_excisio']

    temp = validate_request_badania(tonsils, data_request)

    if len(temp) > 0:
        result += '. Migdałki podniebienne : '
        result += temp

    palate_dure = ['palate_dura', 'palate_dura_gothic', 'palate_dura_cleft', 'palate_dura_tumor']

    temp = validate_request_badania(palate_dure, data_request)

    if len(temp) > 0:
        result += '. Podniebienie twarde : '
        result += temp

    palate_soft = ['palate_soft', 'palate_soft_ulvula', 'palate_soft_post_operatio', 'palate_soft_brodawczak',
                   'palate_soft_infiltratio', 'palate_soft_abscesus']

    temp = validate_request_badania(palate_soft, data_request)

    if len(temp) > 0:
        result += '. Podniebienie miękkie : '
        result += temp

    larynx = ['larynx', 'larynx_leukoplakia', 'larynx_nodules', 'larynx_Reinke', 'larynx_cancer', 'larynx_polypus_left',
              'larynx_polypus_right', 'larynx_infection', 'larynx_pachydermia', 'larynx_gerd', 'larynx_paresis_left',
              'larynx_paresis_right', 'larynx_paresis', 'larynx_hypertrofia', 'larynx_infection_chronica',
              'larynx_fungis']

    temp = validate_request_badania(larynx, data_request)

    if len(temp) > 0:
        result += '. Krtań głośnia : '
        result += temp

    larynx_recessus = ['larynx_recessus', 'larynx_recessus_glue', 'larynx_recessus_pus', 'larynx_recessus_blood',
                       'larynx_recessus_cysta', 'larynx_recessus_tumor_right', 'larynx_recessus_tumor_left',
                       'larynx_recessus_corpus_alienum']

    temp = validate_request_badania(larynx_recessus, data_request)

    if len(temp) > 0:
        result += '. Zachyłki gruszkowate krtani : '
        result += temp

    subglotis = ['subglotis', 'subglotis_null', 'subglotis_stenosis', 'subglotis_tumor', 'subglotis_corpus_alienum',
                 'subglotis_polypus']

    temp = validate_request_badania(subglotis, data_request)

    if len(temp) > 0:
        result += '. Okolica podgłośniowa krtani : '
        result += temp

    nos = ['nose', 'nose_post_trauma', 'nose_congenital_malformation', 'nose_nostril_asymetry']

    temp = validate_request_badania(nos, data_request)

    if len(temp) > 0:
        result += '. Nos zewnętrzny : '
        result += temp

    nasal_vestibule = ['nasal_vestibule', 'nasal_vestibule_pus', 'nasal_vestibule_boil', 'nasal_vestibule_blood']

    temp = validate_request_badania(nasal_vestibule, data_request)

    if len(temp) > 0:
        result += '. Przedsionek nosa : '
        result += temp

    nasal_duct = ['nasal_duct', 'nasal_duct_glue', 'nasal_duct_pus', 'nasal_duct_blood']

    temp = validate_request_badania(nasal_duct, data_request)

    if len(temp) > 0:
        result += '. Przewody nosowe : '
        result += temp

    nasal_septum = ['nasal_septum', 'nasal_septum_right', 'nasal_septum_left', 'nasal_septum_all',
                    'nasal_septum_post_operationem', 'nasal_septum_perforation', 'nasal_septum_button']

    temp = validate_request_badania(nasal_septum, data_request)

    if len(temp) > 0:
        result += '. Przegroda nosa : '
        result += temp

    nasal_mucosa = ['nasal_mucosa', 'nasal_mucosa_hyperemia', 'nasal_mucosa_oedema', 'nasal_mucosa_adhesions',
                    'nasal_mucosa_morbus_Rendu', 'nasal_mucosa_infection', 'nasal_mucosa_chronica',
                    'nasal_mucosa_atrofica', 'nasal_mucosa_ozena', 'nasal_mucosa_polyposa', 'nasal_mucosa_fungis',
                    'nasal_mucosa_tumor']

    temp = validate_request_badania(nasal_mucosa, data_request)

    if len(temp) > 0:
        result += '. Błona śluzowa nosa : '
        result += temp

    nasopharynx = ['nasopharynx', 'nasopharynx_adenoid', 'nasopharynx_polypus', 'nasopharynx_tumor',
                   'nasopharynx_glue', 'nasopharynx_pus']

    temp = validate_request_badania(nasopharynx, data_request)

    if len(temp) > 0:
        result += '. Nosowa część gardła : '
        result += temp

    olfaction = ['olfaction', 'olfaction_weakness', 'olfaction_opaque', 'olfaction_null']

    temp = validate_request_badania(olfaction, data_request)

    if len(temp) > 0:
        result += '. Badanie węchu : '
        result += temp

    tuba_auditiva = ['tuba_auditiva', 'tuba_auditiva_left_null', 'tuba_auditiva_right_null', 'tuba_auditiva_null']

    temp = validate_request_badania(tuba_auditiva, data_request)

    if len(temp) > 0:
        result += '. Przedmuch trąbek słuchowych Eustachiusza : '
        result += temp

    auris = ['auris', 'auris_injury_left', 'auris_tumor_left', 'auris_infectionis', 'auris_injury_right',
             'auris_tumor_right', 'auris_pain_left', 'auris_alata', 'auris_abscesus', 'auris_pain_right',
             'auris_congenital_anormaly', 'auris_abscesus_right']

    temp = validate_request_badania(auris, data_request)

    if len(temp) > 0:
        result += '. Małżowiny uszne : '
        result += temp

    auris_externa = ['auris_externa', 'auris_externa_post_operation', 'auris_externa_infectio_right',
                     'auris_externa_infectio_left', 'auris_externa_tumor_right', 'auris_externa_tumor_left']

    temp = validate_request_badania(auris_externa, data_request)

    if len(temp) > 0:
        result += '. Uszy zewnętrzne : '
        result += temp

    aural_duct = ['aural_duct', 'aural_duct_wax_left', 'aural_duct_wax_right', 'aural_duct_tumor',
                  'aural_duct_granulation_left', 'aural_duct_granulation_right', 'aural_duct_egzostozy',
                  'aural_duct_oedema_right', 'aural_duct_oedema_left', 'aural_duct_oedema_all',
                  'aural_duct_mycosis_right', 'aural_duct_mycosis_left', 'aural_duct_blood_left',
                  'aural_duct_blood_right', 'aural_duct_corpus_alienum_left', 'aural_duct_corpus_alienum_right']

    temp = validate_request_badania(aural_duct, data_request)

    if len(temp) > 0:
        result += '. Przewody słuchowe : '
        result += temp

    aural_membrana = ['aural_membrana', 'aural_membrana_perforatio_left', 'aural_membrana_perforatio_right',
                      'aural_membrana_hyperemia_left', 'aural_membrana_hyperemia_right', 'aural_membrana_glue_ear_left',
                      'aural_membrana_glue_ear_right', 'aural_membrana_myringocslerosis_right',
                      'aural_membrana_myringocslerosis_left', 'aural_membrana_ventylation_left',
                      'aural_membrana_ventylation_right', 'aural_membrana_perforatio_post_trauma_left',
                      'aural_membrana_perforatio_post_trauma_right']

    temp = validate_request_badania(aural_membrana, data_request)

    if len(temp) > 0:
        result += '. Błony bębenkowe : '
        result += temp

    balance = ['balance', 'balance_Romberg_right', 'balance_Romberg_left', 'balance_Romberg_back',
               'balance_Unterberger', 'balance_Unterberger_left', 'balance_Unterberger_right',
               'balance_Dix_Hallpike', 'balance_Dix_Hallpike_left', 'balance_Dix_Hallpike_right',
               'balance_Dix_Hallpike_all', 'balance_Dix_Hallpike_central_disorder']

    temp = validate_request_badania(balance, data_request)

    if len(temp) > 0:
        result += '.\n Badanie narządu równowagi : '
        result += temp

    result += '.'

    if data_request['Weber'] != 'nie badano' or data_request['Rinne_left'] != 'nie badano' or \
            data_request['Rinne_right'] != 'nie badano':
        result += ' Badanie Stroikowe : '
        if data_request.get('Weber'):
            result += 'Weber - '
            result += "".join([data_request['Weber'], ', '])

        if data_request.get('Rinne_left'):
            result += 'Rinne lewy - '
            result += "".join([data_request['Rinne_left'], ', '])
        if data_request.get('Bing_left'):
            result += 'Bing lewy - '
            result += "".join([data_request['Bing_left'], ', '])
        if data_request.get('Rinne_right'):
            result += 'Rinne prawy - '
            result += "".join([data_request['Rinne_right'], ', '])
        if data_request.get('Bing_right'):
            result += 'Bing prawy - '
            result += "".join([data_request['Bing_right'], ', '])
    return result


def zalecenia(data_request) -> str:
    lista_zalecen = ['Okresowa kontrola w Poradni Laryngologicznej, ', 'zakaz palenia tytoniu i pochodnych',
                     'oszczędzający głos tryb życia', 'dieta niedrażniąca przewodu pokarmowego',
                     'dieta zbilansowana', 'zakaz czyszczenia uszu patyczkami', 'ochrona uszu przed wodą',
                     'unikanie większego wysiłku fizycznego', 'unikanie osób zainfekowanych',
                     'ochrona okolicy operowanej przed urazem', 'unikanie nadmiernego nasłonecznienia',
                     'przez 30 minut po zabiegu nie jeść i nie pić', 'kontrola po zabiegu celem zdjęcia szwów',
                     'kontrola po zabiegu', 'kontrola celem usunięcia tamponady', 'kontrola z wynikiem badania słuchu',
                     'kontrola z wynikiem badania MRI GŁOWY', ' kontrola z wynikiem badania TK ZATOK',
                     'kontrola z wynikiem badania TK KOŚCI SKRONIOWYCH', 'kontrola z wynikiem badania USG',
                     'kontrola z wynikiem badania BACC', 'kontrola z wynikiem GASTROSKOPII',
                     'kontrola z wynikiem badania VNG', 'kontrola z wynikiem badania POLISOMNOGRAFICZNEGO',
                     'kontrola z wynikiem zleconych badań laboratoryjnych', 'konsultacja i leczenie stomatologiczne',
                     'diagnostyka alergologiczna(testy)', 'konsultacja neurologiczna', 'konsultacja okulistyczna',
                     'konsultacja foniatryczna', 'konsultacja reumatologiczna', 'konsultacja chirurgiczna',
                     'skierowano do szpitala w trybie ostrym !', 'skierowano do szpitala na planowy zabieg !']

    result = lista_zalecen[0]
    lista = data_request.getlist('selectZalecenia')
    for item in lista:
        it = int(item)
        result += lista_zalecen[it - 1] + ', '
    return result


def pesel2birth(pesel):
    """
    Wyznacza datę urodzenia z numeru PESEL.

    :param pesel: Numer PESEL jako string.
    :return: Data urodzenia w formacie 'YYYY-MM-DD'.
    """
    if len(pesel) != 11:
        return "BŁĘDNY PESEL!"

    year = int(pesel[0:2])
    month = int(pesel[2:4])
    day = int(pesel[4:6])

    if 80 <= month <= 99:  # 1800–1899
        year += 1800
        month -= 80
    elif 1 <= month <= 12:  # 1900–1999
        year += 1900
    elif 21 <= month <= 32:  # 2000–2099
        year += 2000
        month -= 20
    elif 41 <= month <= 52:  # 2100–2199
        year += 2100
        month -= 40
    elif 61 <= month <= 72:  # 2200–2299
        year += 2200
        month -= 60
    else:
        return "BŁĘDNY PESEL!"

    try:
        birth_date = datetime(year, month, day).strftime('%Y-%m-%d')
        return birth_date
    except ValueError:
        return "BŁĘDNY PESEL!"


def generate_pdf(data):
    freq_list = ["250", "500", "1000", "2000", "3000", "4000", "6000", "8000"]

    # Przekształcenie na listę
    zabiegi_list = [item.strip() for item in data['zabiegi'].split('\n') if item.strip()]

    def bullet_point(text, bullet='•'):
        pdf.set_x(10)
        pdf.cell(10, 10, bullet)
        pdf.multi_cell(0, 10, text)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Dodanie czcionek obsługujących Unicode
    deja_vu_sans_path = os.path.abspath('./fonts/DejaVuSans.ttf')
    pdf.add_font('DejaVu', '', deja_vu_sans_path, uni=True)

    deja_vu_bold_path = os.path.abspath('./fonts/DejaVuSans-Bold.ttf')
    pdf.add_font('DejaVu-Bold', '', deja_vu_bold_path, uni=True)

    # Nagłówek z datą i miejscem
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10,
                   f"{data['siteZapis'] if data['siteZapis'] != '' else 'Gdańsk'}, dnia {date.today().strftime('%d-%m-%Y')} r.",
                   align='R')
    pdf.ln(10)

    # Dane osobowe
    pdf.set_font("DejaVu-Bold", size=12)
    pdf.cell(0, 10, "Dane osobowe:")
    pdf.ln(6)

    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, f"{data['first_name']} {data['surname']}, ur. {pesel2birth(data['pesel'])}")
    pdf.ln(6)

    address_line = f"{data['city_select']}, {data['street']} {data['home_numer']}".strip(", ")
    pdf.cell(0, 10, address_line)

    pdf.ln(20)

    # Wywiad
    pdf.set_font("DejaVu-Bold", size=12)
    pdf.cell(0, 10, "WYWIAD", align='C')
    pdf.ln(6)
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10, data['wywiad'])

    # Schorzenia ogólne
    if data['ogolne']:
        pdf.set_font("DejaVu-Bold", size=12)
        pdf.cell(0, 10, "Schorzenia ogólne:")
        pdf.ln(6)
        pdf.set_font("DejaVu", size=12)
        pdf.multi_cell(0, 10, data['ogolne'])

    # Schorzenia laryngologiczne
    if data['laryngolog']:
        pdf.set_font("DejaVu-Bold", size=12)
        pdf.cell(0, 10, "Schorzenia laryngologiczne:")
        pdf.ln(6)
        pdf.set_font("DejaVu", size=12)
        pdf.multi_cell(0, 10, data['laryngolog'])

    # Badanie laryngologiczne
    if data['orl']:
        pdf.set_font("DejaVu-Bold", size=12)
        pdf.cell(0, 10, "Badanie laryngologiczne:")
        pdf.ln(6)
        pdf.set_font("DejaVu", size=12)
        pdf.multi_cell(0, 10, data['orl'])

    # Zabiegi
    if zabiegi_list:
        pdf.set_font("DejaVu-Bold", size=12)
        pdf.cell(0, 10, "Zabiegi:")
        pdf.ln(6)
        pdf.set_font("DejaVu", size=12)

        for zabieg in zabiegi_list:
            bullet_point(zabieg)

    # Szept
    if 'szepty' in data and len(data['szepty']) > 11:
        pdf.set_font("DejaVu", size=12)
        pdf.cell(0, 10, f"W dniu {data['szepty']}")
        pdf.ln(10)

    # Audiogram
    if (not any(data.get(f"UL__{freq}") for freq in freq_list) or
            not any(data.get(f"UP__{freq}") for freq in freq_list)):
        pass
    else:
        pdf.set_font("DejaVu-Bold", size=12)
        pdf.cell(0, 10, f"AUDIOGRAM {data['data_audiogramu']}")
        pdf.ln(10)
        pdf.set_font("DejaVu", size=10)
        # Nagłówki tabeli: częstotliwości
        pdf.cell(30, 10, "Hz", 1, 0, "C")  # Pusta komórka (lewa kolumna)
        for freq in freq_list:
            pdf.cell(18, 10, freq, 1, 0, "C")  # Nagłówki z kolejnymi częstotliwościami
        pdf.ln()  # Nowy wiersz

        # Dane dla ucha lewego
        pdf.cell(30, 10, "Ucho lewe", 1, 0, "C")
        for freq in freq_list:
            value = data.get(f"UL__{freq}", "-")  # Pobiera dane dla ucha lewego lub "Brak"
            pdf.cell(18, 10, str(value), 1, 0, "C")
        pdf.ln()  # Nowy wiersz

        # Dane dla ucha prawego
        pdf.cell(30, 10, "Ucho prawe", 1, 0, "C")
        for freq in freq_list:
            value = data.get(f"UP__{freq}", "-")  # Pobiera dane dla ucha prawego lub "Brak"
            pdf.cell(18, 10, str(value), 1, 0, "C")
        pdf.ln(14)

        # Diagnoza
        if data['diagnoza']:
            pdf.set_font("DejaVu-Bold", size=12)
            pdf.cell(0, 10, "DIAGNOZA:")
            pdf.ln(10)
            pdf.set_font("DejaVu", size=12)
            pdf.multi_cell(0, 10, data['diagnoza'])
            pdf.ln(10)

    # Zalecenia
    pdf.set_font("DejaVu-Bold", size=12)
    pdf.cell(0, 10, "ZALECENIA:")
    pdf.ln(10)
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10, data['zalecenie'])

    # Podpis
    pdf.ln(10)
    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 10, "podpis i pieczątka", align='R')

    return pdf.output(dest='S').encode('latin1')


def walidacja_pesela(pesel):
    """
    :param pesel: The PESEL number to be validated as a string of digits.
    :return: True if the PESEL is valid, False otherwise.
    """
    # Sprawdzamy, czy PESEL ma dokładnie 11 cyfr i czy znaki są cyframi
    if len(pesel) != 11 or not pesel.isdigit():
        return False
    # Wagi dla pozycji PESEL-a
    wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    # Obliczamy sumę kontrolną
    suma = sum(int(pesel[i]) * wagi[i] for i in range(10))
    # Cyfra kontrolna to ostatnia cyfra PESEL-a
    cyfra_kontrolna = (10 - suma % 10) % 10
    # Sprawdzamy, czy cyfra kontrolna zgadza się z ostatnią cyfrą PESEL-a
    return cyfra_kontrolna == int(pesel[10])


def object_to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


# Funkcja czyta międzynarodową klasyfikację chorób ICD-10
def get_icd_10():
    try:
        with open('instance/icd_10.txt', 'r', encoding="utf-8") as file:
            get_data_icd_10 = file.readlines()
    except FileNotFoundError:
        print("Error: Specified file does not exist.")
        return []
    except IOError as e:
        print(f"Error: Unable to read the file. Details: {e}")
        return []
    return get_data_icd_10


# Sprawdzenie i przygotowanie danych audiogramu
def prepare_audiogram_data(dane):
    if not dane.get("data_audiogramu"):
        return None, {}

    data_audiogramu = datetime.strptime(dane.get("data_audiogramu"), "%Y-%m-%d")
    pola_audiogramu = {f"{prefix}_{hz}": dane.get(f"{prefix.upper()}__{hz}")
                       for prefix in ('ul', 'up')
                       for hz in ('250', '500', '1000', '2000', '3000', '4000', '6000', '8000')}
    if any(pola_audiogramu.values()):
        return data_audiogramu, pola_audiogramu
    return None, {}


def save_visit_to_db(data, user_id):
    """
    Zapisuje dane wizyty do bazy danych.

    :param data: Dane przesłane z formularza
    :param user_id: ID użytkownika wykonującego operację
    :return: Obiekt zapisanej wizyty
    :raises: IntegrityError, Exception
    """
    try:
        # Płeć na podstawie PESEL
        pesel = data.get("pesel")
        if not pesel or len(pesel) != 11:
            raise ValueError("Nieprawidłowy PESEL.")

        gender = 'M' if int(pesel[10]) % 2 else 'K'

        # Pobranie lub stworzenie pacjenta
        hidden_result_input = data.get("hiddenResultInput")
        if hidden_result_input:
            try:
                patient_id = int(hidden_result_input)
            except ValueError:
                raise ValueError("Nieprawidłowy ID pacjenta w hiddenResultInput.")
        else:
            patient = db.session.execute(
                db.select(Patient).filter_by(pesel=pesel)
            ).scalar_one_or_none()

            if not patient:
                patient = Patient(
                    first_name=data.get("first_name"),
                    surname=data.get("surname"),
                    pesel=pesel,
                    gender=gender,
                    state=data.get("wojewodztwo"),
                    city=data.get("city_select"),
                    street=data.get("street"),
                    apartment_number=data.get("home_numer")
                )
                db.session.add(patient)
                db.session.commit()
            patient_id = patient.id

        audiogram_date, audiogram_values = prepare_audiogram_data(data)

        # Zapis wizyty
        new_visit = Visit(
            user_id=user_id,
            patient_id=patient_id,
            diagnosis=data.get('diagnoza'),
            location=data.get('siteZapis'),
            interview=data.get('wywiad'),
            general_info=data.get('ogolne'),
            orl=data.get('orl'),
            examination=data.get('laryngolog'),
            recommendations=data.get('zalecenie'),
            whisper_test=data.get('szepty'),
            nfz_info=data.get('kody_nfz'),
            examination_date=date.today(),
            routine=data.get('zabiegi')
        )
        db.session.add(new_visit)
        db.session.commit()

        # Zapis audiogramu (jeśli są dane)
        if audiogram_date:
            new_audiogram = Audiogram(
                patient_id=patient_id,
                visit_id=new_visit.id,
                audiogram_date=audiogram_date,
                **{key: value for key, value in audiogram_values.items() if value is not None}
            )
            db.session.add(new_audiogram)
            db.session.commit()

        return new_visit
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"IntegrityError: {e}")
        raise e
    except ValueError as ve:
        logging.error(f"Błąd walidacji danych: {ve}")
        raise ve
    except Exception as e:
        db.session.rollback()
        logging.error(f"Nieoczekiwany błąd: {e}")
        raise e


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
    :param start_date: Optional start date to filter the data by created_at (string 'yyyy-mm-dd').
    :param end_date: Optional end date to filter the data by created_at (string 'yyyy-mm-dd').
    :return: DataFrame with grouped and aggregated data, including a summary row.
    """
    try:
        # Konwertujemy daty na obiekty datetime.date
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Sprawdzamy i konwertujemy kolumnę created_at, jeśli wymaga konwersji
        if not pd.api.types.is_datetime64_any_dtype(df['created_at']):
            df['created_at'] = pd.to_datetime(df['created_at']).dt.date

        # Filtrujemy dane na podstawie zakresu dat
        if start_date or end_date:
            mask = True
            if start_date:
                mask &= df['created_at'] >= start_date
            if end_date:
                mask &= df['created_at'] <= end_date
            df = df[mask]

        # Sprawdzamy poprawność selected_types
        if isinstance(selected_types, str) and selected_types.strip().lower() == "all":
            # Jeśli selected_types to pojedynczy string "all"
            grouped = df.groupby(["created_at", "first_name", "surname", "city", "info"]).agg(
                num_examinations=("created_at", "size"),
                able_to_work=("is_able_to_work", "sum")
            ).reset_index()
        elif isinstance(selected_types, list) and "all" in selected_types:
            # Jeśli selected_types to lista zawierająca "all"
            grouped = df.groupby(["created_at", "first_name", "surname", "city", "info"]).agg(
                num_examinations=("created_at", "size"),
                able_to_work=("is_able_to_work", "sum")
            ).reset_index()
        else:
            try:
                # Próba konwersji wartości na int
                selected_types_int = [int(t) for t in selected_types]
            except (ValueError, TypeError) as e:
                raise ValueError(
                    "Invalid `selected_types`. Must be a list containing integers or the string 'all'."
                ) from e

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

    except Exception as e:
        raise Exception("An error occurred during processing.") from e



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
    pivot_df = df.pivot_table(index='created_at', columns='type', values='count', aggfunc='sum', fill_value=0)

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

def process_selected_types(raw_types):
    """
    Processes and cleans selected types list by:
    - Parsing any string representations of lists.
    - Removing duplicates, preserving order.
    - Discarding 'all' if other entries exist.
    :param raw_types: List[str] - Raw list of selected types input.
    :return: List[str] - Processed list of selected types.
    """
    # Parse the selected types from input
    parsed_types = []
    for item in raw_types:
        try:
            if isinstance(item, str) and item.startswith('[') and item.endswith(']'):
                parsed_types.extend(ast.literal_eval(item))
            else:
                parsed_types.append(item)
        except (ValueError, SyntaxError) as e:
            logging.warning(f"Failed to parse selected_types item: {item}. Error: {e}")
            parsed_types.append(item)

    # Clean the parsed list: remove 'all' and duplicates
    if 'all' in parsed_types and len(parsed_types) > 1:
        parsed_types = [typ for typ in parsed_types if typ != 'all']
    return list(dict.fromkeys(parsed_types))


def handle_form_request():
    """
    Handles logic for processing selected types from the form.
    :return: List[str] - Processed selected types.
    """
    raw_types = request.form.getlist("selected_types")
    return process_selected_types(raw_types) if raw_types else ['all']
