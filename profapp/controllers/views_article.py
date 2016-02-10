from flask import render_template, redirect, url_for, request, g, make_response, json, jsonify, session
from profapp.models.articles import Article, ArticleCompany, ArticlePortalDivision, ReaderArticlePortalDivision
from profapp.models.tag import Tag, TagPortalDivision, TagPortalDivisionArticle
from profapp.models.portal import PortalDivision, UserPortalReader, Portal, MemberCompanyPortal
from ..models.pr_base import Search, PRBase, Grid
from .blueprints_declaration import article_bp
from .request_wrapers import ok, tos_required
from .pagination import pagination
from config import Config
from .views_file import crop_image, update_croped_image
from ..models.files import ImageCroped
from ..models.company import Company, UserCompany

from utils.db_utils import db
from sqlalchemy.orm.exc import NoResultFound
from ..constants.FILES_FOLDERS import FOLDER_AND_FILE
from sqlalchemy.sql import expression, and_
from sqlalchemy import text
import time


# @article_bp.route('/list/', methods=['GET'])
# @tos_required
# def show_mine():
#     return render_template('article/list.html')
#
#
# @article_bp.route('/list/', methods=['POST'])
# @ok
# def load_mine(json):
#     page = json.get('paginationOptions')['pageNumber']
#     pageSize = json.get('paginationOptions')['pageSize']
#     search_text = json.get('search_text')
#     params = {'user_id': g.user_dict['id']}
#     params['sort'] = {}
#     params['filter'] = {}
#     if json.get('sort'):
#         for n in json.get('sort'):
#             params['sort'][n] = json.get('sort')[n]
#     if json.get('filter'):
#         for b in json.get('filter'):
#             if json.get('filter')[b] != '-- all --':
#                 params['filter'][b] = json.get('filter')[b]
#     subquery = ArticleCompany.subquery_user_articles(search_text=search_text, **params)
#     articles, pages, current_page = pagination(subquery,
#                                                page=page, items_per_page=pageSize)
#     add_param = {'value': '1', 'label': '-- all --'}
#     statuses = Article.list_for_grid_tables(ARTICLE_STATUS_IN_COMPANY.all, add_param, False)
#     company_list_for_grid = Article.list_for_grid_tables(
#             ArticleCompany.get_companies_where_user_send_article(g.user_dict['id']), add_param, True)
#     articles_drid_data = Article.getListGridDataArticles(articles.all())
#     grid_filters = {'company': company_list_for_grid, 'status': statuses}
#     return {'grid_data': articles_drid_data,
#             'grid_filters': grid_filters,
#             'total': subquery.count()}


@article_bp.route('/material_update/<string:material_id>/', methods=['GET'])
@article_bp.route('/publication_update/<string:publication_id>/', methods=['GET'])
@article_bp.route('/material_create/company/<string:company_id>/', methods=['GET'])
@tos_required
def article_show_form(material_id=None, publication_id=None, company_id=None):
    company = Company.get(company_id if company_id else (
        ArticlePortalDivision.get(publication_id) if publication_id else ArticleCompany.get(material_id)).company.id)
    return render_template('article/form.html', material_id=material_id, company_id=company_id,
                           publication_id=publication_id, company=company)


@article_bp.route('/material_update/<string:material_id>/', methods=['POST'])
@article_bp.route('/publication_update/<string:publication_id>/', methods=['POST'])
@article_bp.route('/material_create/company/<string:company_id>/', methods=['POST'])
@tos_required
@ok
def load_form_create(json, company_id=None, material_id=None, publication_id=None):
    action = g.req('action', allowed=['load', 'validate', 'save'])

    def portal_division_dict(article, tags=None):
        if (not hasattr(article, 'portal_division_id')) or (article.portal_division_id is None):
            return {'positioned_articles': []}
        else:
            filter = article.position_unique_filter()
            return {'positioned_articles':
                        [pda.get_client_side_dict(fields='id|position|title') for pda in
                         db(ArticlePortalDivision).filter(filter).
                             order_by(expression.desc(ArticlePortalDivision.position)).all()],
                    'availableTags': tags
                    }

    available_tag_names = None

    if company_id:  # creating material version
        articleVersion = ArticleCompany(company_id=company_id, editor=g.user, article=Article(author_user_id=g.user.id))
    elif material_id:  # companys version. always updating existing
        articleVersion = ArticleCompany.get(material_id)
    elif publication_id:  # updating portal version
        articleVersion = ArticlePortalDivision.get(publication_id)
        portal_division_id = articleVersion.portal_division_id

        article_tag_names = articleVersion.tags
        available_tags = PortalDivision.get(portal_division_id).portal_division_tags
        available_tag_names = list(map(lambda x: getattr(x, 'name', ''), available_tags))

    if action == 'load':
        article_dict = articleVersion.get_client_side_dict(more_fields='long|company')

        if publication_id:
            article_dict = dict(list(article_dict.items()) + [('tags', article_tag_names)])

        image_dict = {'ratio': Config.IMAGE_EDITOR_RATIO, 'coordinates': None,
                      'image_file_id': article_dict['image_file_id'],
                      'no_image_url': g.fileUrl(FOLDER_AND_FILE.no_article_image())
                      }
        # article_dict['long'] = '<table><tr><td><em>cell</em> 1</td><td><strong>cell<strong> 2</td></tr></table>'
        # TODO: VK by OZ: this code should be moved to model
        try:
            if article_dict.get('image_file_id'):
                image_dict['image_file_id'], image_dict['coordinates'] = ImageCroped. \
                    get_coordinates_and_original_img(article_dict.get('image_file_id'))
            else:
                image_dict['image_file_id'] = None
        except Exception as e:
            pass

        return {'article': article_dict,
                'image': image_dict,
                'portal_division': portal_division_dict(articleVersion, available_tag_names)}
    else:
        parameters = g.filter_json(json, 'article.title|subtitle|short|long|keywords, image.*')
        articleVersion.attr(parameters['article'])

        if action == 'validate':
            articleVersion.detach()
            return articleVersion.validate(articleVersion.id is not None)
        else:
            image_id = parameters['image'].get('image_file_id')
            # TODO: VK by OZ: this code dont work if ArticlePortalDivision updated
            if image_id:
                articleVersion.image_file_id = crop_image(image_id, parameters['image']['coordinates'])
            else:
                articleVersion.image_file_id = None

            if type(articleVersion) == ArticlePortalDivision:
                tag_names = json['article']['tags']
                articleVersion.manage_article_tags(tag_names)

            articleVersion.save()
            if publication_id:
                articleVersion.insert_after(json['portal_division']['insert_after'],
                                            articleVersion.position_unique_filter())
            return {'article': articleVersion.save().get_client_side_dict(more_fields='long'), 'image': json['image'],
                    'portal_division': portal_division_dict(articleVersion)}


@article_bp.route('/material_details/<string:material_id>/', methods=['GET'])
@tos_required
# @check_rights(simple_permissions([]))
def material_details(material_id):
    return render_template('company/material_details.html',
                           article=ArticleCompany.get(material_id).get_client_side_dict(more_fields='company|long'),
                           company=Company.get(ArticleCompany.get(material_id).company.id))


# def format_material_published(publication, portal):
#

def get_portal_dict_for_material(portal, material_id, company_id):
    ret = portal.get_client_side_dict(fields='id,name,divisions.id|name|portal_division_type_id,own_company.name')
    ret['rights_company_at_portal'] = MemberCompanyPortal.get(company_id=company_id, portal_id=ret['id']).get_rights(),
    ret['divisions'] = PRBase.get_ordered_dict([d for d in ret['divisions'] if (
        d['portal_division_type_id'] == 'events' or d['portal_division_type_id'] == 'news')])
    publication_in_portal = db(ArticlePortalDivision).filter_by(article_company_id=material_id).filter(
            ArticlePortalDivision.portal_division_id.in_(
                    [div_id for div_id, div in ret['divisions'].items()])).first()

    if publication_in_portal:
        ret['publication'] = publication_in_portal.get_client_side_dict(
                'id,position,title,status,visibility,portal_division_id,publishing_tm')
        ret['publication']['division'] = ret['divisions'][ret['publication']['portal_division_id']]
        ret['publication']['counts'] = '0/0/0/0'
        # TODO: OZ by OZ
        ret['actions'] = ['unpublish', 'edit']
    else:
        ret['publication'] = None
        ret['actions'] = ['submit', 'publish', 'edit']
    return ret


@article_bp.route('/material_details/<string:material_id>/', methods=['POST'])
@ok
def material_details_load(json, material_id):
    material = ArticleCompany.get(material_id)

    portals = [get_portal_dict_for_material(p, material_id, material.company_id) for p in
               Company.get(material.company_id).get_portals_where_company_is_member()]

    return {
        'material': material.get_client_side_dict(more_fields='long'),
        'company': Company.get(material.company_id).get_client_side_dict(),
        'rights_user_in_company': UserCompany.get(company_id=material.company_id).get_rights(),
        'portals': {
            'grid_data': portals,
            'grid_filters': {
                'publication.status': Grid.filter_for_status(ArticlePortalDivision.STATUSES)
            }
        }
    }


@article_bp.route('/material_submit_to_portal/', methods=['POST'])
# @check_rights(simple_permissions([]))
@ok
def material_submit_to_portal(json):
    action = g.req('action', allowed=['submit', 'publish'])
    portal = PortalDivision.get(json['portal_division_id']).portal
    material = ArticleCompany.get(json['material_id'])
    publication = material.clone_for_portal(json['portal_division_id'], action)

    return get_portal_dict_for_material(portal, json['material_id'], material.company_id)

@article_bp.route('/material_unpublish_from_portal/', methods=['POST'])
@ok
def publication_unpublish_from_portal(json):
    return {}

# @article_bp.route('/material_details_publications/<string:material_id>/', methods=['POST'])
# @ok
# def material_portals_load(json, material_id):
# article = ArticleCompany.get(material_id)
#
#
# joined_portals = {}
# if article.portal_article:
#     joined_portals = {articles.division.portal.id: portals.pop(articles.division.portal.id)
#                       for articles in article.portal_article
#                       if articles.division.portal.id in portals}
#
# user_rights = list(g.user.user_rights_in_company(article.company_id))
#
# return {'article': article.get_client_side_dict(more_fields='long'),
#         'company': Company.get(article.company_id).get_client_side_dict(),
#         'publications': {
#             'portals': portals,
#             'statuses': Grid.filter_for_status(ArticlePortalDivision.STATUSES),
#             'visibilities': Grid.filter_for_status(ArticlePortalDivision.VISIBILITIES)
#         }
#         # 'allowed_statuses': ARTICLE_STATUS_IN_COMPANY.can_user_chage_status_to(article['status']),
#
#
#         # 'user_rights': ['publish', 'unpublish', 'edit'],
#         # TODO: uncomment the string below and delete above
#         # TODO: when all works with rights are finished
#         # 'user_rights': user_rights,
#         # 'joined_portals': joined_portals
#         }


@article_bp.route('/details/<string:article_id>/', methods=['GET'])
@tos_required
def details(article_id):
    return render_template('article/details.html',
                           article_id=article_id)


@article_bp.route('/details/<string:article_id>/', methods=['POST'])
@ok
def details_load(json, article_id):
    return Article.get(article_id).get_client_side_dict()


# @article_bp.route('/search_for_company_to_submit/', methods=['POST'])
# @ok
# def search_for_company_to_submit(json):
#     companies = Article().search_for_company_to_submit(
#             g.user_dict['id'], json['article_id'], json['search'])
#     return companies


# @article_bp.route('/submit_to_company/<string:article_id>/', methods=['POST'])
# @ok
# def submit_to_company(json, article_id):
#     a = Article.get(article_id)
#     a.mine_version.clone_for_company(json['company_id']).save()
#     return {'article': a.get(article_id).get_client_side_dict(),
#             'company_id': json['company_id']}


# @article_bp.route('/resubmit_to_company/<string:article_company_id>/', methods=['POST'])
# @ok
# def resubmit_to_company(json, article_company_id):
#     a = ArticleCompany.get(article_company_id)
#     if not a.status == ARTICLE_STATUS_IN_COMPANY.declined:
#         raise Exception('article should have %s to be resubmited' %
#                         ARTICLE_STATUS_IN_COMPANY.declined)
#     a.status = ARTICLE_STATUS_IN_COMPANY.submitted
#     return {'article': a.save().get_client_side_dict()}


@article_bp.route('/details_reader/<string:article_portal_division_id>')
@tos_required
def details_reader(article_portal_division_id):
    article = ArticlePortalDivision.get(article_portal_division_id)
    article.add_recently_read_articles_to_session()
    article_dict = article.get_client_side_dict(fields='id, title,short, cr_tm, md_tm, '
                                                       'publishing_tm, keywords, status, long, image_file_id,'
                                                       'division.name, division.portal.id,'
                                                       'company.name|id')
    article_dict['tags'] = article.tags
    ReaderArticlePortalDivision.add_to_table_if_not_exists(article_portal_division_id)
    favorite = article.check_favorite_status(user_id=g.user.id)

    return render_template('partials/reader/reader_details.html',
                           article=article_dict,
                           favorite=favorite
                           )


@article_bp.route('/list_reader')
@article_bp.route('/list_reader/<int:page>/')
@tos_required
def list_reader(page=1):
    search_text = request.args.get('search_text') or ''
    favorite = 'favorite' in request.args
    if not favorite:
        articles, pages, page = Search.search({'class': ArticlePortalDivision,
                                               'filter': and_(ArticlePortalDivision.portal_division_id ==
                                                              db(PortalDivision).filter(
                                                                      PortalDivision.portal_id ==
                                                                      db(UserPortalReader,
                                                                         user_id=g.user.id).subquery().
                                                                      c.portal_id).subquery().c.id,
                                                              ArticlePortalDivision.status ==
                                                              ArticlePortalDivision.STATUSES['PUBLISHED']),
                                               'tags': True, 'return_fields': 'default_dict'}, page=page)
    else:
        articles, pages, page = Search.search({'class': ArticlePortalDivision,
                                               'filter': (ArticlePortalDivision.id == db(ReaderArticlePortalDivision,
                                                                                         user_id=g.user.id,
                                                                                         favorite=True).subquery().c.
                                                          article_portal_division_id),
                                               'tags': True, 'return_fields': 'default_dict'}, page=page,
                                              search_text=search_text)
    portals = UserPortalReader.get_portals_for_user() if not articles else None

    return render_template('partials/reader/reader_base.html',
                           articles=articles,
                           pages=pages,
                           current_page=page,
                           page_buttons=Config.PAGINATION_BUTTONS,
                           portals=portals,
                           favorite=favorite
                           )


@article_bp.route('add_to_favorite/', methods=['POST'])
def add_delete_favorite():
    favorite = json.loads(request.form.get('favorite'))
    article_portal_division_id = request.form.get('article_portal_division_id')
    ReaderArticlePortalDivision.add_delete_favorite_user_article(article_portal_division_id, favorite)
    return jsonify({'favorite': favorite})
