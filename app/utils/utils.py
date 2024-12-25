from datetime import datetime
from sqlalchemy import and_, or_

from app.models import Schedule


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
