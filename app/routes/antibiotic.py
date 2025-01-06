from flask import Blueprint, render_template, abort, request, flash
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from app.utils.utils import parse_weight

antibiotic_bp = Blueprint('antibiotic', __name__)


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
        dose_augmentin = dose_sumamed = dose_levoxa = dose_duracef = dose_zinnat = dose_cetix = None

        multiplier_map = {
            'inputGroupSelect02': {'1': 200, 'default': 100},
            'inputGroupSelect04': {'2': 500, '3': 500, 'default': 250},
            'inputGroupSelect05': {'2': 250, 'default': 125}
        }

        weight_augmentin = parse_weight(request.form.get('waga_augmentin', ''))
        weight_sumamed = parse_weight(request.form.get('waga_sumamed', ''))
        weight_levoxa = parse_weight(request.form.get('waga_levoxa', ''))
        weight_duracef = parse_weight(request.form.get('waga_duracef', ''))
        weight_zinnat = parse_weight(request.form.get('waga_zinnat', ''))
        weight_cetix = parse_weight(request.form.get('waga_cetix', ''))

        missing_weights = [weight_augmentin, weight_sumamed, weight_levoxa, weight_duracef, weight_zinnat, weight_cetix]
        mass_zero = sum(1 for weight in missing_weights if not weight)

        if weight_augmentin:
            how_many = (weight_augmentin * 90.0 * 0.5 ) / 120.0
            dose_augmentin = f'{how_many:.1f} ml / 2 x dobę'

        mnoznik = multiplier_map['inputGroupSelect02'].get(request.form.get('inputGroupSelect02', 'default'), 100)
        if weight_sumamed:
            how_many = (weight_sumamed * 10.0 / mnoznik) * 5
            dose_sumamed = f'{how_many:.1f} ml / 1 x dobę'

        if weight_levoxa:
            dose_levoxa = '2 x 1 na dobę'

        mnoznik = multiplier_map['inputGroupSelect04'].get(request.form.get('inputGroupSelect04', 'default'), 250)
        if weight_duracef:
            if float(weight_duracef) < 40.0:
                how_many = ((weight_duracef * 25.0) / mnoznik) * 2.5
                how_many_2 = how_many * 2
                dose_duracef = f'{how_many:.1f}-{how_many_2:.1f} ml / 2 x dobę'
            if 40 <= weight_duracef <= 70:
                dose_duracef = '1 x 1 g'
            if weight_duracef > 70.0:
                dose_duracef = '2 x 1 g'

        mnoznik = multiplier_map['inputGroupSelect05'].get(request.form.get('inputGroupSelect05', 'default'), 125)
        if weight_zinnat:
            if float(weight_zinnat) < 40.0:
                how_many = ((weight_zinnat * 15.0) / mnoznik) * 2.5
                dose_zinnat = f'{how_many:.1f} ml / 2 x dobę'
            if 40 <= weight_zinnat <= 70.0:
                dose_zinnat = '2 x 250 mg'
            if weight_zinnat > 70.0:
                dose_zinnat = '2 x 500 mg'

        if weight_cetix:
            how_many = ((weight_cetix * 8.0) / 100) * 5
            half_dose = how_many * 0.5
            dose_cetix = f'1x {how_many:.1f} - 2x {half_dose:.1f} ml/dobę'
            if weight_cetix >= 50:
                dose_cetix = '1x1 lub 2x 1/2 tabl.'

        if mass_zero == 6:
            flash('Nie podano nigdzie masy ciała pacjenta !', 'danger')

        jump = 'the_end' if any([weight_duracef, weight_zinnat, weight_cetix]) else 'start'

        return render_template('antibiotic.html',
                               user=current_user.login,
                               skok=jump,
                               waga_augmentin=weight_augmentin, dawka_augmentin=dose_augmentin,
                               select_01=request.form.get('inputGroupSelect01'),
                               waga_sumamed=weight_sumamed, dawka_sumamed=dose_sumamed,
                               select_02=request.form.get('inputGroupSelect02'),
                               waga_levoxa=weight_levoxa, dawka_levoxa=dose_levoxa,
                               select_03=request.form.get('inputGroupSelect03'),
                               waga_duracef=weight_duracef, dawka_duracef=dose_duracef,
                               select_04=request.form.get('inputGroupSelect04'),
                               waga_zinnat=weight_zinnat, dawka_zinnat=dose_zinnat,
                               select_05=request.form.get('inputGroupSelect05'),
                               waga_cetix=weight_cetix, dawka_cetix=dose_cetix,
                               select_06=request.form.get('inputGroupSelect06')
        )
    except TemplateNotFound:
        return abort(404)
