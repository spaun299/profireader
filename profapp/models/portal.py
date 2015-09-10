from ..constants.TABLE_TYPES import TABLE_TYPES
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
# from db_init import Base, g.db
from ..controllers import errors
from flask import g
from utils.db_utils import db
from .company import Company
from .pr_base import PRBase, Base


class Portal(Base, PRBase):
    __tablename__ = 'portal'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False,
                primary_key=True)
    name = Column(TABLE_TYPES['name'])
    host = Column(TABLE_TYPES['short_name'])
    company_owner_id = Column(TABLE_TYPES['id_profireader'],
                              ForeignKey('company.id'),
                              unique=True)
    portal_plan_id = Column(TABLE_TYPES['id_profireader'],
                            ForeignKey('portal_plan.id'))

    portal_layout_id = Column(TABLE_TYPES['id_profireader'],
                              ForeignKey('portal_layout.id'))

    layout = relationship('PortalLayout')
    divisions = relationship('PortalDivision', backref='portal',
                             primaryjoin='Portal.id=='
                                         'PortalDivision.portal_id')
    article = relationship('ArticlePortal', backref='portal',
                           uselist=False)
    companies = relationship('Company', secondary='company_portal')

    def __init__(self, name=None, companies=[],
                 portal_plan_id='55dcb92a-6708-4001-acca-b94c96260506',
                 company_owner_id=None, article=None,
                 host=None, divisions=[],
                 portal_layout_id='55e99785-bda1-4001-922f-ab974923999a'
                 ):
        self.name = name
        self.portal_plan_id = portal_plan_id
        self.company_owner_id = company_owner_id
        self.article = article
        self.host = host
        self.portal_layout_id = portal_layout_id
        self.divisions = divisions
        self.companies = companies

    def create_portal(self, company_id, division_name, division_type):

        if db(Portal, company_owner_id=company_id).count():
            raise errors.PortalAlreadyExist({
                'message': 'portal for company %(name)s',
                'data': self.get_client_side_dict()
            })

            raise errors.PortalAlreadyExist('portal for company already exists')
            # except errors.PortalAlreadyExist as e:
            #     details = e.args[0]
            #     print(details['message'])
        self.own_company = db(Company, id=company_id).one()
        self.save()
        self.divisions.append(PortalDivision.add_new_division(
            portal_id=self.id, name=division_name,
            division_type=division_type))
        company_assoc = CompanyPortal(
            company_portal_plan_id=self.portal_plan_id)
        company_assoc.portal = self
        company_assoc.company = self.own_company

        return self

    def get_client_side_dict(self, fields='id|name, divisions.*, '
                                          'layout.*'):
        return self.to_dict(fields)

    @staticmethod
    def search_for_portal_to_join(company_id, searchtext):
        return [port.get_client_side_dict() for port in
                db(Portal).filter(~db(CompanyPortal,
                                      company_id=company_id,
                                      portal_id=Portal.id).exists()
                                  ).filter(
                    Portal.name.ilike("%" + searchtext + "%")).all()]

    @staticmethod
    def own_portal(company_id):
        try:
            ret = db(Portal, company_owner_id=company_id).one()
            return ret
        except:
            return []

    @staticmethod
    def query_portal(portal_id):
        ret = db(Portal, id=portal_id).one()
        return ret

class PortalPlan(Base, PRBase):
    __tablename__ = 'portal_plan'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False,
                primary_key=True)
    name = Column(TABLE_TYPES['name'], nullable=False)

    def __init__(self, name=None):
        self.name = name


class PortalLayout(Base, PRBase):
    __tablename__ = 'portal_layout'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False,
                primary_key=True)
    name = Column(TABLE_TYPES['name'], nullable=False)
    path = Column(TABLE_TYPES['name'], nullable=False)

    def __init__(self, name=None):
        self.name = name


class CompanyPortal(Base, PRBase):
    __tablename__ = 'company_portal'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False,
                primary_key=True)
    company_id = Column(TABLE_TYPES['id_profireader'],
                        ForeignKey('company.id'))
    portal_id = Column(TABLE_TYPES['id_profireader'],
                       ForeignKey('portal.id'))
    company_portal_plan_id = Column(TABLE_TYPES['id_profireader'])
    portal = relationship(Portal, backref='company_assoc')
    company = relationship(Company, backref='portal_assoc')

    def __init__(self, company_id=None, portal_id=None,
                 company_portal_plan_id=None):
        self.company_id = company_id
        self.portal_id = portal_id
        self.company_portal_plan_id = company_portal_plan_id

    @staticmethod
    def all_companies_on_portal(portal_id):
        comp_port = db(CompanyPortal, portal_id=portal_id).all()
        return [db(Company, id=company.company_id).one() for company in
                comp_port] if comp_port else False

    @staticmethod
    def add_portal_to_company_portal(portal_plan_id,
                                     company_id,
                                     portal_id):
        return CompanyPortal(company_portal_plan_id=portal_plan_id,
                             company_id=company_id,
                             portal_id=portal_id)

    @staticmethod
    def apply_company_to_portal(company_id, portal_id):
        g.db.add(CompanyPortal(company_id=company_id,
                               portal_id=portal_id,
                               company_portal_plan_id=Portal().
                               query_portal(portal_id).
                               portal_plan_id))
        g.db.flush()

    @staticmethod
    def show_companies_on_my_portal(company_id):

        portal = Portal().own_portal(company_id)
        return CompanyPortal().all_companies_on_portal(portal.id) if \
            portal else []

    @staticmethod
    def get_portals(company_id):

        return db(CompanyPortal, company_id=company_id).all()


class PortalDivision(Base, PRBase):
    __tablename__ = 'portal_division'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    cr_tm = Column(TABLE_TYPES['timestamp'])
    md_tm = Column(TABLE_TYPES['timestamp'])
    portal_division_type_id = Column(
        TABLE_TYPES['id_profireader'],
        ForeignKey('portal_division_type.id'))
    portal_id = Column(TABLE_TYPES['id_profireader'],
                       ForeignKey('portal.id'))
    name = Column(TABLE_TYPES['short_name'], default='')

    def __init__(self, portal_division_type_id=None,
                 name=None, portal_id=None):
        self.portal_division_type_id = portal_division_type_id
        self.name = name
        self.portal_id = portal_id

    def get_client_side_dict(self, fields='id|name'):
        return self.to_dict(fields)

    @staticmethod
    def add_new_division(portal_id, name, division_type):
        return PortalDivision(portal_id=portal_id,
                              name=name,
                              portal_division_type_id=division_type)

class PortalDivisionType(Base, PRBase):

    __tablename__ = 'portal_division_type'
    id = Column(TABLE_TYPES['short_name'], primary_key=True)

    @staticmethod
    def get_division_types():
        return db(PortalDivisionType).all()

class UserPortalReader(Base, PRBase):
    __tablename__ = 'user_portal_reader'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    user_id = Column(TABLE_TYPES['id_profireader'],
                     ForeignKey('user.id'))
    company_id = Column(TABLE_TYPES['id_profireader'],
                        ForeignKey('company.id'))
    status = Column(TABLE_TYPES['id_profireader'])
    portal_plan_id = Column(TABLE_TYPES['id_profireader'],
                            ForeignKey('portal_plan.id'))

    def __init__(self, user_id=None, company_id=None, status=None,
                 portal_plan_id=None):
        self.user_id = user_id
        self.company_id = company_id
        self.status = status
        self.portal_plan_id = portal_plan_id
