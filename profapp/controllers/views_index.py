from flask import render_template, request, session, redirect, url_for, g, flash
from .blueprints_declaration import general_bp
from flask.ext.login import login_required
from ..models.portal import Portal, UserPortalReader, ReaderUserPortalPlan
from profapp.controllers.errors import BadDataProvided
from utils.email import email_send


@general_bp.route('help/')
def help():
    return render_template('help.html')


@general_bp.route('')
def index():
    return render_template('general/index.html')


@general_bp.route('portals_list/')
def portals_list():
    portals = [(id, name) for id, name in UserPortalReader.get_portals_for_user()]
    return render_template('general/portals_list.html', portals=portals)


@general_bp.route('subscribe/')
def auth_before_subscribe_to_portal():
    portal_id = request.args.get('portal_id', None)
    session['portal_id'] = portal_id
    return redirect(url_for('auth.login_signup_endpoint', login_signup='login'))


@general_bp.route('send_email_create_portal/')
@login_required
def send_email_create_portal():
    return render_template('general/send_email_create_portal.html')


@general_bp.route('send_email', methods=['POST'])
def send_email():
    return email_send(**{name: str(val) for name, val in request.form.items()})
