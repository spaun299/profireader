from flask import render_template, redirect, url_for, request, g, make_response
from profapp.models.articles import Article, ArticleCompany, ArticlePortalDivision
from profapp.models.tag import Tag, TagPortalDivision, TagPortalDivisionArticle
from profapp.models.portal import PortalDivision
from .blueprints_declaration import article_bp
from .request_wrapers import ok
from ..constants.ARTICLE_STATUSES import ARTICLE_STATUS_IN_COMPANY, ARTICLE_STATUS_IN_PORTAL
from .pagination import pagination
from config import Config
from .views_file import crop_image, update_croped_image
from ..models.files import ImageCroped
from utils.db_utils import db
from sqlalchemy.orm.exc import NoResultFound
from ..constants.FILES_FOLDERS import FOLDER_AND_FILE
from sqlalchemy.sql import expression
from sqlalchemy import and_

import time


@article_bp.route('/list/', methods=['GET'])
def show_mine():
    return render_template('article/list.html')


@article_bp.route('/list/', methods=['POST'])
@ok
def load_mine(json):
    page = json.get('gr_data')['paginationOptions']['pageNumber'] if json.get('gr_data') else 1
    pageSize = json.get('gr_data')['paginationOptions']['pageSize'] if json.get('gr_data') else 25
    search_text = json.get('gr_data')['search_text'] if json.get('gr_data') else None
    params = {'user_id': g.user_dict['id']}
    if json.get('gr_data'):
        params['sort'] = {}
        params['filter'] = {}
        if json.get('gr_data')['sort']:
            for n in json.get('gr_data')['sort']:
                params['sort'][n] = json.get('gr_data')['sort'][n]
        if json.get('gr_data')['filter']:
            for b in json.get('gr_data')['filter']:
                if json.get('gr_data')['filter'][b] != '--all--':
                    params['filter'][b] = json.get('gr_data')['filter'][b]
    subquery = ArticleCompany.subquery_user_articles(search_text=search_text,**params)
    articles, pages, current_page = pagination(subquery,
                                               page=page, items_per_page=pageSize)
    add_param = {'value': '1', 'label': 'All'}
    statuses = Article.list_for_grid_tables(ARTICLE_STATUS_IN_COMPANY.all, add_param, False)
    company_list_for_grid = Article.list_for_grid_tables(ArticleCompany.get_companies_where_user_send_article(g.user_dict['id']), add_param, True)
    articles_drid_data = Article.getListGridDataArticles(articles.all())
    grid_filters = {'company': company_list_for_grid,'status': statuses}
    return {'grid_data': articles_drid_data,
            'grid_filters': grid_filters,
            'total': subquery.count()}


@article_bp.route('/update/<string:article_company_id>/', methods=['GET'])
@article_bp.route('/updateatportal/<string:article_portal_division_id>/', methods=['GET'])
@article_bp.route('/create/', methods=['GET'])
def article_show_form(article_company_id=None, article_portal_division_id=None):
    return render_template('article/form.html', article_portal_division_id=article_portal_division_id,
                           article_company_id=(article_company_id or article_portal_division_id))


@article_bp.route('/create/', methods=['POST'])
@article_bp.route('/update_mine/<string:mine_version_article_company_id>/', methods=['POST'])
@article_bp.route('/update/<string:article_company_id>/', methods=['POST'])
@article_bp.route('/updateatportal/<string:article_portal_division_id>/', methods=['POST'])
@ok
def load_form_create(json, article_company_id=None, mine_version_article_company_id=None,
                     article_portal_division_id=None):
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

    if article_company_id:  # companys version. always updating existing
        articleVersion = ArticleCompany.get(article_company_id)
    elif mine_version_article_company_id:  # updating personal version
        articleVersion = ArticleCompany.get(mine_version_article_company_id)
    elif article_portal_division_id:  # updating portal version
        articleVersion = ArticlePortalDivision.get(article_portal_division_id)
        portal_division_id = articleVersion.portal_division_id

        article_tag_names = articleVersion.tags
        available_tags = PortalDivision.get(portal_division_id).portal_division_tags
        available_tag_names = list(map(lambda x: getattr(x, 'name', ''), available_tags))

    else:  # creating personal version
        articleVersion = ArticleCompany(editor=g.user, article=Article(author_user_id=g.user.id))

    if action == 'load':
        article_dict = articleVersion.get_client_side_dict(more_fields='long|company')

        if article_portal_division_id:
            article_dict = dict(list(article_dict.items()) + [('tags', article_tag_names)])

        image_dict = {'ratio': Config.IMAGE_EDITOR_RATIO, 'coordinates': None,
                      'image_file_id': article_dict['image_file_id'],
                      'no_image_file_id': FOLDER_AND_FILE.no_article_image()
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
        parameters = g.filter_json(json, 'article.title|short|long|keywords, image.*')

        articleVersion.attr(parameters['article'])
        if action == 'validate':
            articleVersion.detach()
            return articleVersion.validate(article_company_id is None)
        else:
            image_id = parameters['image'].get('image_file_id')
            # TODO: VK by OZ: this code dont work if ArticlePortalDivision updated
            if image_id:
                del parameters['image']['image_file_id']
                articleVersion.image_file_id = crop_image(image_id, parameters['image']['coordinates'])
            else:
                articleVersion.image_file_id = None

            if type(articleVersion) == ArticlePortalDivision:
                tag_names = json['article']['tags']
                articleVersion.manage_article_tags(tag_names)

            a = articleVersion.save()
            if article_portal_division_id:
                articleVersion.insert_after(json['portal_division']['insert_after'], articleVersion.position_unique_filter())
            return {'article': articleVersion.save().get_client_side_dict(more_fields='long'), 'image': json['image'],
                    'portal_division': portal_division_dict(articleVersion)}


@article_bp.route('/details/<string:article_id>/', methods=['GET'])
def details(article_id):
    return render_template('article/details.html',
                           article_id=article_id)


@article_bp.route('/details/<string:article_id>/', methods=['POST'])
@ok
def details_load(json, article_id):
    return Article.get(article_id).get_client_side_dict()


@article_bp.route('/search_for_company_to_submit/', methods=['POST'])
@ok
def search_for_company_to_submit(json):
    companies = Article().search_for_company_to_submit(
        g.user_dict['id'], json['article_id'], json['search'])
    return companies


@article_bp.route('/submit_to_company/<string:article_id>/', methods=['POST'])
@ok
def submit_to_company(json, article_id):
    a = Article.get(article_id)
    a.mine_version.clone_for_company(json['company_id']).save()
    return {'article': a.get(article_id).get_client_side_dict(),
            'company_id': json['company_id']}


@article_bp.route('/resubmit_to_company/<string:article_company_id>/', methods=['POST'])
@ok
def resubmit_to_company(json, article_company_id):
    a = ArticleCompany.get(article_company_id)
    if not a.status == ARTICLE_STATUS_IN_COMPANY.declined:
        raise Exception('article should have %s to be resubmited' %
                        ARTICLE_STATUS_IN_COMPANY.declined)
    a.status = ARTICLE_STATUS_IN_COMPANY.submitted
    return {'article': a.save().get_client_side_dict()}
