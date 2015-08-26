from flask import render_template, redirect, url_for, request, g
from profapp.forms.article import ArticleForm
from profapp.models.articles import Article, ArticleVersion
from profapp.models.users import User
from profapp.models.company import Company
from db_init import db_session
from .blueprints import article_bp
from .request_wrapers import json
#import os


@article_bp.route('/my/', methods=['GET'])
def show_mine():
    return render_template('article/mine_list.html', articles = Article.list(g.user_dict['id']))

@article_bp.route('/create/', methods=['GET'])
def show_form_create():
    return render_template('article/edit.html', edit_version = {'name': '', 'short':  '', 'long': ''})

@article_bp.route('/create/', methods=['POST'])
def create():
    return redirect(url_for('article.my_versions', article_id = ArticleVersion(None, **request.form.to_dict(True)).save().article_id))

@article_bp.route('/update/<string:article_version_id>/', methods=['GET'])
def show_form_update(article_version_id):
    return render_template('article/edit.html', article_version = ArticleVersion.get(article_version_id))

@article_bp.route('/update/<string:article_version_id>/', methods=['POST'])
def update(article_version_id):
    return redirect(url_for('article.my_versions', article_id = ArticleVersion(article_version_id, **request.form.to_dict(True)).save().article_id))

@article_bp.route('/my/versions/<string:article_id>/', methods=['GET'])
def my_versions(article_id):
    allversions = Article.get_last_company_versions_for_user(article_id, g.user.id)
    return render_template('article/versions.html',
                           edit_version = [v.__dict__ for v in allversions if v.company_id is None][0],
                           company_versions={v.id:v.__dict__ for v in allversions if v.company_id is not None})


@article_bp.route('/send_to_company/', methods=['POST'])
@json
def send_to_company():
    data = request.json

    ArticleVersion.get(data['article_version_id']).clone_for_company(data['company_id']).save()


    # article.clone
    return {'haha': 'hi'}
    # pass