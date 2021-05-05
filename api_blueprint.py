from flask import Blueprint, url_for, redirect, abort, render_template
from flask_login import current_user, login_required
from data.models import *

blueprint = Blueprint('api', __name__)

@blueprint.route('/api')
@login_required
def api_description():
    return render_template('api.html', title='API')

