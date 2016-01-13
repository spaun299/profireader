from sqlalchemy import Column, ForeignKey, text
from sqlalchemy.orm import relationship, aliased, backref
from sqlalchemy.sql import expression
from ..constants.TABLE_TYPES import TABLE_TYPES
# from db_init import db_session
from ..models.company import Company
from ..models.portal import PortalDivision, Portal, PortalDivisionType
from ..models.users import User
from ..models.files import File, FileContent
from ..models.tag import Tag, TagPortalDivision, TagPortalDivisionArticle
from config import Config
# from ..models.tag import Tag
from utils.db_utils import db
from .pr_base import PRBase, Base, MLStripper, Search
# from db_init import Base
from utils.db_utils import db
from ..constants.ARTICLE_STATUSES import ARTICLE_STATUS_IN_COMPANY, ARTICLE_STATUS_IN_PORTAL
from flask import g
from sqlalchemy.sql import or_, and_
from sqlalchemy.sql import expression
import re
from sqlalchemy import event
from ..controllers import errors
from ..constants.SEARCH import RELEVANCE


class ArticlePortalDivision(Base, PRBase):
    __tablename__ = 'article_portal_division'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True, nullable=False)
    article_company_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('article_company.id'))
    # portal_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal.id'))
    portal_division_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal_division.id'))
    image_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'), nullable=False)

    cr_tm = Column(TABLE_TYPES['timestamp'])
    title = Column(TABLE_TYPES['name'], default='')
    short = Column(TABLE_TYPES['text'], default='')
    long = Column(TABLE_TYPES['text'], default='')
    long_stripped = Column(TABLE_TYPES['text'], nullable=False)
    keywords = Column(TABLE_TYPES['keywords'], nullable=False)
    md_tm = Column(TABLE_TYPES['timestamp'])
    publishing_tm = Column(TABLE_TYPES['timestamp'])
    position = Column(TABLE_TYPES['position'])

    status = Column(TABLE_TYPES['id_profireader'], default=ARTICLE_STATUS_IN_PORTAL.published)

    division = relationship('PortalDivision',
                            backref=backref('article_portal_division', cascade="save-update, merge, delete"),
                            cascade="save-update, merge, delete")

    company = relationship(Company, secondary='article_company',
                           primaryjoin="ArticlePortalDivision.article_company_id == ArticleCompany.id",
                           secondaryjoin="ArticleCompany.company_id == Company.id",
                           viewonly=True, uselist=False)

    # portal_division_tags = relationship('TagPortalDivision',
    #                                     secondary='tag_portal_division_article',
    #                                     back_populates='articles')

    # tag_assoc_ = relationship('TagPortalDivisionArticle',
    #                                 back_populates='article_portal_division_select')
    search_fields = {'title': {'relevance': lambda field='title': RELEVANCE.title},
                     'short': {'relevance': lambda field='short': RELEVANCE.short},
                     'long': {'relevance': lambda field='long': RELEVANCE.long},
                     'keywords': {'relevance': lambda field='keywords': RELEVANCE.keywords}}
    tag_assoc_select = relationship('TagPortalDivisionArticle',
                                    back_populates='article_portal_division_select',
                                    cascade="save-update, merge, delete, delete-orphan",
                                    passive_deletes=True
                                    )

    def search_filter_default(self, division_id, company_id=None):
        """ :param division_id: string with id from table portal_division,
                   optional company_id: string with id from table company. If provided
                   , this function will check if ArticleCompany has relation with our class.
            :return: dict with prepared filter parameters for search method """
        division = db(PortalDivision, id=division_id).one()
        division_type = division.portal_division_type.id
        filter = None
        if division_type == 'index':
            filter = {'class': ArticlePortalDivision,
                      'filter': and_(ArticlePortalDivision.portal_division_id.in_(db(
                                     PortalDivision.id, portal_id=division.portal_id).filter(
                          PortalDivision.portal_division_type_id != 'events'
                      )), ArticlePortalDivision.status == ARTICLE_STATUS_IN_PORTAL.published),
                      'return_fields': 'default_dict', 'tags': True}
        elif division_type == 'news':
            if not company_id:
                filter = {'class': ArticlePortalDivision,
                          'filter': and_(ArticlePortalDivision.portal_division_id == division_id,
                                         ArticlePortalDivision.status ==
                                         ARTICLE_STATUS_IN_PORTAL.published),
                          'return_fields': 'default_dict', 'tags': True}
            else:
                filter = {'class': ArticlePortalDivision,
                          'filter': and_(ArticlePortalDivision.portal_division_id == division_id,
                                         ArticlePortalDivision.status ==
                                         ARTICLE_STATUS_IN_PORTAL.published,
                                         db(ArticleCompany, company_id=company_id,
                                            id=ArticlePortalDivision.article_company_id).exists()),
                          'return_fields': 'default_dict', 'tags': True}
        elif division_type == 'events':
            if not company_id:
                filter = {'class': ArticlePortalDivision,
                          'filter': and_(ArticlePortalDivision.portal_division_id == division_id,
                                         ArticlePortalDivision.status ==
                                         ARTICLE_STATUS_IN_PORTAL.published),
                          'return_fields': 'default_dict', 'tags': True}
            else:
                filter = {'class': ArticlePortalDivision,
                          'filter': and_(ArticlePortalDivision.portal_division_id == division_id,
                                         ArticlePortalDivision.status ==
                                         ARTICLE_STATUS_IN_PORTAL.published,
                                         db(ArticleCompany, company_id=company_id,
                                            id=ArticlePortalDivision.article_company_id).exists()),
                          'return_fields': 'default_dict', 'tags': True}
        return filter

    @property
    def tags(self):
        query = g.db.query(Tag.name). \
            join(TagPortalDivision). \
            join(TagPortalDivisionArticle). \
            filter(TagPortalDivisionArticle.article_portal_division_id == self.id)
        tags = list(map(lambda x: x[0], query.all()))
        return tags

    portal = relationship('Portal',
                          secondary='portal_division',
                          primaryjoin="ArticlePortalDivision.portal_division_id == PortalDivision.id",
                          secondaryjoin="PortalDivision.portal_id == Portal.id",
                          back_populates='articles',
                          uselist=False)

    def __init__(self, article_company_id=None, title=None, short=None, keywords=None, position=None,
                 long=None, status=None, portal_division_id=None, image_file_id=None
                 ):
        self.article_company_id = article_company_id
        self.title = title
        self.short = short
        self.keywords = keywords
        self.image_file_id = image_file_id
        self.long = long
        self.status = status
        self.position = position
        self.portal_division_id = portal_division_id
        # self.portal_id = portal_id

    def get_client_side_dict(self, fields='id|image_file_id|title|short|long|image_file_id|position|'
                                          'keywords|cr_tm|md_tm|'
                                          'status|publishing_tm, '
                                          'company.id|name, division.id|name, portal.id|name',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    @staticmethod
    def update_article_portal(article_portal_division_id, **kwargs):
        db(ArticlePortalDivision, id=article_portal_division_id).update(kwargs)

    @staticmethod
    def get_portals_where_company_send_article(company_id):

        # return db(ArticlePortalDivision, company_id=company_id).group_by.all()

        # all = {'name': 'All', 'id': 0}
        portals = {}
        # portals['0'] = {'name': 'All'}
        # portals.append(all)

        for article in db(ArticleCompany, company_id=company_id).all():
            for port in article.portal_article:
                portals[port.portal.id] = port.portal.name
        return portals

    @staticmethod
    def get_companies_which_send_article_to_portal(portal_id):
        # all = {'name': 'All', 'id': 0}
        companies = {}
        # companies.append(all)
        articles = g.db.query(ArticlePortalDivision). \
            join(ArticlePortalDivision.portal). \
            filter(Portal.id == portal_id).all()
        # for article in db(ArticlePortalDivision, portal_id=portal_id).all():
        for article in articles:
            companies[article.company.id] = article.company.name
        return companies

    def clone_for_company(self, company_id):
        return self.detach().attr({'company_id': company_id,
                                   'status': ARTICLE_STATUS_IN_COMPANY.
                                  submitted})

    @staticmethod
    def subquery_portal_articles(search_text=None, portal_id=None, **kwargs):
        sub_query = db(ArticlePortalDivision)
        if 'filter' in kwargs.keys():
             if 'publication_status' in kwargs['filter'].keys():
                sub_query = db(ArticlePortalDivision, status= kwargs['filter']['publication_status'])
             if 'company' in kwargs['filter'].keys():
                sub_query = sub_query.join(ArticlePortalDivision.company).filter(Company.id == kwargs['filter']['company'])
        sub_query = sub_query. \
            join(ArticlePortalDivision.division). \
            join(PortalDivision.portal). \
            filter(Portal.id == portal_id)
        if search_text:
            if 'title' in search_text:
                sub_query = sub_query.filter(ArticlePortalDivision.title.ilike("%" + search_text['title'] + "%"))
        if 'sort' in kwargs.keys():
            if 'date' in kwargs['sort'].keys():
                sub_query = sub_query.order_by(ArticlePortalDivision.publishing_tm.asc()) if kwargs[
                                                                                              'sort']['date'] == 'asc' else sub_query.order_by(
                 ArticlePortalDivision.publishing_tm.desc())

        else:
            sub_query = sub_query.order_by(expression.desc(ArticlePortalDivision.publishing_tm))
        return sub_query

    def manage_article_tags(self, new_tags):
        self.tag_assoc_select = []
        g.db.add(self)
        g.db.commit()  # TODO (AA to AA): this solution solves the problem but we MUST find another one to avoid commit on this stage!
        tags_portal_division_article = []
        for i in range(len(new_tags)):
            tag_portal_division_article = TagPortalDivisionArticle(position=i + 1)
            tag_portal_division = \
                g.db.query(TagPortalDivision). \
                    select_from(TagPortalDivision). \
                    join(Tag). \
                    filter(TagPortalDivision.portal_division_id == self.portal_division_id). \
                    filter(Tag.name == new_tags[i]).one()
            tag_portal_division_article.tag_portal_division = tag_portal_division
            tags_portal_division_article.append(tag_portal_division_article)
        self.tag_assoc_select = tags_portal_division_article

    def position_unique_filter(self):
        return and_(ArticlePortalDivision.portal_division_id == self.portal_division_id,
                    ArticlePortalDivision.position != None)


class ArticleCompany(Base, PRBase):
    __tablename__ = 'article_company'
    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    editor_user_id = Column(TABLE_TYPES['id_profireader'],
                            ForeignKey('user.id'), nullable=False)
    company_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('company.id'))
    article_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('article.id'))
    # created_from_version_id = Column(TABLE_TYPES['id_profireader'],
    # ForeignKey('article_version.id'))
    title = Column(TABLE_TYPES['title'], nullable=False)
    short = Column(TABLE_TYPES['text'], nullable=False)
    long = Column(TABLE_TYPES['text'], nullable=False)
    long_stripped = Column(TABLE_TYPES['text'], nullable=False)
    status = Column(TABLE_TYPES['status'], nullable=False)
    cr_tm = Column(TABLE_TYPES['timestamp'])
    md_tm = Column(TABLE_TYPES['timestamp'])
    image_file_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('file.id'), nullable=False)
    keywords = Column(TABLE_TYPES['keywords'], nullable=False)
    # TODO: OZ by OZ: we need keywords in ArticleCompany ??

    company = relationship(Company)
    editor = relationship(User)
    article = relationship('Article', primaryjoin="and_(Article.id==ArticleCompany.article_id)",
                           uselist=False)
    portal_article = relationship('ArticlePortalDivision',
                                  primaryjoin="ArticleCompany.id=="
                                              "ArticlePortalDivision."
                                              "article_company_id",
                                  backref='company_article')
    search_fields = {'title': {'relevance': lambda field='title': RELEVANCE.title},
                     'short': {'relevance': lambda field='short': RELEVANCE.short},
                     'long': {'relevance': lambda field='long': RELEVANCE.long},
                     'keywords': {'relevance': lambda field='keywords': RELEVANCE.keywords}}

    def get_client_side_dict(self,
                             fields='id|title|short|keywords|cr_tm|md_tm|article_id|image_file_id|status|company_id',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    def validate(self, is_new):
        ret = super().validate(is_new)
        # TODO: (AA to OZ): regexp doesn't work

        if not re.match('.*\S{3,}.*', self.title):
            ret['errors']['title'] = 'pls enter title longer than 3 letters'
        if not re.match('\S+.*', self.keywords):
            ret['warnings']['keywords'] = 'pls enter at least one keyword'
        return ret

    @staticmethod
    def get_companies_where_user_send_article(user_id):
        # all = {'name': 'All', 'id': 0}
        # companies = []
        # companies.append(all)
        companies = {}
        for article in db(Article, author_user_id=user_id).all():
            for comp in article.submitted_versions:
                companies[comp.company.id] = comp.company.name
                # companies.append(comp.company.get_client_side_dict(fields='id, name'))
        return companies #all, [dict(comp) for comp in set([tuple(c.items()) for c in companies])]

    @staticmethod
    def get_companies_for_article(article_id):
        companies = []
        for article in db(Article, id=article_id).all():
            for comp in article.submitted_versions:
                companies.append(comp.company.get_client_side_dict(fields='id, name'))
        return [dict(comp) for comp in set([tuple(c.items()) for c in companies])]

    def clone_for_company(self, company_id):
        return self.detach().attr({'company_id': company_id,
                                   'status': ARTICLE_STATUS_IN_COMPANY.
                                  submitted})

    @staticmethod
    def subquery_user_articles(search_text=None, user_id=None, **kwargs):
        own_article = aliased(ArticleCompany, name="OwnArticle")
        sub_query = db(Article, own_article.md_tm, author_user_id=user_id). \
            join(own_article,
                 and_(Article.id == own_article.article_id, own_article.company_id == None))
        article_filter = db(ArticleCompany, article_id=Article.id)
        if search_text:
            if 'title' in search_text:
                article_filter = article_filter.filter(ArticleCompany.title.ilike(
                    "%" + repr(search_text['title']).strip("'") + "%"))
        if 'filter' in kwargs.keys():
             if 'company' in kwargs['filter'].keys():
                article_filter = article_filter.filter(ArticleCompany.company_id==kwargs['filter']['company'])
             if 'status' in kwargs['filter'].keys():
                article_filter = article_filter.filter(ArticleCompany.status==kwargs['filter']['status'])
        if 'sort' in kwargs.keys():
            if 'date' in kwargs['sort'].keys():
                sub_query = sub_query.order_by(own_article.md_tm.asc()) if kwargs['sort']['date'] == 'asc' else sub_query.order_by(
                own_article.md_tm.desc())
        else:
            sub_query = sub_query.order_by(own_article.md_tm.desc())
        return sub_query.filter(article_filter.exists())

    @staticmethod
    def subquery_company_articles(search_text=None, company_id=None, **kwargs):
        sub_query = db(ArticleCompany, company_id=company_id)
        if 'filter' in kwargs.keys():
             if 'material_status' in kwargs['filter'].keys():
                sub_query = db(ArticleCompany, company_id=company_id, status=kwargs['filter']['material_status'])
             if 'publication_status' in kwargs['filter'].keys() or 'portals' in kwargs['filter'].keys():
                sub_query = sub_query.join(ArticlePortalDivision,
                                       ArticlePortalDivision.article_company_id == ArticleCompany.id)
                if 'publication_status' in kwargs['filter'].keys():
                    sub_query = sub_query.filter(ArticlePortalDivision.status == kwargs['filter']['publication_status'])
                if 'portals' in kwargs['filter'].keys():
                    sub_query = sub_query.join(PortalDivision,
                                           PortalDivision.id == ArticlePortalDivision.portal_division_id). \
                    filter(PortalDivision.portal_id == kwargs['filter']['portals'])
        if search_text:
            if 'title' in search_text:
                sub_query = sub_query.filter(ArticleCompany.title.ilike("%" + search_text['title'] + "%"))
        if 'sort' in kwargs.keys():
            if 'date' in kwargs['sort'].keys():
                sub_query = sub_query.order_by(ArticleCompany.md_tm.asc()) if kwargs[
                                                                              'sort']['date'] == 'asc' else sub_query.order_by(
                ArticleCompany.md_tm.desc())

        else:
            sub_query = sub_query.order_by(expression.desc(ArticleCompany.md_tm))
        return sub_query

        # self.portal_devision_id = portal_devision_id
        # self.article_company_id = article_company_id
        # self.title = title
        # self.short = short
        # self.long = long
        # self.status = status

    # def find_files_used(self):
    #     ret = [found.group(1) for found in re.findall('http://file001.profireader.com/([^/]*)/', self.long)]
    #     # if self.image_file_id:
    #     #     ret.append(self.image_file_id)
    #     return ret

    def clone_for_portal(self, portal_division_id, tag_names=[]):
        filesintext = {found[1]: True for found in
                       re.findall('(https?://file001.profireader.com/([^/]*)/)', self.long)}
        if self.image_file_id:
            filesintext[self.image_file_id] = True
        company = db(PortalDivision, id=portal_division_id).one().portal.own_company

        article_portal_division = \
            ArticlePortalDivision(
                title=self.title, short=self.short, long=self.long,
                portal_division_id=portal_division_id,
                article_company_id=self.id,
                keywords=self.keywords,
            )

        # TODO (AA to AA): old  tag_portal_division_article should be deleted.
        # TagPortalDivisionArticle(article_portal_division_id=None, tag_portal_division_id=None, position=None)

        article_portal_division.portal_division_tags = []

        tags_portal_division_article = []
        for i in range(len(tag_names)):
            tag_portal_division_article = TagPortalDivisionArticle(position=i + 1)
            tag_portal_division = \
                g.db.query(TagPortalDivision). \
                    select_from(TagPortalDivision). \
                    join(Tag). \
                    filter(TagPortalDivision.portal_division_id == portal_division_id). \
                    filter(Tag.name == tag_names[i]).one()

            tag_portal_division_article.tag_portal_division = tag_portal_division
            tags_portal_division_article.append(tag_portal_division_article)
        article_portal_division.tag_assoc_select = tags_portal_division_article

        article_portal_division.save()

        for file_id in filesintext:
            filesintext[file_id] = \
                File.get(file_id).copy_file(company_id=company.id,
                                            root_folder_id=company.system_folder_file_id,
                                            parent_id=company.system_folder_file_id,
                                            article_portal_division_id=article_portal_division.id).save().id

        if self.image_file_id:
            article_portal_division.image_file_id = filesintext[self.image_file_id]

        long_text = self.long
        for old_image_id in filesintext:
            long_text = long_text.replace('://file001.profireader.com/%s/' % (old_image_id,),
                                          '://file001.profireader.com/%s/' % ( filesintext[old_image_id],))

        article_portal_division.long = long_text

        return self

    def get_article_owner_portal(self, **kwargs):
        return [art_port_div.division.portal for art_port_div in self.portal_article if kwargs][0]

    @staticmethod
    def update_article(company_id, article_id, **kwargs):
        db(ArticleCompany, company_id=company_id, id=article_id).update(kwargs)


def set_long_striped(mapper, connection, target):
    target.long_stripped = MLStripper().strip_tags(target.long)


event.listen(ArticlePortalDivision, 'before_update', set_long_striped)
event.listen(ArticlePortalDivision, 'before_insert', set_long_striped)
event.listen(ArticleCompany, 'before_update', set_long_striped)
event.listen(ArticleCompany, 'before_insert', set_long_striped)


class Article(Base, PRBase):
    __tablename__ = 'article'

    id = Column(TABLE_TYPES['id_profireader'], primary_key=True)
    author_user_id = Column(TABLE_TYPES['id_profireader'],
                            ForeignKey('user.id'), nullable=False)

    submitted_versions = relationship(ArticleCompany,
                                      primaryjoin="and_(Article.id==ArticleCompany.article_id, "
                                                  "ArticleCompany.company_id!=None)")

    mine_version = relationship(ArticleCompany,
                                primaryjoin="and_(Article.id==ArticleCompany.article_id, "
                                            "ArticleCompany.company_id==None)",
                                uselist=False)

    def get_client_side_dict(self,
                             fields='id, mine_version|submitted_versions.id|title|short|'
                                    'cr_tm|md_tm|company_id|status|image_file_id, '
                                    'submitted_versions.editor.id|'
                                    'profireader_name, '
                                    'submitted_versions.company.name',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    def get_article_with_html_tag(self, text_into_html):
        article = self.get_client_side_dict()
        article['mine_version']['title'] = article['mine_version']['title'].replace(text_into_html,
                                                                                    '<span class=colored>%s</span>' % text_into_html)
        return article

    @staticmethod
    def search_for_company_to_submit(user_id, article_id, searchtext):
        # TODO: AA by OZ:    .filter(user_id has to be employee in company and
        # TODO: must have rights to submit article to this company)
        return [x.get_client_side_dict(fields='id,name') for x in db(Company).filter(~db(ArticleCompany).
                                                                                     filter_by(company_id=Company.id,
                                                                                               article_id=article_id).
                                                                                     exists()).filter(
            Company.name.ilike("%" + searchtext + "%")).all()]

    @staticmethod
    def save_edited_version(user_id, article_company_id, **kwargs):
        a = ArticleCompany.get(article_company_id)
        return a.attr(kwargs)

    @staticmethod
    def get_articles_for_user(user_id):
        return g.db.query(Article).filter_by(author_user_id=user_id).all()

    # @staticmethod
    # def subquery_articles_at_portal(portal_division_id=None, search_text=None):
    #
    #     if not search_text:
    #         sub_query = db(ArticlePortalDivision).order_by('publishing_tm').filter(text(
    #             ' "publishing_tm" < clock_timestamp() ')).filter_by(
    #             portal_division_id=portal_division_id,
    #             status=ARTICLE_STATUS_IN_PORTAL.published)
    #     else:
    #         sub_query = db(ArticlePortalDivision).order_by('publishing_tm').filter(text(
    #             ' "publishing_tm" < clock_timestamp() ')).filter_by(
    #             portal_division_id=portal_division_id,
    #             status=ARTICLE_STATUS_IN_PORTAL.published).filter(
    #             or_(
    #                 ArticlePortalDivision.title.ilike("%" + search_text + "%"),
    #                 ArticlePortalDivision.short.ilike("%" + search_text + "%"),
    #                 ArticlePortalDivision.long.ilike("%" + search_text + "%")))
    #     return sub_query

    @staticmethod
    def subquery_articles_at_portal(search_text=None, **kwargs):
        portal_id = None
        if 'portal_id' in kwargs.keys():
            portal_id = kwargs['portal_id']
            kwargs.pop('portal_id', None)
        # search_text = 'aa'
        # test = db(Search).filter(Search.text.ilike("%" + search_text + "%")).filter(
        #     Search.index == db(ArticlePortalDivision).filter(
        #         ArticlePortalDivision.portal_division_id == db(
        #             PortalDivision, portal_id=portal_id).first().id).first()).all()
        # for a in test:
        #     print(a)
        # print(**kwargs)
        # test = db(Search, table_name=ArticlePortalDivision.__tablename__).filter(Search.text.ilike("%" + search_text + "%")).filter(
        #     ArticlePortalDivision.portal_division_id in db(PortalDivision.id, portal_id=portal_id).all())
        # for a in test:
        #     print(a.text)

        sub_query = db(ArticlePortalDivision, status=ARTICLE_STATUS_IN_PORTAL.published, **kwargs). \
            order_by(ArticlePortalDivision.publishing_tm.desc()).filter(
            text(' "publishing_tm" < clock_timestamp() '))

        if portal_id:
            sub_query = sub_query.join(PortalDivision).join(Portal).filter(Portal.id == portal_id)

        if search_text:
            sub_query = sub_query. \
                filter(or_(ArticlePortalDivision.title.ilike("%" + search_text + "%"),
                           ArticlePortalDivision.short.ilike("%" + search_text + "%"),
                           ArticlePortalDivision.long_stripped.ilike("%" + search_text + "%")))
        return sub_query

    # @staticmethod
    # def get_articles_for_portal(page_size, portal_division_id,
    #                             pages, page=1, search_text=None):
    #     page -= 1
    #     if not search_text:
    #         query = g.db.query(ArticlePortalDivision).order_by('publishing_tm').filter(text(
    #             ' "publishing_tm" < clock_timestamp() ')).filter_by(
    #             portal_division_id=portal_division_id,
    #             status=ARTICLE_STATUS_IN_PORTAL.published)
    #     else:
    #         query = g.db.query(ArticlePortalDivision).order_by('publishing_tm').filter(text(
    #             ' "publishing_tm" < clock_timestamp() ')).filter_by(
    #             portal_division_id=portal_division_id,
    #             status=ARTICLE_STATUS_IN_PORTAL.published).filter(
    #             or_(
    #                 ArticlePortalDivision.title.ilike("%" + search_text + "%"),
    #                 ArticlePortalDivision.short.ilike("%" + search_text + "%"),
    #                 ArticlePortalDivision.long.ilike("%" + search_text + "%")))
    #
    #     if page_size:
    #         query = query.limit(page_size)
    #     if page:
    #         query = query.offset(page*page_size) if int(page) in range(
    #             0, int(pages)) else query.offset(pages*page_size)
    #
    #     return query

    @staticmethod
    def get_one_article(article_id):
        article = g.db.query(ArticleCompany).filter_by(id=article_id).one()
        return article

    @staticmethod
    def get_articles_submitted_to_company(company_id):
        articles = g.db.query(ArticleCompany).filter_by(company_id=company_id).all()
        return articles if articles else []

    @staticmethod
    def list_for_grid_tables(list, add_param, is_dict):
        new_list = []
        n = 1
        if add_param:
            new_list.append(add_param)
            n = 2
        if is_dict == False:
            list.sort()
        for s in list:
            label = list[s] if is_dict else s
            id = s if is_dict else ''
            new_list.append({
                'value': str(n),
                'label': label,
                'id': id
            })
            n += 1
        return new_list

    @staticmethod
    def getListGridDataMaterials(articles):
        grid_data = []
        for article in articles:
            allowed_statuses = []
            art_stats = ARTICLE_STATUS_IN_COMPANY.can_user_change_status_to(article.status)
            for s in art_stats:
                allowed_statuses.append({'id': s, 'value': s})
            port = 'not sent' if len(article.portal_article) == 0 else ''
            grid_data.append({'date': article.md_tm,
                              'title': article.title,
                              'portals': port,
                              'publication_status': '',
                              'material_status': article.status,
                              'id': str(article.id),
                              'level': True,
                              'allowed_status': allowed_statuses})
            if article.portal_article:
                i = 0
                for portal in article.portal_article:
                    grid_data.append({'date': '',
                                      'title': '',
                                      'portals': portal.portal.name,
                                      'publication_status': portal.status,
                                      'material_status': '',
                                      'id': portal.id,
                                      'level': False})
        return grid_data

    @staticmethod
    def getListGridDataPublication(articles):
        publications = []
        for a in articles:
            a = a.get_client_side_dict()
            if a.get('long'):
                del a['long']
            publications.append(a)
        grid_data = []
        for article in publications:
            allowed_statuses = []
            art_stats = ARTICLE_STATUS_IN_PORTAL.can_user_change_status_to(article['status'])
            for s in art_stats:
                allowed_statuses.append({'id': s, 'value': s})
            port = article['company']['name'] if article['company']['name'] else 'Not sent to any company yet'
            grid_data.append({'date': article['publishing_tm'],
                              'title': article['title'],
                              'company': port,
                              'publication_status': article['status'],
                              'id': str(article['id']),
                              'level': True,
                              'allowed_status': allowed_statuses})
        return grid_data

    @staticmethod
    def getListGridDataArticles(articles):
        articles_drid_data = []
        for (article, time) in articles:
            companies_for_article = ArticleCompany.get_companies_for_article(article.id)
            article_dict = article.get_client_side_dict()
            capm = '' if len(companies_for_article) > 0 else 'Not sent to any company yet'
            st = '' if len(article_dict['submitted_versions']) > 0 else 'Not sent'
            article_dict['md_tm'] = time
            articles_drid_data.append({'date': article_dict['md_tm'],
                                       'title': article_dict['mine_version']['title'],
                                       'company': capm,
                                       'status': st,
                                       'id': str(article_dict['id']),
                                       'level': True})
            if companies_for_article:
                i = 0
                for child in companies_for_article:
                    st = article_dict['submitted_versions'][i]['status'] if len(
                        article_dict['submitted_versions']) > 0 else 'Not sent'
                    articles_drid_data.append({'date': '',
                                               'title': '',
                                               'company': child['name'],
                                               'status': st,
                                               'id': '',
                                               'level': False})
                    i += 1
        return articles_drid_data
        # for article in articles:
        #     article.possible_new_statuses = ARTICLE_STATUS_IN_COMPANY.\
        #         can_user_change_status_to(article.status)


class ArticleCompanyHistory(Base, PRBase):
    __tablename__ = 'article_company_history'
    id = Column(TABLE_TYPES['bigint'], primary_key=True)
    editor_user_id = Column(TABLE_TYPES['id_profireader'])
    company_id = Column(TABLE_TYPES['id_profireader'])
    name = Column(TABLE_TYPES['name'])
    short = Column(TABLE_TYPES['text'], default='')
    long = Column(TABLE_TYPES['text'], default='')
    article_company_id = Column(TABLE_TYPES['id_profireader'])
    article_id = Column(TABLE_TYPES['id_profireader'])

    def __init__(self, editor_user_id=None, company_id=None, name=None,
                 short=None, long=None, article_company_id=None,
                 article_id=None):
        super(ArticleCompanyHistory, self).__init__()
        self.editor_user_id = editor_user_id
        self.company_id = company_id
        self.name = name
        self.short = short
        self.long = long
        self.article_company_id = article_company_id
        self.article_id = article_id
