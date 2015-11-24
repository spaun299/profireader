from flask import render_template, redirect, url_for, request, g, make_response
from profapp.forms.article import ArticleForm
from profapp.models.articles import Article, ArticleCompany, ArticlePortalDivision
from profapp.models.users import User
# from profapp.models.company import Company
# from db_init import db_session
from .blueprints_declaration import article_bp
from .request_wrapers import ok, object_to_dict
from ..constants.ARTICLE_STATUSES import ARTICLE_STATUS_IN_COMPANY, ARTICLE_STATUS_IN_PORTAL
# import os
from .pagination import pagination
from config import Config
from .views_file import crop_image, update_croped_image
from ..models.files import ImageCroped, File
from ..models.pr_base import PRBase
from utils.db_utils import db
from sqlalchemy.orm.exc import NoResultFound
from ..models.translate import TranslateTemplate



@article_bp.route('/translate/', methods=['POST'])
@ok
def translate(json):
    translation = TranslateTemplate.getTranslate(request.json['template'], request.json['phrase'])
    return {'phrase': translation}


@article_bp.route('/save_translate/', methods=['POST'])
@ok
def save_translate(json):
    return TranslateTemplate.getTranslate(json['template'], json['phrase'], json['url'])


@article_bp.route('/list/', methods=['GET'])
def show_mine():
    return render_template(
        'article/list.html',
        angular_ui_bootstrap_version='//angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.js')


@article_bp.route('/list/', methods=['POST'])
@ok
def load_mine(json):
    current_page = json.get('pages')['current_page'] if json.get('pages') else 1
    chosen_company_id = json.get('chosen_company')['id'] if json.get('chosen_company') else 0
    params = {'search_text': json.get('search_text'), 'user_id': g.user_dict['id']}
    original_chosen_status = None
    article_status = json.get('chosen_status')
    if chosen_company_id:
        params['company_id'] = chosen_company_id
    if article_status and article_status != 'All':
        params['status'] = original_chosen_status = article_status
    subquery = ArticleCompany.subquery_user_articles(**params)

    articles, pages, current_page = pagination(subquery,
                                               page=current_page)

    all, companies = ArticleCompany.get_companies_where_user_send_article(g.user_dict['id'])
    statuses = {status: status for status in ARTICLE_STATUS_IN_COMPANY.all}
    statuses['All'] = 'All'

    articles_with_time = []

    for (article, time) in articles.all():
        article_dict = article.get_client_side_dict()
        article_dict['md_tm'] = time
        articles_with_time.append({'article': article_dict,
                                   'company_count': len(article_dict['submitted_versions']) + 1})

    return {'articles': articles_with_time,
            'companies': companies,
            'search_text': json.get('search_text') or '',
            'original_search_text': json.get('search_text') or '',
            'chosen_company': json.get('chosen_company') or all,
            'pages': {'total': pages,
                      'current_page': current_page,
                      'page_buttons': Config.PAGINATION_BUTTONS},
            'chosen_status': json.get('chosen_status') or statuses['All'],
            'original_chosen_status': original_chosen_status,
            'statuses': statuses}


@article_bp.route('/create/', methods=['GET'])
def show_form_create():
    return render_template('article/create.html')


@article_bp.route('/create/', methods=['POST'])
@ok
def load_form_create(json):
    action = g.req('action', allowed=['load', 'validate', 'save'])
    if action == 'load':
        return {'id': '', 'title': '', 'short': '', 'long': '', 'coordinates': '',
                'ratio': Config.IMAGE_EDITOR_RATIO}
    if action == 'validate':
        del json['coordinates'], json['ratio']

        return Article.save_new_article(g.user_dict['id'],
                                        **g.filter_json(json, 'title,short,long,keywords')).mine_version.validate(
            'insert')
    else:
        image_id = json.get('image_file_id')
        if image_id:
            json['image_file_id'] = crop_image(image_id, json.get('coordinates'))
        del json['coordinates'], json['ratio']
        article = Article.save_new_article(g.user_dict['id'], **json)
        g.db.add(article)
        return article.get_client_side_dict()


@article_bp.route('/update/<string:article_company_id>/', methods=['GET'])
def show_form_update(article_company_id):
    return render_template('article/update.html',
                           article_company_id=article_company_id)


@article_bp.route('/update/<string:article_company_id>/', methods=['POST'])
@ok
def load_form_update(json, article_company_id):
    action = g.req('action', allowed=['load', 'save', 'validate'])
    article = ArticleCompany.get(article_company_id)
    if action == 'load':
        article = article.get_client_side_dict()
        article.update(ratio=Config.IMAGE_EDITOR_RATIO)
        image_id = article.get('image_file_id')
        if image_id:
            try:
                article['image_file_id'], coordinates = ImageCroped. \
                    get_coordinates_and_original_img(image_id)
                article.update(coordinates)
            except NoResultFound:
                pass
        return article
    else:
        article.attr({key: val for key, val in json.items() if key in
                      ['keywords', 'title', 'short', 'long']})
        if action == 'save':
            image_id = json.get('image_file_id')
            coordinates = json.get('coordinates')
            if image_id:
                if db(ImageCroped, original_image_id=image_id).count():
                    update_croped_image(image_id, coordinates)
                else:
                    article.image_file_id = crop_image(image_id, coordinates)
                    article.save()

            article = article.get_client_side_dict()
            # print(article['image_file_id'])
            return article
        else:
            # return {'errors': {}, 'warnings': {}, 'notices': {}}
            article.detach()
            return article.validate('update')


@article_bp.route('/save/<string:article_company_id>/', methods=['POST'])
@ok
def save(json, article_company_id):
    pass
    # return ret.get_client_side_dict()


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
