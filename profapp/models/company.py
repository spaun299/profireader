from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Enum  # , update
from sqlalchemy.orm import relationship, backref
# from db_init import Base, db_session
from flask.ext.login import current_user
from sqlalchemy import Column, String, ForeignKey, update
from sqlalchemy.orm import relationship
from ..constants.TABLE_TYPES import TABLE_TYPES
from flask import g
from config import Config
from ..constants.STATUS import STATUS
from utils.db_utils import db
from sqlalchemy import CheckConstraint
from flask import abort
from .rights import Right
from ..controllers.request_wrapers import check_rights
from .files import File
from .pr_base import PRBase, Base, Search, Grid
from ..controllers import errors
from ..constants.STATUS import STATUS_NAME
from .rights import get_my_attributes
from functools import wraps
from .files import YoutubePlaylist
from ..constants.SEARCH import RELEVANCE
from .users import User
from ..models.portal import Portal
from ..models.portal import MemberCompanyPortal
from ..models.portal import UserPortalReader


class Company(Base, PRBase):
    __tablename__ = 'company'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    name = Column(TABLE_TYPES['name'], unique=True, nullable=False, default='')
    logo_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'), nullable=False)
    journalist_folder_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'), nullable=False)
    # corporate_folder_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'))
    system_folder_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'), nullable=False)
    #    portal_consist = Column(TABLE_TYPES['boolean'])
    author_user_id = Column(TABLE_TYPES['id_profireader'],
                            ForeignKey('user.id'),
                            nullable=False)
    country = Column(TABLE_TYPES['name'], nullable=False, default='')
    region = Column(TABLE_TYPES['name'], nullable=False, default='')
    address = Column(TABLE_TYPES['name'], nullable=False, default='')
    phone = Column(TABLE_TYPES['phone'], nullable=False, default='')
    phone2 = Column(TABLE_TYPES['phone'], nullable=False, default='')
    email = Column(TABLE_TYPES['email'], nullable=False, default='')
    short_description = Column(TABLE_TYPES['text'], nullable=False, default='')
    about = Column(TABLE_TYPES['text'], nullable=False, default='')
    status = Column(TABLE_TYPES['status'], nullable=False, default=STATUS.ACTIVE())
    lat = Column(TABLE_TYPES['float'], nullable=False, default=49.8418907)
    lon = Column(TABLE_TYPES['float'], nullable=False, default=24.0316261)

    portal_members = relationship('MemberCompanyPortal')

    own_portal = relationship('Portal',
                              back_populates='own_company', uselist=False,
                              foreign_keys='Portal.company_owner_id')

    # member_portal_plan = relationship('Portal',
    #                           back_populates='own_company', uselist=False,
    #                           foreign_keys='Portal.company_owner_id')

    user_owner = relationship('User', back_populates='companies')
    search_fields = {'name': {'relevance': lambda field='name': RELEVANCE.name},
                     'short_description': {'relevance': lambda field='short_description': RELEVANCE.short_description},
                     'about': {'relevance': lambda field='about': RELEVANCE.about},
                     'country': {'relevance': lambda field='country': RELEVANCE.country},
                     'phone': {'relevance': lambda field='phone': RELEVANCE.phone}}

    # TODO: AA by OZ: we need employees.position (from user_company table) (also search and fix #ERROR employees.position.2#)
    # ERROR employees.position.1#
    employees = relationship('User',
                             secondary='user_company',
                             back_populates='employers',
                             lazy='dynamic')

    youtube_playlists = relationship('YoutubePlaylist')

    # todo: add company time creation
    logo_file_relationship = relationship('File',
                                          uselist=False,
                                          backref='logo_owner_company',
                                          foreign_keys='Company.logo_file_id')

    def get_readers_for_portal(self, filters):
        query = g.db.query(User).join(UserPortalReader).join(UserPortalReader.portal).join(Portal.own_company).filter(
                Company.id == self.id)
        list_filters = []
        if filters:
            for filter in filters:
                list_filters.append({'type': 'text', 'value': filters[filter], 'field': eval("User." + filter)})
        query = Grid.subquery_grid(query, list_filters)
        return query

    @property
    def readers_query(self):
        return g.db.query(User.id,
                          User.profireader_email,
                          User.profireader_name,
                          User.profireader_first_name,
                          User.profireader_last_name
                          ). \
            join(UserPortalReader). \
            join(Portal). \
            join(self.__class__). \
            order_by(User.profireader_name). \
            filter(self.__class__.id == self.id)

        # get all users in company : company.employees
        # get all users companies : user.employers

    # TODO: VK by OZ I think this have to be moved to __init__ and dublication check to validation
    def setup_new_company(self):
        """Add new company to company table and make all necessary relationships,
        if company with this name already exist raise DublicateName"""
        if db(Company, name=self.name).count():
            raise errors.DublicateName({
                'message': 'Company name %(name)s already exist. Please choose another name',
                'data': self.get_client_side_dict()})

        user_company = UserCompany(status=UserCompany.STATUSES['ACTIVE'],
                                   rights=UserCompany.RIGHTS_AT_COMPANY_FOR_OWNER)
        user_company.employer = self
        g.user.employer_assoc.append(user_company)
        g.user.companies.append(self)
        self.youtube_playlists.append(YoutubePlaylist(name=self.name, company_owner=self))
        self.save()
        print(self)

        return self

    def get_portals_where_company_is_member(self):
        """This method return all portals-partners current company"""
        return [memcomport.portal for memcomport in db(MemberCompanyPortal, company_id=self.id).all()]

    def suspended_employees(self):
        """ Show all suspended employees from company. Before define method you should have
        query with one company """
        suspended_employees = [x.get_client_side_dict(more_fields='md_tm, employee, employee.employers')
                               for x in self.employee_assoc
                               if x.status == STATUS.DELETED()]
        return suspended_employees

    @staticmethod
    def query_company(company_id):
        """Method return one company"""
        ret = db(Company, id=company_id).one()
        return ret

    @staticmethod
    def search_for_company(user_id, searchtext):
        """Return all companies which are not current user employers yet"""
        query_companies = db(Company).filter(
                Company.name.like("%" + searchtext + "%")).filter.all()
        ret = []
        for x in query_companies:
            ret.append(x.dict())

        return ret
        # return PRBase.searchResult(query_companies)

        # @staticmethod
        # def update_comp(company_id, data):
        #     """Edit company. Pass to data parameters which will be edited"""
        #     company = db(Company, id=company_id)
        #     upd = {x: y for x, y in zip(data.keys(), data.values())}
        #     company.update(upd)

        # if passed_file:
        #     file = File(company_id=company_id,
        #                 parent_id=company.one().system_folder_file_id,
        #                 author_user_id=g.user_dict['id'],
        #                 name=passed_file.filename,
        #                 mime=passed_file.content_type)
        #     company.update(
        #         {'logo_file_id': file.upload(
        #             content=passed_file.stream.read(-1)).id}
        #     )
        # db_session.flush()

    @staticmethod
    def search_for_company_to_join(user_id, searchtext):
        """Return all companies which are not current user employers yet"""
        return [company.get_client_side_dict() for company in
                db(Company).filter(~db(UserCompany, user_id=user_id,
                                       company_id=Company.id).exists()).
                    filter(Company.name.ilike("%" + searchtext + "%")
                           ).all()]

    def get_client_side_dict(self,
                             fields='id,name,author_user_id,country,region,address,phone,phone2,email,short_description,journalist_folder_file_id,logo_file_id,about,lat,lon,own_portal.id|host',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    @staticmethod
    def subquery_company_partners(company_id, filters):
        sub_query = db(MemberCompanyPortal, company_id=company_id)
        list_filters = []
        if filters:
            sub_query = sub_query.join(MemberCompanyPortal.portal)
            if 'portal.name' in filters:
                list_filters.append({'type': 'text', 'value': filters['portal.name'], 'field': Portal.name})
            if 'link' in filters:
                list_filters.append({'type': 'text', 'value': filters['link'], 'field': Portal.host})
            if 'company' in filters:
                sub_query = sub_query.join(Company, Portal.company_owner_id == Company.id)
                list_filters.append({'type': 'text', 'value': filters['company'], 'field': Company.name})
            sub_query = Grid.subquery_grid(sub_query, list_filters)
        return sub_query


def forbidden_for_current_user(**kwargs):
    if 'user_id' in kwargs.keys():
        user_id = kwargs['user_id']
    elif 'user' in kwargs.keys():
        user_id = kwargs['user'].id
    else:
        user_id = None

    rez = current_user.id != user_id
    return rez


# TODO (AA to AA): Create a decorator that does this work!
# TODO: see the function params_for_user_company_business_rules.
# def simple_permissions(rights):
#     def business_rule(**kwargs):
#         # TODO (AA to AA): Implement json handling when json is available among other parameters.
#         params = kwargs['json'] if 'json' in kwargs.keys() else kwargs
#
#         keys = params.keys()
#         if 'company_id' in keys:
#             company_object = params['company_id']
#         elif 'company' in keys:
#             company_object = params['company']
#         else:
#             company_object = None
#         if 'user_id' in keys:
#             user_object = params['user_id']
#         elif 'user' in keys:
#             user_object = params['user']
#         else:
#             user_object = current_user
#
#         return UserCompany.permissions(rights, user_object, company_object)
#     return business_rule


class UserCompany(Base, PRBase):
    __tablename__ = 'user_company'

    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    user_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('user.id'), nullable=False)
    company_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('company.id'), nullable=False)

    status = Column(TABLE_TYPES['status'], default='APPLICANT')
    STATUSES = {'APPLICANT': 'APPLICANT', 'ACTIVE': 'ACTIVE', 'SUSPENDED': 'SUSPENDED', 'FIRED': 'FIRED'}

    RIGHT_AT_COMPANY = {
        'FILES_BROWSE': 2 ** (4 - 1),
        'FILES_UPLOAD': 2 ** (5 - 1),
        'FILES_DELETE_OTHERS': 2 ** (14 - 1),

        'MATERIALS_SUBMIT_TO_ANOTHER_PORTAL': 2 ** (8 - 1),
        'MATERIALS_EDIT_OTHERS': 2 ** (12 - 1),

        'PUBLICATION_PUBLISH_AT_OWN_PORTAL': 2 ** (2 - 1),
        'PUBLICATION_UNPUBLISH_AT_OWN_PORTAL': 2 ** (3 - 1),
        'PUBLICATION_SET_PRIORITY': 2 ** (11 - 1),

        'EMPLOYEE_CONFIRM_NEW': 2 ** (6 - 1),
        'EMPLOYEE_SUSPEND_UNSUSPEND': 2 ** (7 - 1),

        'COMPANY_REQUIRE_MEMBEREE_AT_PORTALS': 2 ** (15 - 1),
        'COMPANY_MANAGE_USER_RIGHTS': 2 ** (9 - 1),
        'COMPANY_EDIT_PROFILE': 2 ** (1 - 1),

        'EDIT_PORTAL_PROFILE': 2 ** (10 - 1),

        'PORTAL_MANAGE_READERS': 2 ** (16 - 1),
        'PORTAL_MANAGE_COMMENTS': 2 ** (18 - 1),
        'PORTAL_MANAGE_MEMBERS_COMPANIES': 2 ** (13 - 1)
    }

    RIGHTS_AT_COMPANY_DEFAULT = RIGHT_AT_COMPANY['FILES_BROWSE'] | RIGHT_AT_COMPANY[
        'MATERIALS_SUBMIT_TO_ANOTHER_PORTAL']
    RIGHTS_AT_COMPANY_FOR_OWNER = 0x7fffffffffffffff

    position = Column(TABLE_TYPES['short_name'], default='')

    md_tm = Column(TABLE_TYPES['timestamp'])
    works_since_tm = Column(TABLE_TYPES['timestamp'])

    banned = Column(TABLE_TYPES['boolean'], default=False, nullable=False)

    # _rights = Column(TABLE_TYPES['bigint'],
    #                  CheckConstraint('_rights >= 0',
    #                                  name='cc_unsigned_rights'),
    #                  default=0, nullable=False)

    _rights = Column(TABLE_TYPES['bigint'], default=RIGHTS_AT_COMPANY_DEFAULT, nullable=False)

    employer = relationship('Company', backref='employee_assoc')
    employee = relationship('User', backref=backref('employer_assoc', lazy='dynamic'))

    UniqueConstraint('user_id', 'company_id', name='uc_user_id_company_id')

    # todo (AA to AA): check handling md_tm

    def __init__(self, user_id=None, company_id=None, status=STATUS.NONACTIVE(), rights=0,
                 works_since_tm=works_since_tm):

        super(UserCompany, self).__init__()
        self.user_id = user_id
        self.company_id = company_id
        self.status = status
        self._rights = rights
        self.works_since_tm = works_since_tm

    @staticmethod
    def get(user_id=None, company_id=None):
        return db(UserCompany).filter_by(user_id=user_id if user_id else g.user.id, company_id=company_id).one()

    def get_statuses_avaible(self):
        return {s: True for s in self.STATUSES}

    def get_rights_avaible(self):
        return {s: True for s in self.RIGHT_AT_COMPANY}

    def get_rights(self):
        return PRBase.convert_rights_binary_to_dict(self._rights, self.RIGHT_AT_COMPANY)

    def get_client_side_dict(self, fields='id,user_id,company_id,works_since_tm,position,status',
                             more_fields=None):
        ret = self.to_dict(fields, more_fields)
        ret['rights'] = self.get_rights()
        return ret

    def set_client_side_dict(self, json):
        self.attr(g.filter_json(json, 'status|position'))
        self._rights = PRBase.convert_rights_dict_to_binary(json['rights'], self.RIGHT_AT_COMPANY)

    @property
    def rights_set(self):
        return Right.transform_rights_into_set(self.rights_int)

    @rights_set.setter
    #  rights_iterable may be a set or list
    def rights_set(self, rights_iterable=[]):
        rights_int = Right.transform_rights_into_integer(rights_iterable)
        self.rights_int = rights_int

    # @staticmethod
    # def user_in_company(user_id, company_id):
    #     """Return user (status, rights) in some company"""
    #     ret = db(UserCompany, user_id=user_id, company_id=company_id).one()
    #     return ret

    # do we provide any rights to user at subscribing? Not yet
    def subscribe_to_company(self):
        """Add user to company with non-active status. After that Employer can accept request,
        and add necessary rights, or reject this user. Method need instance of class with
        parameters : user_id, company_id, status"""
        if db(UserCompany, user_id=self.user_id,
              company_id=self.company_id).count():
            raise errors.AlreadyJoined({
                'message': 'user already joined to company %(name)s',
                'data': self.get_client_side_dict()})
        self.employee = User.user_query(self.user_id)
        self.employer = db(Company, id=self.company_id).one()
        return self

    @staticmethod
    def change_status_employee(company_id, user_id, status=STATUS.SUSPENDED()):
        """This method make status employee in this company suspended"""
        db(UserCompany, company_id=company_id, user_id=user_id). \
            update({'status': status})
        if status == STATUS.DELETED():
            UserCompany.update_rights(user_id=user_id,
                                      company_id=company_id,
                                      new_rights=()
                                      )
            # db_session.flush()

    @staticmethod
    def apply_request(company_id, user_id, bool):
        """Method which define when employer apply or reject request from some user to
        subscribe to this company. If bool == True(Apply) - update rights to basic rights in company
        and status to active, If bool == False(Reject) - just update status to rejected."""
        if bool == 'True':
            stat = STATUS.ACTIVE()
            UserCompany.update_rights(user_id,
                                      company_id,
                                      Config.BASE_RIGHT_IN_COMPANY)
        else:
            stat = STATUS.REJECTED()
        db(UserCompany, company_id=company_id, user_id=user_id,
           status=STATUS.NONACTIVE()).update({'status': stat})

    def has_rights(self, binary_right):
        return True if self.status == self.STATUSES['ACTIVE'] and (binary_right & self._rights) else False
        # user_company = self.employer_assoc.filter_by(company_id=company_id).first()
        # return user_company.rights_set if user_company and user_company.status == STATUS.ACTIVE() and user_company.employer.status == STATUS.ACTIVE() else []

    @staticmethod
    # @check_rights(simple_permissions([Right['manage_rights_company']]))
    # @check_rights(forbidden_for_current_user)
    def update_rights(user_id, company_id, new_rights, position=None):
        """This method defines for update user-rights in company. Apply list of rights"""
        new_rights_binary = Right.transform_rights_into_integer(new_rights)
        user_company = db(UserCompany, user_id=user_id, company_id=company_id)
        rights_dict = {'_rights': new_rights_binary}
        if position is not None:
            rights_dict['position'] = position
        # rights_dict = {'rights_int': new_rights_binary}  # TODO (AA to AA): does it work?
        user_company.update(rights_dict)

    #  corrected
    @staticmethod
    def show_rights(company_id):
        """Show all rights all users in current company with all statuses"""
        emplo = {}
        for user in db(Company, id=company_id).one().employees:
            user_company = user.employer_assoc.filter_by(company_id=company_id).one()
            emplo[user.id] = {'id': user.id,
                              'name': user.user_name,
                              # TODO (AA to AA): don't pass user object
                              'user': user,
                              'rights': {},
                              'companies': [user.employers],
                              'status': user_company.status,
                              'date': user_company.md_tm,
                              'position': user_company.position}

            # emplo[user.id]['rights'] = \
            #     Right.transform_rights_into_set(user_company.rights_set)

            emplo[user.id]['rights'] = user_company.rights_set
            # earlier it was a dictionary:
            # {'right_1': True, 'right_2': False, ...}
        return emplo

    @staticmethod
    def search_for_user_to_join(company_id, searchtext):
        """Return all users in current company which have characters
        in their name like searchtext"""
        return [user.get_client_side_dict(fields='profireader_name|id') for user in
                db(User).filter(~db(UserCompany, user_id=User.id, company_id=company_id).exists()).
                    filter(User.profireader_name.ilike("%" + searchtext + "%")).all()]

        # @staticmethod
        # def permissions(needed_rights_iterable, user_object, company_object):
        #
        #     needed_rights_int = Right.transform_rights_into_integer(needed_rights_iterable)
        #     # TODO: implement Anonymous User handling
        #     if not (user_object and company_object):
        #         raise errors.ImproperRightsDecoratorUse
        #
        #     user = user_object
        #     company = company_object
        #     if type(user_object) is str:
        #         user = g.db.query(User).filter_by(id=user_object).first()
        #         if not user:
        #             return abort(400)
        #     if type(company_object) is str:
        #         company = g.db.query(Company).filter_by(id=company_object).first()
        #         if not company:
        #             return abort(400)
        #
        #     user_company = user.employer_assoc.filter_by(company_id=company.id).first()
        #
        #     if not user_company:
        #         return False if needed_rights_iterable else True
        #
        #     if user_company.banned:  # or user_company.status != STATUS.ACTIVE():
        #         return False
        #
        #     if user_company:
        #         available_rights = user_company.rights_int
        #     else:
        #         return False
        #         # available_rights = 0
        #
        #     return True if available_rights & needed_rights_int == needed_rights_int else False
