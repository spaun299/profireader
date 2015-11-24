from .blueprints_declaration import front_bp
from flask import render_template, request, url_for, redirect, g, current_app
from ..models.articles import Article, ArticlePortalDivision, ArticleCompany
from ..models.portal import MemberCompanyPortal, PortalDivision, Portal, Company, \
    PortalDivisionSettings_company_subportal
from utils.db_utils import db
from ..models.users import User
from ..models.company import UserCompany

from config import Config
# from profapp import
from .pagination import pagination
from sqlalchemy import Column, ForeignKey, text
import os
from flask import send_from_directory
import collections


def get_division_for_subportal(portal_id, member_company_id):
    q = g.db().query(PortalDivisionSettings_company_subportal). \
        join(MemberCompanyPortal,
             MemberCompanyPortal.id == PortalDivisionSettings_company_subportal.member_company_portal_id). \
        join(PortalDivision,
             PortalDivision.id == PortalDivisionSettings_company_subportal.portal_division_id). \
        filter(MemberCompanyPortal.company_id == member_company_id). \
        filter(PortalDivision.portal_id == portal_id)

    PortalDivisionSettings = q.all()
    if (len(PortalDivisionSettings)):
        return PortalDivisionSettings[0]
    else:
        return g.db().query(PortalDivision).filter_by(portal_id=portal_id,
                                                      portal_division_type_id='index').one()


def get_params(**argv):
    search_text = request.args.get('search_text') if request.args.get('search_text') else ''
    app = current_app._get_current_object()
    portal = g.db().query(Portal).filter_by(host=app.config['SERVER_NAME']).one()

    sub_query = Article.subquery_articles_at_portal(search_text=search_text, portal_id=portal.id)
    return search_text, portal, sub_query


def portal_and_settings(portal):
    ret = portal.get_client_side_dict()
    newd = []
    for di in ret['divisions']:
        if di['portal_division_type_id'] == 'company_subportal':
            pdset = g.db().query(PortalDivisionSettings_company_subportal). \
                filter_by(portal_division_id=di['id']).one()
            com_port = g.db().query(MemberCompanyPortal).get(pdset.member_company_portal_id)
            di['member_company'] = Company.get(com_port.company_id)
        newd.append(di)
    ret['divisions'] = newd
    return ret


@front_bp.route('favicon.ico')
def favicon():
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@front_bp.route('/', methods=['GET'])
@front_bp.route('<int:page>/', methods=['GET'])
def index(page=1):
    search_text, portal, sub_query = get_params()
    division = g.db().query(PortalDivision).filter_by(portal_id=portal.id,
                                                      portal_division_type_id='index').one()
    articles, pages, page = pagination(query=sub_query, page=page)

    ordered_articles = collections.OrderedDict()
    for a in articles:
        ordered_articles[a.id] = dict(list(a.get_client_side_dict().items()) +
                                      list({'tags': a.tags}.items()))

    return render_template('front/bird/index.html',
                           articles=ordered_articles,
                           portal=portal_and_settings(portal),
                           current_division=division.get_client_side_dict(),
                           pages=pages,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
                           search_text=search_text)


@front_bp.route('<string:division_name>/', methods=['GET'])
@front_bp.route('<string:division_name>/<int:page>/', methods=['GET'])
def division(division_name, page=1):
    search_text, portal, sub_query = get_params()
    division = g.db().query(PortalDivision).filter_by(portal_id=portal.id, name=division_name).one()
    if division.portal_division_type_id == 'catalog' and search_text:
        return redirect(url_for('front.index', search_text=search_text))
    if division.portal_division_type_id == 'news' or division.portal_division_type_id == 'events':
        sub_query = Article.subquery_articles_at_portal(search_text=search_text,
                                                        portal_division_id=division.id)
        articles, pages, page = pagination(query=sub_query, page=page)
        ordered_articles = collections.OrderedDict()
        for a in articles:
            ordered_articles[a.id] = a.get_client_side_dict()

        return render_template('front/bird/division.html',
                               articles=ordered_articles,
                               current_division=division.get_client_side_dict(),
                               portal=portal_and_settings(portal),
                               pages=pages,
                               current_page=page,
                               page_buttons=Config.PAGINATION_BUTTONS,
                               search_text=search_text)

    elif division.portal_division_type_id == 'catalog':

        # sub_query = Article.subquery_articles_at_portal(search_text=search_text,
        # articles, pages, page = pagination(query=sub_query, page=page)

        members = {member.id: member.company.get_client_side_dict() for
                   member in division.portal.company_members}

        return render_template('front/bird/catalog.html',
                               members=members,
                               current_division=division.get_client_side_dict(),
                               portal=portal_and_settings(portal))

    else:
        return 'unknown division.portal_division_type_id = %s' % (division.portal_division_type_id,)


# TODO OZ by OZ: portal filter, move portal filtering to decorator

@front_bp.route('details/<string:article_portal_division_id>')
def details(article_portal_division_id):
    search_text, portal, sub_query = get_params()

    article = ArticlePortalDivision.get(article_portal_division_id)
    article_dict = article.to_dict('id, title,short, cr_tm, md_tm, '
                                   'publishing_tm, keywords, status, long, image_file_id,'
                                   'division.name, division.portal.id,'
                                   'company.name')
    article_dict['tags'] = article.tags

    division = g.db().query(PortalDivision).filter_by(id=article.portal_division_id).one()

    related_articles = g.db().query(ArticlePortalDivision).filter(
        division.portal.id == article.division.portal_id).order_by(
        ArticlePortalDivision.cr_tm.desc()).limit(10).all()

    return render_template('front/bird/article_details.html',
                           portal=portal_and_settings(portal),
                           current_division=division.get_client_side_dict(),
                           articles_related={a.id: a.to_dict('id, title, cr_tm, company.name|id') for a
                                             in related_articles},
                           article=article_dict
                           )


@front_bp.route(
    '<string:division_name>/_c/<string:member_company_id>/<string:member_company_name>/')
@front_bp.route(
    '<string:division_name>/_c/<string:member_company_id>/<string:member_company_name>/<int:page>/')
def subportal_division(division_name, member_company_id, member_company_name, page=1):
    member_company = Company.get(member_company_id)

    search_text, portal, sub_query = get_params()

    division = get_division_for_subportal(portal.id, member_company_id)

    subportal_division = g.db().query(PortalDivision).filter_by(portal_id=portal.id,
                                                                name=division_name).one()

    sub_query = Article.subquery_articles_at_portal(
        search_text=search_text,
        portal_division_id=subportal_division.id). \
        filter(db(ArticleCompany,
                  company_id=member_company_id,
                  id=ArticlePortalDivision.article_company_id).exists())
    # filter(Company.id == member_company_id)

    articles, pages, page = pagination(query=sub_query, page=page)
    ordered_articles = collections.OrderedDict()
    for a in articles:
        ordered_articles[a.id] = a.get_client_side_dict()

    return render_template('front/bird/subportal_division.html',
                           articles=ordered_articles,
                           subportal=True,
                           portal=portal_and_settings(portal),
                           current_division=division.get_client_side_dict(),
                           current_subportal_division=subportal_division.get_client_side_dict(),
                           member_company=member_company.get_client_side_dict(),
                           pages=False,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
                           search_text=search_text)


@front_bp.route('_c/<string:member_company_id>/<string:member_company_name>/')
def subportal(member_company_id, member_company_name, page=1):
    search_text, portal, sub_query = get_params()
    if search_text:
        return redirect(url_for('front.index', search_text=search_text))

    member_company = Company.get(member_company_id)

    division = get_division_for_subportal(portal.id, member_company_id)

    subportal_division = g.db().query(PortalDivision).filter_by(portal_id=portal.id,
                                                                portal_division_type_id='index').one()

    return render_template('front/bird/subportal.html',
                           subportal=True,
                           portal=portal_and_settings(portal),
                           current_division=division.get_client_side_dict(),
                           current_subportal_division=subportal_division.get_client_side_dict(),
                           member_company=member_company.get_client_side_dict(),
                           current_subportal_division_name='index',
                           pages=False,
                           # current_page=page,
                           # page_buttons=Config.PAGINATION_BUTTONS,
                           # search_text=search_text
                           )


@front_bp.route('_c/<string:member_company_id>/<string:member_company_name>/address/')
def subportal_address(member_company_id, member_company_name):
    search_text, portal, sub_query = get_params()

    member_company = Company.get(member_company_id)

    division = get_division_for_subportal(portal.id, member_company_id)

    return render_template('front/bird/subportal_address.html',
                           subportal=True,
                           portal=portal_and_settings(portal),
                           current_division=division.get_client_side_dict(),
                           current_subportal_division=False,
                           current_subportal_division_name='address',
                           member_company=member_company.get_client_side_dict(),
                           pages=False,
                           # current_page=page,
                           # page_buttons=Config.PAGINATION_BUTTONS,
                           # search_text=search_text
                           )


@front_bp.route('_c/<string:member_company_id>/<string:member_company_name>/contacts/')
def subportal_contacts(member_company_id, member_company_name):
    search_text, portal, sub_query = get_params()

    member_company = Company.get(member_company_id)

    division = get_division_for_subportal(portal.id, member_company_id)

    company_users = member_company.employees

    # TODO: AA by OZ: remove this. llok also for ERROR employees.position.2
    # ERROR employees.position.2#
    def getposition(u_id, c_id):
        r = db(UserCompany, user_id=u_id, company_id=c_id).first()
        return r.position if r else ''

    return render_template('front/bird/subportal_contacts.html',
                           subportal=True,
                           company_users={
                           u.id: dict(u.get_client_side_dict(), position=getposition(u.id, member_company_id)) for u in
                           company_users},
                           portal=portal_and_settings(portal),
                           current_division=division.get_client_side_dict(),
                           current_subportal_division=False,
                           current_subportal_division_name='contacts',
                           member_company=member_company.get_client_side_dict(),
                           pages=False,
                           # current_page=page,
                           # page_buttons=Config.PAGINATION_BUTTONS,
                           # search_text=search_text
                           )
