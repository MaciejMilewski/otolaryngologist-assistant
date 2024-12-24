from flask import Blueprint, render_template, abort, flash
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound

from app import db
from app.models import Procedure

visit_bp = Blueprint('visit', __name__)


@visit_bp.route('/visit', methods=['GET'])
@login_required
def main_form():
    try:
        zabiegi = db.session.query(Procedure).all()
        return render_template('visit.html', user=current_user.login, zabiegi=zabiegi)
    except TemplateNotFound:
        return abort(404)


@visit_bp.route('/generuj', methods=['GET'])  # GENERUJ, podstawienie właściwego pliku html
@login_required
def generuj():
    try:
        pass
        return "generuj ..."

    except TemplateNotFound:
        return abort(404)
