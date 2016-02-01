from .blueprints_declaration import reader_bp
from flask import render_template, redirect, jsonify, json, request
from .request_wrapers import tos_required
from sqlalchemy import and_
from ..models.articles import ArticlePortalDivision, ReaderArticlePortalDivision, Search
from ..models.portal import PortalDivision, UserPortalReader
from config import Config
from utils.db_utils import db


@reader_bp.route('profile/')
def profile():
    render_template('partials/reader/reader_profile.html')


@reader_bp.route('/details_reader/<string:article_portal_division_id>')
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


@reader_bp.route('/list_reader')
@reader_bp.route('/list_reader/<int:page>/')
@tos_required
def list_reader(page=1):
    search_text = request.args.get('search_text') or ''
    favorite = 'favorite' in request.args
    if not favorite:
        articles, pages, page = Search.search({'class': ArticlePortalDivision,
                                               'filter': and_(ArticlePortalDivision.portal_division_id ==
                                                              db(PortalDivision).filter(
                                                                  PortalDivision.portal_id ==
                                                                  db(UserPortalReader, user_id=g.user.id).subquery().
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


@reader_bp.route('add_to_favorite/', methods=['POST'])
def add_delete_favorite():
    favorite = json.loads(request.form.get('favorite'))
    article_portal_division_id = request.form.get('article_portal_division_id')
    ReaderArticlePortalDivision.add_delete_favorite_user_article(article_portal_division_id, favorite)
    return jsonify({'favorite': favorite})
