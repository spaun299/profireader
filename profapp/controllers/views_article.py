from flask import render_template, redirect, url_for, request, g, make_response
from profapp.models.articles import Article, ArticleCompany, ArticlePortalDivision
from .blueprints_declaration import article_bp
from .request_wrapers import ok
from ..constants.ARTICLE_STATUSES import ARTICLE_STATUS_IN_COMPANY, ARTICLE_STATUS_IN_PORTAL
from .pagination import pagination
from config import Config
from .views_file import crop_image, update_croped_image
from ..models.files import ImageCroped
from utils.db_utils import db
from sqlalchemy.orm.exc import NoResultFound
import time


@article_bp.route('/list/', methods=['GET'])
def show_mine():
    return render_template('article/list.html')


@article_bp.route('/list/', methods=['POST'])
@ok
def load_mine(json):
    current_page = json.get('pages') if json.get('pages') else 1
    chosen_company_id = json.get('chosen_company') if json.get('chosen_company') else 0
    search_text = json.get('search_text') if json.get('search_text') else None
    params = {'search_text': search_text, 'user_id': g.user_dict['id']}
    original_chosen_status = None
    article_status = json.get('chosen_status') if json.get('chosen_status') else None
    if chosen_company_id:
        params['company_id'] = chosen_company_id
    if article_status and article_status != 'All':
        params['status']  = article_status
    date_sort = json.get('sort_date') if json.get('sort_date') else None
    subquery = ArticleCompany.subquery_user_articles(sort=date_sort,**params)
    articles, pages, current_page = pagination(subquery,
                                               page=current_page, items_per_page=json.get('pageSize'))

    all, companies = ArticleCompany.get_companies_where_user_send_article(g.user_dict['id'])
    add_param = {'value': '1','label': 'All'}
    statuses = Article.list_for_grid_tables(ARTICLE_STATUS_IN_COMPANY.all, add_param, False)
    company_list_for_grid = [];b=1
    companies.sort(key=lambda k: k['name'])
    for cp in companies:
        company_list_for_grid.append({
                'value': str(b),
                'label': cp['name'],
                'id': cp['id']
        })
        b += 1
    articles_with_time = []
    for (article, time) in articles.all():
        article_dict = article.get_client_side_dict()
        article_dict['md_tm'] = time
        articles_with_time.append({'article': article_dict,
                                   'company_count': len(article_dict['submitted_versions']) + 1})
    articles_drid_data = []

    for (article, time) in articles.all():
        companies_for_article = ArticleCompany.get_companies_for_article(article.id)
        article_dict = article.get_client_side_dict()
        capm = '' if len(companies_for_article)>0 else 'Not sent to any company yet'
        st = '' if len(article_dict['submitted_versions'])>0 else 'Not sent'
        article_dict['md_tm'] = time
        articles_drid_data.append({'Date': article_dict['md_tm'],
                                   'Title': article_dict['mine_version']['title'],
                                   'Campanies': capm,
                                   'Status': st,
                                   'id': str(article_dict['id']),
                                   'level': True})
        if companies_for_article:
            i = 0
            for child in companies_for_article:
                st = article_dict['submitted_versions'][i]['status'] if len(article_dict['submitted_versions'])>0 else 'Not sent'
                articles_drid_data.append({'Date': '',
                                   'Title': '',
                                   'Campanies': child['name'],
                                   'Status': st,
                                   'id': '',
                                   'level': False})
                i += 1


    return { 'grid_data': articles_drid_data,
            'articles': articles_with_time,
            'companies': company_list_for_grid,
            'search_text': json.get('search_text') or '',
            'original_search_text': json.get('search_text') or '',
            'chosen_company': json.get('chosen_company') or all,
            'pages': {'total': pages,
                      'current_page': current_page,
                      'page_buttons': Config.PAGINATION_BUTTONS},
            'chosen_status': json.get('chosen_status') or statuses[-1],
            'original_chosen_status': original_chosen_status,
            'statuses': statuses,
            'total': len(articles_with_time)}


@article_bp.route('/update/<string:article_company_id>/', methods=['GET'])
@article_bp.route('/create/', methods=['GET'])
def article_show_form(article_company_id=None):
    return render_template('article/form.html', article_company_id=article_company_id)

@article_bp.route('/create/', methods=['POST'])
@article_bp.route('/update_mine/<string:mine_version_article_company_id>/', methods=['POST'])
@article_bp.route('/update/<string:article_company_id>/', methods=['POST'])
@ok
def load_form_create(json, article_company_id=None, mine_version_article_company_id=None):
    action = g.req('action', allowed=['load', 'validate', 'save'])

    if article_company_id:  # companys version. always updating existing
        articleVersion = ArticleCompany.get(article_company_id)
    elif mine_version_article_company_id:  # updating personal version
        articleVersion = ArticleCompany.get(mine_version_article_company_id)
    else:  # creating personal version
        articleVersion = ArticleCompany(editor=g.user, article=Article(author_user_id=g.user.id))

    if action == 'load':
        image_dict = {'ratio': Config.IMAGE_EDITOR_RATIO, 'coordinates': None, 'image_file_id': None}
        article_dict = articleVersion.get_client_side_dict(more_fields='long')
        # article_dict['long'] = '<table><tr><td><em>cell</em> 1</td><td><strong>cell<strong> 2</td></tr></table>'
        if article_dict.get('image_file_id'):
            image_dict['image_file_id'], image_dict['coordinates'] = ImageCroped. \
                get_coordinates_and_original_img(article_dict.get('image_file_id'))
        return {'article': article_dict, 'image': image_dict}
    else:
        parameters = g.filter_json(json, 'article.title|short|long|keywords, image.*')

        articleVersion.attr(parameters['article'])
        if action == 'validate':
            articleVersion.detach()
            return articleVersion.validate(article_company_id is None)
        else:
            image_id = parameters['image'].get('image_file_id')
            if image_id:
                articleVersion.image_file_id = crop_image(image_id,
                                                          json['image'].get('coordinates'))
            return {'article': articleVersion.save().get_client_side_dict(more_fields='long'),
                    'image': json['image']}


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

