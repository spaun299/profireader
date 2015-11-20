from .blueprints_declaration import portal_bp
from flask import render_template, g, flash, redirect, url_for, jsonify
from ..models.company import Company
from flask.ext.login import current_user, login_required
from ..models.portal import PortalDivisionType
from utils.db_utils import db
from ..models.portal import MemberCompanyPortal, Portal, PortalLayout, PortalDivision, \
    PortalDivisionSettings_company_subportal
from ..models.tag import Tag, TagPortal, TagPortalDivision
from .request_wrapers import ok, check_rights
from ..models.articles import ArticlePortalDivision, ArticleCompany
from ..models.company import simple_permissions
from ..models.rights import Right
from profapp.models.rights import RIGHTS
from ..controllers import errors
import copy
from .pagination import pagination
from ..constants.ARTICLE_STATUSES import ARTICLE_STATUS_IN_PORTAL
from config import Config


@portal_bp.route('/create/<string:company_id>/', methods=['GET'])
@login_required
# @check_rights(simple_permissions([]))
def create(company_id):
    company = db(Company, id=company_id).one()
    company_logo = company.logo_file_relationship.url() \
        if company.logo_file_id else '/static/images/company_no_logo.png'

    return render_template('portal/portal_create.html',
                           company_id=company_id,
                           company_logo=company_logo,
                           company_name=company.name,
                           company=company.get_client_side_dict())


# @portal_bp.route('/create/<string:company_id>/', methods=['POST'])
# @ok
# # @check_rights(simple_permissions([]))
# def load_create(json, company_id):
#     return {}


@portal_bp.route('/<any(create,update):create_or_update>/<string:company_id>/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([Right[RIGHTS.MANAGE_PORTAL()]]))
@ok
def create_save(json, create_or_update, company_id):
    action = g.req('action', allowed=['load', 'save', 'validate'])
    layouts = [x.get_client_side_dict() for x in db(PortalLayout).all()]
    types = {x.id: x.get_client_side_dict() for x in PortalDivisionType.get_division_types()}
    company = Company.get(company_id)
    member_companies = {company_id: company.get_client_side_dict()}
    company_logo = company.logo_file_relationship.url() if company.logo_file_id else '/static/images/company_no_logo.png'

    if action == 'load':
        ret = {'company_id': company_id,
               'company_logo': company_logo,
               'portal_company_members': member_companies,
               'portal': {'company_owner_id': company_id, 'name': '', 'host': '',
                          'logo_file_id': company.logo_file_id,
                          'portal_layout_id': layouts[0]['id'],
                          'divisions': [
                              {'name': 'index page', 'portal_division_type_id': 'index'},
                              {'name': 'news', 'portal_division_type_id': 'news'},
                              {'name': 'events', 'portal_division_type_id': 'events'},
                              {'name': 'catalog', 'portal_division_type_id': 'catalog'},
                              {'name': 'our subportal', 'portal_division_type_id': 'company_subportal',
                               'settings': {'company_id': company_id}}]},
               'layouts': layouts, 'division_types': types}
        if create_or_update == 'update':
            pass
            # ret['portal'] =
        return ret
    else:
        json_portal = json['portal']
        if create_or_update == 'update':
            pass
        elif create_or_update == 'create':
            portal = Portal(company_owner=company, **g.filter_json(json_portal, 'name', 'portal_layout_id', 'host'))
            divisions = []
            for division_json in json['portal']['divisions']:
                division = PortalDivision(portal, portal_division_type_id=division_json['portal_division_type_id'],
                                          position=len(json['portal']['divisions']) - len(divisions),
                                          name=division_json['name'])
                if division_json['portal_division_type_id'] == 'company_subportal':
                    division.settings = {'member_company_portal': portal.company_members[0]}
                divisions.append(division)
            # self, portal=portal, portal_division_type=portal_division_type, name='', settings={}
            portal.divisions = divisions
        if action == 'save':
            return portal.setup_created_portal(g.filter_json(json_portal, 'logo_file_id')).save().get_client_side_dict()
        else:
            return portal.validate(create_or_update)


# member_company = Portal.companies


# @portal_bp.route('/confirm_create/<string:company_id>/', methods=['POST'])
# @login_required
# # @check_rights(simple_permissions([Right[RIGHTS.MANAGE_PORTAL()]]))
# @ok
# def confirm_create(json, company_id):
#
#
#
#
#     validation_result = portal.validate()
#
#     if '__validation' in json:
#         db = getattr(g, 'db', None)
#         db.rollback()
#         return validation_result
#     elif len(validation_result['errors'].keys()):
#         raise errors.ValidationException(validation_result)
#     else:
#
#
#     ret = {
#         'company_id': company_id,
#         'company_logo': company_logo,
#         'layouts': layouts,
#         'division_types': {x.id: x.get_client_side_dict() for x in
#                            PortalDivisionType.get_division_types()}
#     }
#
#     if action == 'create':
#         ret['portal'] = {'company_id': company_id, 'name': '', 'host': '',
#                          'portal_layout_id': layouts[0]['id'],
#                          'divisions': [
#                              {'name': 'index page', 'portal_division_type_id': 'index'},
#                              {'name': 'news', 'portal_division_type_id': 'news'},
#                              {'name': 'events', 'portal_division_type_id': 'events'},
#                              {'name': 'catalog', 'portal_division_type_id': 'catalog'},
#                              {'name': 'about', 'portal_division_type_id': 'about'},
#                          ]}
#     else:
#         ret['portal'] = {}
#
#     return ret


@portal_bp.route('/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def apply_company(json):
    MemberCompanyPortal.apply_company_to_portal(company_id=json['company_id'],
                                                portal_id=json['portal_id'])
    return {'portals_partners': [portal.portal.to_dict(
        'name, company_owner_id,id') for portal in MemberCompanyPortal.get_portals(json['company_id'])],
            'company_id': json['company_id']}


@portal_bp.route('/profile/<string:portal_id>/', methods=['GET'])
@login_required
# @check_rights(simple_permissions([]))
def profile(portal_id):
    portal = db(Portal, id=portal_id).one()
    company = portal.own_company
    company_logo = company.logo_file_relationship.url() \
        if company.logo_file_id else '/static/images/company_no_logo.png'
    return render_template('portal/portal_profile.html',
                           company_id=company.id,
                           company_logo=company_logo,
                           company=company.get_client_side_dict()
                           )


# TODO: VK by OZ: remove company_* kwargs


@portal_bp.route('/profile/<string:portal_id>/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def profile_load(json, portal_id):
    portal = db(Portal, id=portal_id).one()
    portal_bound_tags = portal.portal_bound_tags_select
    tags = set(tag_portal_division.tag for tag_portal_division in portal_bound_tags)
    tags_dict = {tag.id: tag.name for tag in tags}
    return {'portal': portal.to_dict('*, divisions.*, own_company.*, portal_bound_tags_select.*',
                                     'portal_notbound_tags_select.*'),
            'portal_id': portal_id,
            'tag': tags_dict}


@portal_bp.route('/profile_edit/<string:portal_id>/', methods=['GET'])
@login_required
# @check_rights(simple_permissions([]))
def profile_edit(portal_id):
    portal = db(Portal, id=portal_id).one()
    company = portal.own_company
    # company_id = portal.company_owner_id

    company_logo = company.logo_file_relationship.url() \
        if company.logo_file_id else '/static/images/company_no_logo.png'
    return render_template('portal/portal_profile_edit.html',
                           company_id=company.id,
                           company_logo=company_logo,
                           company=company.get_client_side_dict()
                           )


# TODO: VK by OZ: remove company_* kwargs

@portal_bp.route('/profile_edit/<string:portal_id>/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def profile_edit_load(json, portal_id):
    portal = db(Portal, id=portal_id).one()

    if 'profile_tags_edit' in json.keys():  # here all changes with tags in db will be done
        # TODO (AA to AA): We have to consider the situation when divisions were changed while editting tags.
        def strip_new_tags(json):
            """ Strips tags have gotten from input prameter json
            :param json: {'bound_tags' [{'portal_division_id': '....', 'tag_name': '  sun  '}, ...],
                'notbound_tags': ['  moon  ', ...], 'confirm_profile_edit': True}
            :return:     {'bound_tags' [{'portal_division_id': '....', 'tag_name': 'sun'}, ...],
                'notbound_tags': ['moon', ...], 'confirm_profile_edit': True}
            """

            def stripping(json_new_value):
                new_list = []
                for elem in json_new_value:
                    new_elem = copy.deepcopy(elem)
                    new_elem['tag_name'] = new_elem['tag_name'].strip()
                    new_list.append(new_elem)
                return new_list

            json_new = {'bound_tags': [], 'notbound_tags': []}

            key = 'bound_tags'
            json_new[key] = stripping(json[key])

            key = 'notbound_tags'
            json_new[key] = list(map(lambda x: getattr(x, 'strip')(), json[key]))

            return json_new

        json_new = strip_new_tags(json)

        curr_portal_bound_tag_port_div_objects = portal.portal_bound_tags_select
        curr_portal_bound_tags = set(map(lambda x: x.tag, curr_portal_bound_tag_port_div_objects))
        curr_portal_bound_tag_names = set(map(lambda x: x.name, curr_portal_bound_tags))
        curr_portal_bound_tags_dict = {}
        for elem in curr_portal_bound_tags:
            curr_portal_bound_tags_dict[elem.name] = elem
        curr_portal_bound_port_div_id_tag_name_object_dict = {}
        for elem in curr_portal_bound_tag_port_div_objects:
            curr_portal_bound_port_div_id_tag_name_object_dict[
                frozenset({('portal_division_id', elem.portal_division_id),
                           ('tag_name', elem.tag.name)})
            ] = elem

        curr_portal_notbound_tag_port_objects = portal.portal_notbound_tags_select
        curr_portal_notbound_tags = set(map(lambda x: x.tag, curr_portal_notbound_tag_port_objects))
        curr_portal_notbound_tag_names = set(map(lambda x: x.name, curr_portal_notbound_tags))
        curr_portal_notbound_tags_dict = {}
        for elem in curr_portal_notbound_tags:
            curr_portal_notbound_tags_dict[elem.name] = elem
        curr_portal_notbound_tag_name_object_dict = {}
        for elem in curr_portal_notbound_tag_port_objects:
            curr_portal_notbound_tag_name_object_dict[elem.tag.name] = elem

        new_bound_tags = json_new['bound_tags']
        new_notbound_tags = json_new['notbound_tags']

        new_bound_tag_names = set(map(lambda x: x['tag_name'], new_bound_tags))
        new_notbound_tag_names = set(new_notbound_tags)

        curr_tag_names = curr_portal_bound_tag_names | curr_portal_notbound_tag_names
        new_tag_tames = new_bound_tag_names | new_notbound_tag_names

        deleted_tag_names = curr_tag_names - new_tag_tames
        added_tag_names = new_tag_tames - (new_tag_tames & curr_tag_names)

        # actually_deleted_tags = set()
        # for tag_name in deleted_tag_names:
        #     other_portal_with_deleted_tags = g.db.query(Portal.id).filter(Portal.id!=portal_id).\
        #         join(PortalDivision).\
        #         join(TagPortalDivision).\
        #         join(Tag).\
        #         filter(Tag.name==tag_name).first()
        #
        #     if not other_portal_with_deleted_tags:
        #         other_portal_with_deleted_tags = g.db.query(Portal.id).\
        #             filter(Portal.id!=portal_id).\
        #             join(TagPortal).\
        #             join(Tag).\
        #             filter(Tag.name==tag_name).first()
        #
        #         if not other_portal_with_deleted_tags:
        #             actually_deleted_tags.add(tag_name)

        actually_added_tags = set()
        for tag_name in added_tag_names:
            other_portal_with_added_tags = g.db.query(Portal.id).filter(Portal.id != portal_id). \
                join(PortalDivision). \
                join(TagPortalDivision). \
                join(Tag). \
                filter(Tag.name == tag_name).first()

            if not other_portal_with_added_tags:
                other_portal_with_added_tags = g.db.query(Portal.id). \
                    filter(Portal.id != portal_id). \
                    join(TagPortal). \
                    join(Tag). \
                    filter(Tag.name == tag_name).first()

                if not other_portal_with_added_tags:
                    actually_added_tags.add(tag_name)

        new_tags_dict = {}
        for tag_name in new_tag_tames:
            tag = g.db.query(Tag).filter_by(name=tag_name).join(TagPortal).first()
            if not tag:
                tag = g.db.query(Tag).filter_by(name=tag_name).join(TagPortalDivision).first()
            if not tag:
                tag = Tag(tag_name)
            new_tags_dict[tag_name] = tag

        # actually_added_tags_dict = {}
        # for tag_name in actually_added_tags:
        #     actually_added_tags_dict[tag_name] = Tag(tag_name)

        # user_company = UserCompany(status=STATUS.ACTIVE(), rights_int=COMPANY_OWNER_RIGHTS)
        # user_company.employer = self
        # g.user.employer_assoc.append(user_company)
        # g.user.companies.append(self)
        # self.youtube_playlists.append(YoutubePlaylist(name=self.name, company_owner=self))
        # self.save()

        # TODO: Now we have actually_deleted_tags and actually_added_tags

        # new_tags_dict = {}
        # for key in actually_added_tags_dict.keys():
        #     new_tags_dict[key] = actually_added_tags_dict[key]
        # for key in curr_portal_bound_tags_dict.keys():
        #     new_tags_dict[key] = curr_portal_bound_tags_dict[key]
        # for key in curr_portal_notbound_tags_dict.keys():
        #     new_tags_dict[key] = curr_portal_notbound_tags_dict[key]

        # curr_portal_bound_tag_port_div_objects
        # curr_portal_bound_port_div_id_tag_name_dict
        # new_bound_tags = json_new['bound_tags']
        # curr_portal_bound_port_div_id_tag_name_object_dict


        # curr_portal_bound_port_div_id_tag_name_object_dict = []
        # for elem in curr_portal_bound_tag_port_div_objects:
        #     curr_portal_bound_port_div_id_tag_name_object_dict.append(
        #         [{'portal_division_id': elem.portal_division_id,
        #          'tag_name': elem.tag.name},
        #          elem]
        #     )

        keys = list(map(dict, curr_portal_bound_port_div_id_tag_name_object_dict.keys()))
        add_tag_portal_bound_list = []
        for elem in json_new['bound_tags']:
            if elem not in keys:
                new_tag_port_div = TagPortalDivision(portal_division_id=elem['portal_division_id'])
                new_tag_port_div.tag = new_tags_dict[elem['tag_name']]
                add_tag_portal_bound_list.append(new_tag_port_div)

        delete_tag_portal_bound_list = []
        for elem in keys:
            if elem not in json_new['bound_tags']:
                delete_tag_portal_bound_list.append(
                    curr_portal_bound_port_div_id_tag_name_object_dict[frozenset(elem.items())]
                )

        add_tag_portal_notbound_list = []
        for elem in json_new['notbound_tags']:
            if elem not in curr_portal_notbound_tags:
                new_tag_port = TagPortal(portal_id=elem['portal_id'])
                new_tag_port.tag = new_tags_dict[elem['tag_name']]
                add_tag_portal_notbound_list.append(new_tag_port)

        delete_tag_portal_notbound_list = []
        for elem in curr_portal_notbound_tags:
            if elem not in json_new['notbound_tags']:
                delete_tag_portal_notbound_list.append(
                    curr_portal_notbound_tag_name_object_dict[elem.name]
                )

        g.db.add_all(add_tag_portal_bound_list + add_tag_portal_notbound_list)
        # read this: http://stackoverflow.com/questions/7892618/sqlalchemy-delete-subquery
        g.db.query(TagPortalDivision). \
            filter(TagPortalDivision.id.in_([x.id for x in delete_tag_portal_bound_list])). \
            delete(synchronize_session=False)
        g.db.query(TagPortal). \
            filter(TagPortal.id.in_([x.id for x in delete_tag_portal_notbound_list])). \
            delete(synchronize_session=False)
        g.db.expire_all()


        # TODO (AA to AA): not to forget to delete unused tags... New tags well be added.

        # for elem in delete_tag_portal_bound_list:
        #     g.db.delete(elem)
        g.db.commit()

        # portal.portal_bound_tags_dynamic = ...
        # portal.portal_notbound_tags_dynamic = ...

        # added_bound_tag_names = new_bound_tag_names - (new_bound_tag_names & curr_portal_bound_tag_names)
        # added_notbound_tag_names = new_notbound_tag_names - (new_notbound_tag_names & curr_portal_notbound_tag_names)

        # tag0_name = curr_portal_bound_tag_port_div_objects[0].tag.name
        # y = list(curr_portal_bound_tag_port_div_objects)         # Operations with portal_bound_tags_dynamic...
        flash('Portal tags successfully updated')

    tags = set(tag_portal_division.tag for tag_portal_division in portal.portal_bound_tags_select)
    tags_dict = {tag.id: tag.name for tag in tags}

    company = portal.own_company
    company_logo = company.logo_file_relationship.url() \
        if company.logo_file_id else '/static/images/company_no_logo.png'
    return {'portal': portal.to_dict('*, '
                                     'divisions.*, '
                                     'own_company.*, '
                                     'portal_bound_tags_select.*',
                                     # 'portal_notbound_tags_select.*'
                                     ),
            'company_logo': company_logo,
            'portal_id': portal_id,
            'tag': tags_dict}


@portal_bp.route('/portals_partners/<string:company_id>/', methods=['GET'])
@login_required
# @check_rights(simple_permissions([]))
def portals_partners(company_id):
    return render_template('company/portals_partners.html', company_id=company_id,
                           company=Company.get(company_id).get_client_side_dict())


# TODO: VK by OZ: remove company_* kwargs

@portal_bp.route('/portals_partners/<string:company_id>/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def portals_partners_load(json, company_id):
    portal = db(Company, id=company_id).one().own_portal
    portals_partners = [port.portal.to_dict('name, company_owner_id, id')
                        for port in MemberCompanyPortal.get_portals(
            company_id) if port]
    user_rights = list(g.user.user_rights_in_company(company_id))
    return {'portal': portal.to_dict('name') if portal else [],
            'portals_partners': portals_partners,
            'company_id': company_id,
            'user_rights': user_rights}


@portal_bp.route('/companies_partners/<string:company_id>/', methods=['GET'])
@login_required
# @check_rights(simple_permissions([]))
def companies_partners(company_id):
    return render_template('company/companies_partners.html', company_id=company_id,
                           company=Company.get(company_id).get_client_side_dict())


# TODO: VK by OZ: remove company_* kwargs


@portal_bp.route('/companies_partners/<string:company_id>/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def companies_partners_load(json, company_id):
    portal = db(Company, id=company_id).one().own_portal
    companies_partners = [comp.to_dict('company.id, company.name') for comp in
                          portal.company_members] if portal else []
    user_rights = list(g.user.user_rights_in_company(company_id))
    return {'portal': portal.to_dict('name') if portal else [],
            'companies_partners': companies_partners,
            'company_id': company_id,
            'user_rights': user_rights}


@portal_bp.route('/search_for_portal_to_join/', methods=['POST'])
@ok
@login_required
# @check_rights(simple_permissions([]))
def search_for_portal_to_join(json):
    portals_partners = Portal.search_for_portal_to_join(
        json['company_id'], json['search'])
    return portals_partners


@portal_bp.route('/publications/<string:company_id>/', methods=['GET'])
@login_required
# @check_rights(simple_permissions([]))
def publications(company_id):
    company = db(Company, id=company_id).one()
    company_logo = company.logo_file_relationship.url() \
        if company.logo_file_id else '/static/images/company_no_logo.png'

    return render_template(
        'portal/portal_publications.html',
        company=company.get_client_side_dict(),
        company_id=company_id,
        angular_ui_bootstrap_version='//angular-ui.github.io/bootstrap/ui-bootstrap-tpls-0.14.2.js',
        company_logo=company_logo
    )


# TODO: VK by OZ: remove company_* kwargs


@portal_bp.route('/publications/<string:company_id>/', methods=['POST'])
@login_required
# @check_rights(simple_permissions([]))
@ok
def publications_load(json, company_id):
    portal = db(Company, id=company_id).one().own_portal
    if not portal:
        return dict(portal_not_exist=True)
    current_page = json.get('page') or 1
    params = {'search_text': json.get('search_text'), 'portal_id': portal.id}
    if json.get('status'):
        params['status'] = json.get('status')
    subquery = ArticlePortalDivision.subquery_portal_articles(**params)
    if json.get('company_id'):
        subquery = subquery.filter(db(ArticleCompany,
                                      company_id=json.get('company_id'),
                                      id=ArticlePortalDivision.article_company_id).exists())
    articles, pages, current_page = pagination(subquery,
                                               page=current_page)

    companies = ArticlePortalDivision.get_companies_which_send_article_to_portal(portal.id)
    statuses = {status: status for status in ARTICLE_STATUS_IN_PORTAL.all}
    publications = []
    for a in articles:
        a = a.get_client_side_dict()
        del a['long']
        publications.append(a)

    return {'publications': publications,
            'companies': companies,
            'pages': {'total': pages,
                      'current_page': current_page,
                      'page_buttons': Config.PAGINATION_BUTTONS},
            'statuses': statuses}


@portal_bp.route('/publication_details/<string:article_id>/<string:company_id>', methods=['GET'])
@login_required
def publication_details(article_id, company_id):
    return render_template('company/publication_details.html',
                           company_id=company_id)


@portal_bp.route('/publication_details/<string:article_id>/<string:company_id>', methods=['POST'])
@login_required
@ok
def publication_details_load(json, article_id, company_id):
    statuses = {status: status for status in ARTICLE_STATUS_IN_PORTAL.all}
    article = db(ArticlePortalDivision, id=article_id).one().get_client_side_dict()
    new_status = ARTICLE_STATUS_IN_PORTAL.published \
        if article['status'] != ARTICLE_STATUS_IN_PORTAL.published \
        else ARTICLE_STATUS_IN_PORTAL.declined
    return {'article': article,
            'user_rights': list(g.user.user_rights_in_company(company_id)),
            'statuses': statuses,
            'new_status': new_status}


@portal_bp.route('/update_article_portal/<string:article_id>', methods=['POST'])
@login_required
@ok
def update_article_portal(json, article_id):
    db(ArticlePortalDivision, id=article_id).update({'status': json.get('new_status')})
    json['article']['status'] = json.get('new_status')
    json['new_status'] = ARTICLE_STATUS_IN_PORTAL.published \
        if json.get('new_status') != ARTICLE_STATUS_IN_PORTAL.published \
        else ARTICLE_STATUS_IN_PORTAL.declined
    return json


# @portal_bp.route('/submit_to_portal/<any(validate,save):action>/', methods=['POST'])
# @ok
# def submit_to_portal(json, action):
#     json['tags'] = ['money', 'sex', 'rock and roll']; tag position is important
#
# article = ArticleCompany.get(json['article']['id'])
# if action == 'validate':
#     return article.validate('update')
# if action == 'save':
#     portal_division_id = json['selected_division']
#     article_portal = article.clone_for_portal(portal_division_id, json['tags'])
#     article.save()
#     portal = article_portal.get_article_owner_portal(portal_division_id=portal_division_id)
#     return {'portal': portal.name}


@portal_bp.route('/submit_to_portal/', methods=['POST'])
# @login_required
# @check_rights(simple_permissions([]))
@ok
def submit_to_portal(json):
    # json['tags'] = ['money', 'sex', 'rock and roll']; tag position is important

    article = ArticleCompany.get(json['article']['id'])
    portal_division_id = json['selected_division']
    article_portal = article.clone_for_portal(portal_division_id, json['tags'])
    article.save()
    portal = article_portal.get_article_owner_portal(portal_division_id=portal_division_id)
    json['article'] = article_portal.to_dict(
        'id, title,short, cr_tm, md_tm, company_id, status, long,'
        'editor_user_id, company.name|id,portal_article.id,'
        'portal_article.division.name, portal_article.division.portal.name,portal_article.status')
    json.update({'portal': portal.name})
    return json
