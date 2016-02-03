from .blueprints_declaration import admin_bp
from flask import g, request, url_for, render_template, flash, current_app
from .request_wrapers import ok
from .pagination import pagination
from ..models.translate import TranslateTemplate
from config import Config
from utils.db_utils import db
from sqlalchemy.sql import expression
import datetime
from ..models.pr_base import PRBase, Grid

@admin_bp.route('/translations', methods=['GET'])
def translations():
    return render_template('admin/translations.html',
                           angular_ui_bootstrap_version='//angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.js')


@admin_bp.route('/translations', methods=['POST'])
@ok
def translations_load(json):
    subquery = TranslateTemplate.subquery_search(json.get('filter'), json.get('sort') , json.get('editItem'))

    translations, pages, current_page, count = pagination(subquery, **Grid.page_options(json.get('paginationOptions')))

    grid_filters = {
        'template': [{'value': portal[0], 'label': portal[0]} for portal in
                    db(TranslateTemplate.template).group_by(TranslateTemplate.template) \
        .order_by(expression.asc(expression.func.lower(TranslateTemplate.template))).all()],
        'url': [{'value': portal[0], 'label': portal[0]} for portal in
                    db(TranslateTemplate.url).group_by(TranslateTemplate.url) \
        .order_by(expression.asc(expression.func.lower(TranslateTemplate.url))).all()]
    }
    return {'grid_data': [translation.get_client_side_dict() for translation in translations],
            'grid_filters': {k: [{'value': None, 'label': TranslateTemplate.getTranslate('', '__-- all --')}] + v for
                             (k, v) in grid_filters.items()},
            'total': count
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


