from ..constants.TABLE_TYPES import TABLE_TYPES
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship, remote
from ..controllers import errors
from flask import g, jsonify
from utils.db_utils import db
# from .company import Company
from .pr_base import PRBase, Base
import re
from .tag import TagPortalDivision, Tag
from sqlalchemy import event
from ..constants.SEARCH import RELEVANCE
import itertools
from sqlalchemy import orm
import itertools
from config import Config
from .articles import ArticlePortalDivision
import simplejson
from .files import File
from profapp.controllers.errors import BadDataProvided


class Portal(Base, PRBase):
    __tablename__ = 'portal'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False,
                primary_key=True)
    name = Column(TABLE_TYPES['name'])
    host = Column(TABLE_TYPES['short_name'])
    lang = Column(TABLE_TYPES['short_name'])

    url_facebook = Column(TABLE_TYPES['url'])
    url_google = Column(TABLE_TYPES['url'])
    url_tweeter = Column(TABLE_TYPES['url'])
    url_linkedin = Column(TABLE_TYPES['url'])

    company_owner_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('company.id'), unique=True)
    # portal_plan_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('member_company_portal_plan.id'))
    portal_layout_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal_layout.id'))

    logo_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'))
    favicon_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'))

    layout = relationship('PortalLayout')

    advs = relationship('PortalAdv', uselist=True)

    divisions = relationship('PortalDivision',
                             # backref='portal',
                             order_by='desc(PortalDivision.position)',
                             primaryjoin='Portal.id==PortalDivision.portal_id')
    config = relationship('PortalConfig', back_populates='portal', uselist=False)

    divisions_lazy_dynamic = relationship('PortalDivision',
                                          order_by='desc(PortalDivision.position)',
                                          primaryjoin='Portal.id==PortalDivision.portal_id',
                                          lazy='dynamic')

    own_company = relationship('Company',
                               # back_populates='own_portal',
                               uselist=False)
    # articles = relationship('ArticlePortalDivision',
    #                         back_populates='portal',
    #                         uselist=False)
    articles = relationship('ArticlePortalDivision',
                            secondary='portal_division',
                            primaryjoin="Portal.id == PortalDivision.portal_id",
                            secondaryjoin="PortalDivision.id == ArticlePortalDivision.portal_division_id",
                            back_populates='portal',
                            uselist=False)

    company_members = relationship('MemberCompanyPortal',
                                   # secondary='member_company_portal'
                                   # back_populates='portal',
                                   # lazy='dynamic'
                                   )
    search_fields = {'name': {'relevance': lambda field='name': RELEVANCE.name},
                     'host': {'relevance': lambda field='host': RELEVANCE.host}}
    # see: http://docs.sqlalchemy.org/en/rel_0_9/orm/join_conditions.html#composite-secondary-joins
    # see: http://docs.sqlalchemy.org/en/rel_0_9/orm/join_conditions.html#creating-custom-foreign-conditions
    # see!!!: http://docs.sqlalchemy.org/en/rel_0_8/orm/relationships.html#association-object
    # see comment: http://stackoverflow.com/questions/17473117/sqlalchemy-relationship-error-object-has-no-attribute-c

    # def get_portal_bound_tags_load_func(self):
    #     return g.db.query('portal.id').with_parent(self)
    # .\
    # join(PortalDivision).\
    # join(TagPortalDivision).\
    # all()
    # portal_bound_tags_load_new = property(_get_portal_bound_tags_load_func)

    portal_bound_tags_dynamic = relationship('TagPortalDivision',
                                             secondary='portal_division',
                                             # secondary='join(Portal, PortalDivision, Portal.id == PortalDivision.portal_id).'
                                             # 'join(TagPortalDivision, TagPortalDivision.id == PortalDivision.portal_id)',
                                             primaryjoin='Portal.id==remote(PortalDivision.portal_id)',
                                             secondaryjoin='PortalDivision.id==remote(TagPortalDivision.portal_division_id)',
                                             # secondaryjoin='PortalDivision.tags_assoc == TagPortalDivision.id',
                                             # secondaryjoin='PortalDivision.portal_division_tags == TagPortalDivision.id',
                                             # viewonly=True,
                                             lazy='dynamic')

    portal_bound_tags_noload = relationship('TagPortalDivision',
                                            secondary='portal_division',
                                            # secondary='join(Portal, PortalDivision, Portal.id == PortalDivision.portal_id).'
                                            # 'join(TagPortalDivision, TagPortalDivision.id == PortalDivision.portal_id)',
                                            primaryjoin='Portal.id == remote(PortalDivision.portal_id)',
                                            secondaryjoin='PortalDivision.id == remote(TagPortalDivision.portal_division_id)',
                                            # secondaryjoin='PortalDivision.tags_assoc == TagPortalDivision.id',
                                            # secondaryjoin='PortalDivision.portal_division_tags == TagPortalDivision.id',
                                            # viewonly=True,
                                            lazy='noload')

    portal_bound_tags_select = relationship('TagPortalDivision',
                                            secondary='portal_division',
                                            # secondary='join(Portal, PortalDivision, Portal.id == PortalDivision.portal_id).'
                                            # 'join(TagPortalDivision, TagPortalDivision.id == PortalDivision.portal_id)',
                                            primaryjoin='Portal.id == remote(PortalDivision.portal_id)',
                                            secondaryjoin='PortalDivision.id == remote(TagPortalDivision.portal_division_id)',
                                            # secondaryjoin='PortalDivision.tags_assoc == TagPortalDivision.id',
                                            # secondaryjoin='PortalDivision.portal_division_tags == TagPortalDivision.id',
                                            # viewonly=True,
                                            )

    portal_notbound_tags_select = relationship('TagPortal')
    portal_notbound_tags_dynamic = relationship('TagPortal', lazy='dynamic')
    portal_notbound_tags_noload = relationship('TagPortal', lazy='noload')

    # d = relationship("D",
    #             secondary="join(B, D, B.d_id == D.id)."
    #                         "join(C, C.d_id == D.id)",
    #             primaryjoin="and_(A.b_id == B.id, A.id == C.a_id)",
    #             secondaryjoin="D.id == B.d_id")

    # tags_assoc = relationship('TagPortalDivision', back_populates='portal_division')

    # company = relationship(Company, secondary='article_company',
    #                        primaryjoin="ArticlePortalDivision.article_company_id == ArticleCompany.id",
    #                        secondaryjoin="ArticleCompany.company_id == Company.id",
    #                        viewonly=True, uselist=False)

    def __init__(self, name=None,
                 # portal_plan_id=None,
                 logo_file_id=None,
                 company_owner=None,
                 favicon_file_id=None,
                 lang='uk',
                 host=None, divisions=[], portal_layout_id=None):
        self.name = name
        self.lang = lang
        self.logo_file_id = logo_file_id
        self.favicon_file_id = favicon_file_id

        # self.company_owner_id = company_owner_id
        # self.articles = articles
        self.host = host
        self.divisions = divisions
        # self.portal_plan_id = portal_plan_id if portal_plan_id else db(MemberCompanyPortalPlan).first().id
        self.portal_layout_id = portal_layout_id if portal_layout_id else db(PortalLayout).first().id

        self.own_company = company_owner

        self.company_members = [
            MemberCompanyPortal(portal=self, company=company_owner, plan=db(MemberCompanyPortalPlan).first())]

        # self.own_company.company_portals = db(MemberCompanyPortalPlan).first()

        # db(MemberCompanyPortalPlan).first().portal_companies.add(MemberCompanyPortal(company=self.own_company))




        # self.company_assoc = [MemberCompanyPortal(portal = self,
        #                                     company = self.own_company,
        #                                     company_portal_plan_id=db(MemberCompanyPortalPlan).first().id)]


        pass

    def setup_created_portal(self, logo_file_id=None):
        # TODO: OZ by OZ: move this to some event maybe
        """This method create portal in db. Before define this method you have to create
        instance of class with parameters: name, host, portal_layout_id, company_owner_id,
        divisions. Return portal)"""

        # except errors.PortalAlreadyExist as e:
        #     details = e.args[0]
        #     print(details['message'])


        # self.company_assoc.portal =
        # self.company_assoc.company =

        for division in self.divisions:
            if division.portal_division_type_id == 'company_subportal':
                PortalDivisionSettingsCompanySubportal(
                    member_company_portal=division.settings['member_company_portal'],
                    portal_division=division).save()

        if logo_file_id:
            originalfile = File.get(logo_file_id)
            if originalfile:
                self.logo_file_id = originalfile.copy_file(
                    company_id=self.company_owner_id,
                    parent_folder_id=self.own_company.system_folder_file_id,
                    article_portal_division_id=None).save().id
        return self

    def get_value_from_config(self, key=None, division_name=None):
        """
        :param key: string, variable which you want to return from config
        optional:
            :param division_name: string, if provided return value from config for division this.
        :return: variable which you want to return from config
        """
        conf = getattr(self.config, key, None)
        if not conf:
            return Config.ITEMS_PER_PAGE
        values = simplejson.loads(conf)
        if division_name:
            ret = values.get(division_name)
        else:
            ret = values
        return ret

    def validate(self, is_new):
        ret = super().validate(is_new)
        if db(Portal, company_owner_id=self.own_company.id).filter(Portal.id != self.id).count():
            ret['errors']['form'] = 'portal for company already exists'
        if not re.match('[^\s]{3,}', self.name):
            ret['errors']['name'] = 'pls enter a bit longer name'
        if not re.match(
                '^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)+([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9]{1,})$',
                self.host):
            ret['errors']['host'] = 'pls enter valid host name'
        if not 'host' in ret['errors'] and db(Portal, host=self.host).filter(Portal.id != self.id).count():
            ret['warnings']['host'] = 'host already taken by another portal'

        grouped = {}

        for inddiv, div in enumerate(self.divisions):
            if not re.match('[^\s]{3,}', div.name):
                if not 'divisions' in ret['errors']:
                    ret['errors']['divisions'] = {}
                ret['errors']['divisions'][inddiv] = 'pls enter valid name'
            if div.portal_division_type_id in grouped:
                grouped[div.portal_division_type_id] += 1
            else:
                grouped[div.portal_division_type_id] = 1

        for check_division in db(PortalDivisionType).all():
            if check_division.id not in grouped:
                grouped[check_division.id] = 0
            if check_division.min > grouped[check_division.id]:
                ret['errors']['add_division'] = 'you need at least %s `%s`' % (check_division.min, check_division.id)
                if grouped[check_division.id] == 0:
                    ret['errors']['add_division'] = 'add at least one `%s`' % (check_division.id,)
            if check_division.max < grouped[check_division.id]:
                ret['errors']['add_division'] = 'you you can have only %s `%s`' % (
                    check_division.max, check_division.id)
        return ret

    def get_client_side_dict(self,
                             fields='id|name, divisions.*, layout.*, logo_file_id, favicon_file_id, company_owner_id, url_facebook',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    @staticmethod
    def search_for_portal_to_join(company_id, searchtext):
        """This method return all portals which are not partners current company"""
        return [port.get_client_side_dict() for port in
                db(Portal).filter(~db(MemberCompanyPortal,
                                      company_id=company_id,
                                      portal_id=Portal.id).exists()
                                  ).filter(Portal.name.ilike("%" + searchtext + "%")).all()]


class MemberCompanyPortal(Base, PRBase):
    __tablename__ = 'member_company_portal'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False, primary_key=True)
    company_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('company.id'))
    portal_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal.id'))

    member_company_portal_plan_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('member_company_portal_plan.id'))

    portal = relationship(Portal
                          # ,back_populates = 'company_members'
                          # , back_populates='member_companies'
                          )

    company = relationship('Company'
                           # ,back_populates = 'portal_members'
                           #                        ,backref = 'portal'
                           #                         ,backref='member_companies'
                           )

    plan = relationship('MemberCompanyPortalPlan'
                        # , backref='partner_portals'
                        )

    def __init__(self, company_id=None, portal=None, company=None, plan=None):
        if company_id and company:
            raise BadDataProvided
        if company_id:
            self.company_id = company_id
        else:
            self.company = company
        self.portal = portal
        self.plan = plan

    @staticmethod
    def apply_company_to_portal(company_id, portal_id):
        """Add company to MemberCompanyPortal table. Company will be partner of this portal"""
        g.db.add(MemberCompanyPortal(company_id=company_id,
                                     portal=db(Portal, id=portal_id).one(),
                                     plan=db(MemberCompanyPortalPlan).first()))
        g.db.flush()

    # @staticmethod
    # def show_companies_on_my_portal(company_id):
    #     """Return all companies partners at portal"""
    #     portal = Portal().own_portal(company_id).companies
    #     return portal

    @staticmethod
    def get_portals(company_id):
        """This method return all portals-partners current company"""
        return db(MemberCompanyPortal, company_id=company_id).all()

    # @staticmethod
    # def subquery_company_partners(company_id, search_text, **kwargs):
    #     sub_query = db(MemberCompanyPortal, company_id=company_id)
    #     if search_text:
    #         sub_query = sub_query.join(MemberCompanyPortal.portal)
    #         if 'portal' in search_text:
    #             sub_query = sub_query.filter(Portal.name.ilike("%" + search_text['portal'] + "%"))
    #         if 'company' in search_text:
    #             sub_query = sub_query.join(MemberCompanyPortal.company)
    #             sub_query = sub_query.filter(Company.name.ilike("%" + search_text['company'] + "%"))
    #         if 'link' in search_text:
    #             sub_query = sub_query.filter(Portal.host.ilike("%" + search_text['link'] + "%"))
    #     return sub_query


class ReaderUserPortalPlan(Base, PRBase):
    __tablename__ = 'reader_user_portal_plan'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False, primary_key=True)
    name = Column(TABLE_TYPES['name'], nullable=False, default='free')
    time = Column(TABLE_TYPES['bigint'], default=9999999)
    price = Column(TABLE_TYPES['float'], default=0)

    def __init__(self, name=None, time=None, price=None):
        super(ReaderUserPortalPlan, self).__init__()
        self.name = name
        self.time = time
        self.price = price


class PortalLayout(Base, PRBase):
    __tablename__ = 'portal_layout'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False, primary_key=True)
    name = Column(TABLE_TYPES['name'], nullable=False)
    path = Column(TABLE_TYPES['name'], nullable=False)

    def __init__(self, name=None):
        self.name = name

    def get_client_side_dict(self, fields='id|name',
                             more_fields=None):
        return self.to_dict(fields, more_fields)


class PortalAdv(Base, PRBase):
    __tablename__ = 'portal_adv'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False, primary_key=True)
    portal_id = Column(TABLE_TYPES['name'], ForeignKey('portal.id'), nullable=False)
    place = Column(TABLE_TYPES['name'], nullable=False)
    html = Column(TABLE_TYPES['text'], nullable=False)

    portal = relationship(Portal, uselist=False)

    def get_client_side_dict(self, fields='id,portal_id,place,html', more_fields=None):
        return self.to_dict(fields, more_fields)


class MemberCompanyPortalPlan(Base, PRBase):
    __tablename__ = 'member_company_portal_plan'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False, primary_key=True)
    name = Column(TABLE_TYPES['short_name'], default='')


class PortalDivision(Base, PRBase):
    __tablename__ = 'portal_division'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    cr_tm = Column(TABLE_TYPES['timestamp'])
    md_tm = Column(TABLE_TYPES['timestamp'])
    portal_division_type_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal_division_type.id'))
    portal_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal.id'))
    name = Column(TABLE_TYPES['short_name'], default='')
    position = Column(TABLE_TYPES['int'])

    portal_division_tags = relationship('Tag', secondary='tag_portal_division')
    tags_assoc = relationship('TagPortalDivision', back_populates='portal_division')

    portal = relationship(Portal, uselist=False)
    portal_division_type = relationship('PortalDivisionType', uselist=False)

    settings = None


    def __init__(self, portal=portal,
                 portal_division_type_id=portal_division_type_id,
                 name='',
                 settings=None,
                 position=0):
        self.position = position
        self.portal = portal
        self.portal_division_type_id = portal_division_type_id
        self.name = name
        self.settings = settings

    # @staticmethod
    # def after_attach(session, target):
    #     #     pass
    #     if target.portal_division_type_id == 'company_subportal':
    #         # member_company_portal = db(MemberCompanyPortal, company_id = target.settings['company_id'], portal_id = target.portal_id).one()
    #         addsettings = PortalDivisionSettingsCompanySubportal(
    #             member_company_portal=target.settings['member_company_portal'], portal_division=target)
    #         g.db.add(addsettings)
    #         # target.settings = db(PortalDivisionSettingsCompanySubportal).filter_by(
    #         #     portal_division_id=self.id).one()

    def search_filter(self):
        return and_(ArticlePortalDivision.portal_division_id.in_(
            db(PortalDivision.id, portal_id=portal.id)),
            ArticlePortalDivision.status ==
            ARTICLE_STATUS_IN_PORTAL.published)

    @orm.reconstructor
    def init_on_load(self):
        if self.portal_division_type_id == 'company_subportal':
            self.settings = db(PortalDivisionSettingsCompanySubportal).filter_by(
                portal_division_id=self.id).one()

    def get_client_side_dict(self, fields='id|name',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

        # @staticmethod
        # def add_new_division(portal_id, name, division_type):
        #     """Add new division to current portal"""
        #     return PortalDivision(portal_id=portal_id,
        #                           name=name,
        #                           portal_division_type_id=division_type)


# @event.listens_for(g.db, 'after_attach')
# event.listen(PortalDivision, 'after_attach', PortalDivision.after_attach)


class PortalDivisionSettingsCompanySubportal(Base, PRBase):
    __tablename__ = 'portal_division_settings_company_subportal'

    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    cr_tm = Column(TABLE_TYPES['timestamp'])
    md_tm = Column(TABLE_TYPES['timestamp'])

    portal_division_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal_division.id'))
    member_company_portal_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('member_company_portal.id'))

    member_company_portal = relationship(MemberCompanyPortal)

    portal_division = relationship(PortalDivision)

    def __init__(self, member_company_portal=member_company_portal, portal_division=portal_division):
        super(PortalDivisionSettingsCompanySubportal, self).__init__()
        self.portal_division = portal_division
        self.member_company_portal = member_company_portal


class PortalDivisionType(Base, PRBase):
    __tablename__ = 'portal_division_type'
    id = Column(TABLE_TYPES['short_name'], primary_key=True)
    min = Column(TABLE_TYPES['int'])
    max = Column(TABLE_TYPES['int'])

    @staticmethod
    def get_division_types():
        """Return all divisions on profireader"""
        return db(PortalDivisionType).all()


class PortalConfig(Base, PRBase):
    __tablename__ = 'portal_config'
    id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal.id'), primary_key=True)
    division_page_size = Column(TABLE_TYPES['credentials'])
    portal = relationship(Portal, back_populates='config', uselist=False)

    def __init__(self, page_size_for_divisions=None, portal=None):
        """
        optional:
            :parameter - page_size_for_divisions = dictionary with key = division name
                                                             and value = page size per this division
                       , default = all divisions have page size from global config. It will converts
                         to json.
        """
        super(PortalConfig, self).__init__()
        self.portal = portal
        self.page_size_for_divisions = page_size_for_divisions
        self.set_division_page_size()

    PAGE_SIZE_PER_DIVISION = 'division_page_size'

    def set_division_page_size(self, page_size_for_divisions=None):
        page_size_for_divisions = page_size_for_divisions or self.page_size_for_divisions
        config = db(PortalConfig, id=self.id).first()
        dps = dict()
        if config and page_size_for_divisions:
            dps = simplejson.loads(getattr(config, PortalConfig.PAGE_SIZE_PER_DIVISION))
            dps.update(page_size_for_divisions)
        elif page_size_for_divisions:
            for division in self.portal.divisions:
                if page_size_for_divisions.get(division.name):
                    dps[division.name] = page_size_for_divisions.get(division.name)
                else:
                    dps[division.name] = Config.ITEMS_PER_PAGE
        else:
            for division in self.portal.divisions:
                dps[division.name] = Config.ITEMS_PER_PAGE
        dps = simplejson.dumps(dps)
        self.division_page_size = dps


class UserPortalReader(Base, PRBase):
    __tablename__ = 'user_portal_reader'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    user_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('user.id'))
    portal_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal.id'))
    status = Column(TABLE_TYPES['id_profireader'], default='active', nullable=False)
    portal_plan_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('reader_user_portal_plan.id'))
    start_tm = Column(TABLE_TYPES['timestamp'])
    end_tm = Column(TABLE_TYPES['timestamp'])

    portal = relationship('Portal')
    user = relationship('User')

    def __init__(self, user_id=None, portal_id=None, status='active', portal_plan_id=None, start_tm=None,
                 end_tm=None):
        super(UserPortalReader, self).__init__()
        self.user_id = user_id
        self.portal_id = portal_id
        self.status = status
        self.start_tm = start_tm
        self.end_tm = end_tm
        self.portal_plan_id = portal_plan_id or g.db(ReaderUserPortalPlan.id).filter_by(name='free').one()[0]

    @staticmethod
    def get_portals_for_user():
        portals = db(Portal).filter(~(Portal.id.in_(db(UserPortalReader.portal_id, user_id=g.user_dict['id'])))).all()
        for portal in portals:
            yield (portal.id, portal.name, )


class FavoriteReaderArticle(Base, PRBase):
    __tablename__ = 'favorite_reader_article'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    user_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('user.id'))
    article_portal_division_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('article_portal_division.id'))

    def __init__(self, user_id=None, article_portal_division_id=None):
        super(FavoriteReaderArticle, self).__init__()
        self.user_id = user_id
        self.article_portal_division_id = article_portal_division_id

    def get_article_portal_division(self):
        return db(ArticlePortalDivision, id=self.article_portal_division_id).one()

    def get_portal_division(self):
        return db(PortalDivision).filter(PortalDivision.id == db(ArticlePortalDivision,
                                         id=self.article_portal_division_id).c.portal_division_id).one()
