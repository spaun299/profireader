from flask import render_template, redirect, url_for, request, g
from .blueprints_declaration import general_bp
from flask.ext.login import current_user, login_required


@general_bp.route('')
def index():
    if current_user.is_authenticated():
        portal_base_profireader = 'partials/portal_base_Profireader_auth_user.html'
        profireader_content = 'partials/reader/reader_content.html'
    else:
        portal_base_profireader = 'partials/portal_base_Profireader.html'
        profireader_content = 'partials/Profireader_content.html'

    return render_template('general/index.html',
                           portal_base_profireader=portal_base_profireader,
                           profireader_content=profireader_content
                           )


@general_bp.route('/subscribe/<string:portal_id>')
@login_required
def reader_subscribe(portal_id):
    # TODO (AA to AA): code here.
    # portal_id = request.args.get('subscribe', None)
    print('here a subscription must be done')
    return redirect(url_for('general.index'))
