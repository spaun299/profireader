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
    page = json.get('gr_data')['paginationOptions']['pageNumber'] if json.get('gr_data') else 1
    pageSize = json.get('gr_data')['paginationOptions']['pageSize'] if json.get('gr_data') else 25
    params = {}
    if json.get('gr_data'):
        params['sort'] = {}
        params['filter'] = {}
        params['search_text'] = {}
        if json.get('gr_data')['sort']:
            for n in json.get('gr_data')['sort']:
                params['sort'][n] = json.get('gr_data')['sort'][n]
        if json.get('gr_data')['filter']:
            for b in json.get('gr_data')['filter']:
                if json.get('gr_data')['filter'][b] != '-- all --':
                    params['filter'][b] = json.get('gr_data')['filter'][b]
        if json.get('gr_data')['search_text']:
            for d in json.get('gr_data')['search_text']:
                if json.get('gr_data')['search_text'][d] != '-- all --':
                    params['search_text'][d] = json.get('gr_data')['search_text'][d]
        if json.get('gr_data')['editItem']:
            exist = db(TranslateTemplate, template=json.get('gr_data')['editItem']['template'], name=json.get('gr_data')['editItem']['name']).first()
            TranslateTemplate.get(exist.id).attr({json.get('gr_data')['editItem']['col']: json.get('gr_data')['editItem']['newValue']}).save().get_client_side_dict()
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
    print(grid_filters)
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
