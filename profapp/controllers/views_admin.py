from .blueprints_declaration import admin_bp
from flask import g, request, url_for, render_template, flash, current_app
from .request_wrapers import ok
from .pagination import pagination
from ..models.translate import TranslateTemplate
from config import Config
from utils.db_utils import db
from sqlalchemy.sql import expression


@admin_bp.route('/translations', methods=['GET'])
def translations():
    return render_template('admin/translations.html',
                           angular_ui_bootstrap_version='//angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.js')


@admin_bp.route('/translations', methods=['POST'])
@ok
def translations_load(json):
    page = json.get('paginationOptions')['pageNumber']
    pageSize = json.get('paginationOptions')['pageSize']
    params = {}
    params['sort'] = {}
    params['filter'] = {}
    params['search_text'] = {}
    if json.get('sort'):
        for n in json.get('sort'):
            params['sort'][n] = json.get('sort')[n]
    if json.get('filter'):
        for b in json.get('filter'):
            if json.get('filter')[b] != '-- all --':
                params['filter'][b] = json.get('filter')[b]
    if json.get('search_text'):
        for d in json.get('search_text'):
            params['search_text'][d] = json.get('search_text')[d]
    if json.get('editItem'):
        exist = db(TranslateTemplate, template=json.get('editItem')['template'], name=json.get('editItem')['name']).first()
        TranslateTemplate.get(exist.id).attr({json.get('editItem')['col']: json.get('editItem')['newValue']}).save().get_client_side_dict()
    subquery = TranslateTemplate.subquery_search(template=json.get('template') or None,
                                                 url=json.get('url') or None,
                                                 **params)
    translations, pages, current_page = pagination(subquery, page=page, items_per_page=pageSize)
    add_param = {'value': '1','label': '-- all --'}
    templates = db(TranslateTemplate.template).group_by(TranslateTemplate.template) \
        .order_by(expression.asc(expression.func.lower(TranslateTemplate.template))).all()
    urls = db(TranslateTemplate.url).group_by(TranslateTemplate.url) \
        .order_by(expression.asc(expression.func.lower(TranslateTemplate.url))).all()

    urls_g = TranslateTemplate.list_for_grid_tables(urls, add_param,False)
    templates_g = TranslateTemplate.list_for_grid_tables(templates, add_param,False)
    grid_data = TranslateTemplate.getListGridDataTranslation(translations)
    grid_filters = {'template': templates_g,'url': urls_g}
    return {'grid_data': grid_data,
            'grid_filters': grid_filters,
            'total': subquery.count()
            }


@admin_bp.route('/translations_save', methods=['POST'])
@ok
def translations_save(json):
    exist = db(TranslateTemplate, template=json['row'], name=json['col']).first()
    return TranslateTemplate.get(exist.id).attr({json['lang']: json['val']}).save().get_client_side_dict()

@admin_bp.route('/delete', methods=['POST'])
@ok
def delete(json):
    return TranslateTemplate.delete(json['objects'])
