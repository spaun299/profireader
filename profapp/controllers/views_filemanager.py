import os
import re
from flask import render_template, g, make_response
from flask.ext.login import current_user
from profapp.models.files import File, FileContent, YoutubeApi
from .blueprints_declaration import filemanager_bp
from .request_wrapers import ok
from functools import wraps
from time import sleep
from flask import jsonify
import json as jsonmodule
from flask import session, redirect, request, url_for
from ..models.google import GoogleAuthorize, GoogleToken
from utils.db_utils import db
from ..models.company import Company
from ..models.translate import TranslateTemplate


def parent_folder(func):
    @wraps(func)
    def function_parent_folder(json, *args, **kwargs):
        ret = func(json, *args, **kwargs)
        return ret

    return function_parent_folder


root = os.getcwd() + '/profapp/static/filemanager/tmp'
json_result = {"result": {"success": True, "error": None}}


@filemanager_bp.route('/')
def filemanager():
    # library = {g.user.personal_folder_file_id:
    # {'name': 'My personal files',
    # 'icon': current_user.gravatar(size=18)}}
    library = {}

    for user_company in g.user.employer_assoc:
        # TODO VK by OZ: we need function that get all emploees with specific right
        # Company.get_emploees('can_read', status = 'active')
        # Company.get_emploees(['can_read', 'can_write'], status = ['active','banned'])
        # similar function User.get_emploers ...
        if user_company.status == 'active' and 'upload_files' in g.user.user_rights_in_company(user_company.company_id):
            library[user_company.employer.journalist_folder_file_id] = {
            'name': "%s files" % (user_company.employer.name,), 'icon': ''}

    file_manager_called_for = request.args[
        'file_manager_called_for'] if 'file_manager_called_for' in request.args else ''
    file_manager_on_action = jsonmodule.loads(
        request.args['file_manager_on_action']) if 'file_manager_on_action' in request.args else {}
    file_manager_default_action = request.args[
        'file_manager_default_action'] if 'file_manager_default_action' in request.args else ''

    # library = {}
    err = True if len(library) == 0 else False
    return render_template('filemanager.html', library=library, err=err,
                           file_manager_called_for=file_manager_called_for,
                           file_manager_on_action=file_manager_on_action,
                           file_manager_default_action=file_manager_default_action)


@filemanager_bp.route('/list/', methods=['POST'])
@ok
# @parent_folder
def list(json):
    list = File.list(json['params']['folder_id'], json['params']['file_manager_called_for'])
    ancestors = File.ancestors(json['params']['folder_id'])
    return {'list': list, 'ancestors': ancestors}


@filemanager_bp.route('/search/', methods=['POST'])
@ok
def search_list(json):
    if json['params']['search_text'] != '':
        list = File.list(json['params']['folder'], json['params']['file_manager_called_for'],
                         json['params']['search_text'])
        ancestors = File.ancestors(json['params']['folder'])
    else:
        list = []
        ancestors = File.ancestors(json['params']['folder'])
    return {'list': list, 'ancestors': ancestors}


@filemanager_bp.route('/createdir/', methods=['POST'])
@ok
def createdir(json, parent_id=None):
    return File.createdir(name=request.json['params']['name'],
                          root_folder_id=request.json['params']['root_id'],
                          parent_id=request.json['params']['folder_id'])


@filemanager_bp.route('/test/', methods=['GET', 'POST'])
def test():
    name = TranslateTemplate.getTranslate('companies_list', 'Company name is `%(name)s` - YOUR OWN COMPANY')
    return render_template('tmp-test.html', file=name)


@filemanager_bp.route('/properties/', methods=['POST'])
@ok
def set_properties(json):
    file = File.get(request.json['params']['id'], )
    return File.set_properties(file, request.json['params']['add_all'], name=request.json['params']['name'],
                               copyright_author_name=request.json['params']['author_name'],
                               description=request.json['params']['description'])


@filemanager_bp.route('/rename/', methods=['POST'])
@ok
def rename(json):
    file = File.get(request.json['params']['id'], )
    return File.rename(file, request.json['params']['name'])


@filemanager_bp.route('/copy/', methods=['POST'])
@ok
def copy(json):
    file = File.get(request.json['params']['id'])
    file.copy_file(request.json['params']['folder_id'])
    return file.id


@filemanager_bp.route('/cut/', methods=['POST'])
@ok
def cut(json):
    file = File.get(request.json['params']['id'])
    return File.move_to(file, request.json['params']['folder_id'])


@filemanager_bp.route('/remove/<string:file_id>', methods=['POST'])
def remove(file_id):
    return File.remove(file_id)


# @filemanager_bp.route('/upload/<string:parent_id>/', methods=['POST'])
# def upload(parent_id):
#     sleep(0.1)
#     parent = File.get(parent_id)
#     root_id = parent.root_folder_id
#     if root_id == None:
#         root_id = parent.id
#     data = request.form
#     uploaded_file = request.files['file']
#     name = File.get_unique_name(uploaded_file.filename, uploaded_file.content_type, parent.id)
#     uploaded = File.upload(name, data, parent.id, root_id, content=uploaded_file.stream.read(-1))
#     return uploaded#jsonify({'result': {'size': 0}})

@filemanager_bp.route('/uploader/', methods=['GET', 'POST'])
@filemanager_bp.route('/uploader/<string:company_id>', methods=['GET', 'POST'])
def uploader(company_id=None):
    token_db_class = GoogleToken()
    credentials_exist = token_db_class.check_credentials_exist()
    google = GoogleAuthorize()
    if not credentials_exist and google.check_admins():
        if 'code' in request.args:
            session['auth_code'] = request.args['code']
            token_db_class.save_credentials()
        return redirect(url_for('company.show')) if 'code' in request.args \
            else redirect(google.get_auth_code())
    return render_template('file_uploader.html', company_id=company_id)


@filemanager_bp.route('/send/<string:parent_id>/', methods=['POST'])
def send(parent_id):
    """ YOU SHOULD SEND PROPERTY NAME, DESCRIPTION, ROOT_FOLDER AND FOLDER.
    NOW THIS VALUES GET FROM DB. HARDCODE!!! """
    file = request.files['file']
    parent = File.get(parent_id)
    root = parent.root_folder_id
    if parent.mime == 'root':
        root = parent.id
    data = request.form
    uploaded_file = request.files['file']
    name = File.get_unique_name(uploaded_file.filename, data.get('ftype'), parent.id)
    company = db(Company, journalist_folder_file_id=root).one()
    if re.match('^video/.*', data.get('ftype')):
        body = {'title': file.filename,
                'description': '',
                'status': 'public'}
        youtube = YoutubeApi(body_dict=body,
                             video_file=file.stream.read(-1),
                             chunk_info=dict(chunk_size=int(data.get('chunkSize')),
                                             chunk_number=int(data.get('chunkNumber')),
                                             total_size=int(data.get('totalSize'))),
                             company_id=company.id,
                             root_folder_id=company.journalist_folder_file_id,
                             parent_folder_id=parent_id)
        youtube.upload()
    else:
        File.upload(name, data, parent.id, root, content=uploaded_file.stream.read(-1))
    return jsonify({'result': {'size': 0}})


@filemanager_bp.route('/resumeopload/', methods=['GET'])
def resumeopload():
    return jsonify({'size': 0})
