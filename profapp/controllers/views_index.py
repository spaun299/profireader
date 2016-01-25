from flask import render_template, jsonify, request, session, redirect, url_for, g, flash
from .blueprints_declaration import general_bp
from flask.ext.login import current_user, login_required
from ..models.portal import Portal, UserPortalReader, ReaderUserPortalPlan, PortalDivision
from ..models.articles import Article, ArticlePortalDivision
from config import Config
from profapp.controllers.errors import BadDataProvided
from .pagination import pagination
from collections import OrderedDict
from ..constants.ARTICLE_STATUSES import ARTICLE_STATUS_IN_PORTAL
from sqlalchemy import text
from utils.db_utils import db

# def get_params(portal_id, **argv):
#     portal = g.db.query(Portal).filter_by(id=portal_id).one()
#     sub_query = Article.subquery_articles_at_portal(search_text='', portal_id=portal.id)
#     return portal, sub_query


# def subquery_articles_at_portal(search_text=None, **kwargs):
#     portal_id = None
#     if 'portal_id' in kwargs.keys():
#         portal_id = kwargs['portal_id']
#         kwargs.pop('portal_id', None)
#
#     sub_query = db(ArticlePortalDivision, status=ARTICLE_STATUS_IN_PORTAL.published, **kwargs). \
#         order_by(ArticlePortalDivision.publishing_tm.desc()).filter(text(' "publishing_tm" < clock_timestamp() '))
#
#     if portal_id:
#         sub_query = sub_query.join(PortalDivision).join(Portal).filter(Portal.id == portal_id)
#
#     if search_text:
#         sub_query = sub_query. \
#             filter(or_(ArticlePortalDivision.title.ilike("%" + search_text + "%"),
#                        ArticlePortalDivision.short.ilike("%" + search_text + "%"),
#                        ArticlePortalDivision.long_stripped.ilike("%" + search_text + "%")))
#     return sub_query


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
