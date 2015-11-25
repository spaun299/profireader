from flask import render_template, jsonify, request, session, redirect, url_for, g
from .blueprints_declaration import general_bp
from flask.ext.login import current_user, login_required
from ..models.portal import Portal
from profapp.controllers.errors import BadDataProvided


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


@general_bp.route('subscribe/')
def auth_before_subscribe_to_portal():
    portal_id = request.args.get('portal_id', None)
    session['portal_id'] = portal_id
    return redirect(url_for('auth.login_signup_endpoint', login_signup='login'))


@general_bp.route('subscribe/<string:portal_id>')
@login_required
def reader_subscribe(portal_id):
    user_dict = g.user_dict
    portal = Portal.get(portal_id)
    if not portal:
        raise BadDataProvided
    # TODO (AA to AA): code here.
    return jsonify({'portal_id': portal_id})
