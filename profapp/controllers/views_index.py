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


@general_bp.route('subscribe/<string:portal_id>')
@login_required
def reader_subscribe(portal_id):
    user_dict = g.user_dict
    portal = Portal.get(portal_id)
    if not portal:
        raise BadDataProvided

    user_portal_reader = g.db.query(UserPortalReader).filter_by(user_id=user_dict['id'], portal_id=portal_id).first()
    if not user_portal_reader:
        user_portal_reader = UserPortalReader(
            user_dict['id'],
            portal_id,
            status='active',
            portal_plan_id=g.db.query(ReaderUserPortalPlan.id).filter_by(name='free').one()[0]
        )
        g.db.add(user_portal_reader)
        g.db.commit()
        flash('You have successfully subscribed to this portal')

    return redirect(url_for('general.index'))


@general_bp.route('send_email_create_portal/')
@login_required
def send_email_create_portal():
    return render_template('general/send_email_create_portal.html')


@general_bp.route('send_email', methods=['POST'])
def send_email():
    return email_send(**{name: str(val) for name, val in request.form.items()})
