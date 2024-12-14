from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound
from werkzeug.security import check_password_hash

from app.models import User

auth_bp = Blueprint('auth', __name__)

# W template url_for('nazwa_blueprint.nazwa_funkcji_z_route')
# W funkcji z route return return render_template('nazwa_template')
# W funkcji z route w rule 'adres url jaki ma się wyświetlić'


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        return render_template('home.html')
    except TemplateNotFound:
        return abort(404)
