from flask import Blueprint, render_template, abort, request, flash
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

from app import verify_csrf_token

antibiotic_bp = Blueprint('antibiotic', __name__)

# Funkcja zwraca wagę po oczyszczeniu z tekstu
def parse_weight(weight):
    try:
        return float(weight.replace(',', '.'))
    except (ValueError, AttributeError):
        return None

@antibiotic_bp.route('/antibiotic', methods=['GET'])
@login_required
def antibiotic_main():
    try:
        return render_template('antibiotic.html', user=current_user.login, skok='start')
    except TemplateNotFound:
        return abort(404)


@antibiotic_bp.route('/calculations', methods=['POST'])
@login_required
def calculations():
    try:
        dawka_augmentin = dawka_sumamed = dawka_levoxa = dawka_duracef = dawka_zinnat = dawka_cetix = None

        mnoznik_map = {
            'inputGroupSelect02': {'1': 200, 'default': 100},
            'inputGroupSelect04': {'2': 500, '3': 500, 'default': 250},
            'inputGroupSelect05': {'2': 250, 'default': 125}
        }

        waga_augmentin = parse_weight(request.form.get('waga_augmentin', ''))
        waga_sumamed = parse_weight(request.form.get('waga_sumamed', ''))
        waga_levoxa = parse_weight(request.form.get('waga_levoxa', ''))
        waga_duracef = parse_weight(request.form.get('waga_duracef', ''))
        waga_zinnat = parse_weight(request.form.get('waga_zinnat', ''))
        waga_cetix = parse_weight(request.form.get('waga_cetix', ''))

        missing_weights = [waga_augmentin, waga_sumamed, waga_levoxa, waga_duracef, waga_zinnat, waga_cetix]
        masa_zero = sum(1 for weight in missing_weights if not weight)

        if waga_augmentin:
            ile = (waga_augmentin * 90.0 * 0.5 ) / 120.0
            dawka_augmentin = f'{ile:.1f} ml / 2 x dobę'

        mnoznik = mnoznik_map['inputGroupSelect02'].get(request.form.get('inputGroupSelect02', 'default'), 100)
        if waga_sumamed:
            ile = (waga_sumamed * 10.0 / mnoznik) * 5
            dawka_sumamed = f'{ile:.1f} ml / 1 x dobę'

        if waga_levoxa:
            dawka_levoxa = '2 x 1 na dobę'

        mnoznik = mnoznik_map['inputGroupSelect04'].get(request.form.get('inputGroupSelect04', 'default'), 250)
        if waga_duracef:
            if float(waga_duracef) < 40.0:
                ile = ((waga_duracef * 25.0) / mnoznik) * 2.5
                ile_2 = ile * 2
                dawka_duracef = f'{ile:.1f}-{ile_2:.1f} ml / 2 x dobę'
            if 40 <= waga_duracef <= 70:
                dawka_duracef = '1 x 1 g'
            if waga_duracef > 70.0:
                dawka_duracef = '2 x 1 g'

        mnoznik = mnoznik_map['inputGroupSelect05'].get(request.form.get('inputGroupSelect05', 'default'), 125)
        if waga_zinnat:
            if float(waga_zinnat) < 40.0:
                ile = ((waga_zinnat * 15.0) / mnoznik) * 2.5
                dawka_zinnat = f'{ile:.1f} ml / 2 x dobę'
            if 40 <= waga_zinnat <= 70.0:
                dawka_zinnat = '2 x 250 mg'
            if waga_zinnat > 70.0:
                dawka_zinnat = '2 x 500 mg'

        if waga_cetix:
            ile = ((waga_cetix * 8.0) / 100) * 5
            polowa = ile * 0.5
            dawka_cetix = f'1x {ile:.1f} - 2x {polowa:.1f} ml/dobę'
            if waga_cetix >= 50:
                dawka_cetix = '1x1 lub 2x 1/2 tabl./dobę'

        if masa_zero == 6:
            flash('Nie podano nigdzie masy ciała pacjenta !', 'danger')

        skok = 'koniec' if any([waga_duracef, waga_zinnat, waga_cetix]) else 'start'

        return render_template('antibiotic.html',
                               user=current_user.login,
                               skok=skok,
                               waga_augmentin=waga_augmentin, dawka_augmentin=dawka_augmentin,
                               select_01=request.form.get('inputGroupSelect01'),
                               waga_sumamed=waga_sumamed, dawka_sumamed=dawka_sumamed,
                               select_02=request.form.get('inputGroupSelect02'),
                               waga_levoxa=waga_levoxa, dawka_levoxa=dawka_levoxa,
                               select_03=request.form.get('inputGroupSelect03'),
                               waga_duracef=waga_duracef, dawka_duracef=dawka_duracef,
                               select_04=request.form.get('inputGroupSelect04'),
                               waga_zinnat=waga_zinnat, dawka_zinnat=dawka_zinnat,
                               select_05=request.form.get('inputGroupSelect05'),
                               waga_cetix=waga_cetix, dawka_cetix=dawka_cetix,
                               select_06=request.form.get('inputGroupSelect06')
        )
    except TemplateNotFound:
        return abort(404)
