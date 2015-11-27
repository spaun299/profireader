from flask import render_template, jsonify, request, session, redirect, url_for, g
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


def get_params(portal_id, **argv):
    portal = g.db.query(Portal).filter_by(id=portal_id).one()
    sub_query = Article.subquery_articles_at_portal(search_text='', portal_id=portal.id)
    return portal, sub_query


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
@general_bp.route('<int:page>/', methods=['GET'])
def index(page=1):
    if not current_user.is_authenticated():
        portal_base_profireader = 'partials/portal_base_Profireader.html'
        profireader_content = 'partials/Profireader_content.html'
        head = 'partials/empty_page.html'
        return render_template('general/index.html',
                               portal_base_profireader=portal_base_profireader,
                               profireader_content=profireader_content,
                               add_head=head
                               )

    # user_portal_reader = g.db.query(UserPortalReader).filter_by(user_id=g.user_dict['id']).all()

    sub_query = g.db.query(ArticlePortalDivision).\
        filter_by(status=ARTICLE_STATUS_IN_PORTAL.published).\
        join(PortalDivision).\
        join(Portal).\
        join(UserPortalReader).\
        filter(UserPortalReader.user_id==g.user_dict['id']).\
        order_by(ArticlePortalDivision.publishing_tm.desc()).\
        filter(text(' "publishing_tm" < clock_timestamp() '))

    # search_text, portal, sub_query = get_params()
    articles, pages, page = pagination(query=sub_query, page=page)

    ordered_articles = OrderedDict()
    for a in articles:
        ordered_articles[a.id] = dict(list(a.get_client_side_dict().items()) +
                                      list({'tags': a.tags}.items()))

    portal_base_profireader = 'partials/portal_base_Profireader_auth_user.html'
    profireader_content = 'partials/reader/reader_content.html'
    head = 'partials/reader/head.html'
    # head = 'partials/empty_page.html'

    return render_template('general/index.html',
                           portal_base_profireader=portal_base_profireader,
                           profireader_content=profireader_content,
                           add_head=head,
                           articles=ordered_articles,
                           pages=pages,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
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

    # user_portal_reader = g.db(UserPortalReader).filter_by(user_id=user_dict['id'], portal_id=portal_id).first()
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

    return redirect(url_for('general.index'))
