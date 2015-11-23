from .pr_base import PRBase, Base
from ..constants.TABLE_TYPES import TABLE_TYPES
from sqlalchemy import Column, ForeignKey, text
from utils.db_utils import db
import datetime
import re
from flask import g, request, current_app

class TranslateTemplate(Base, PRBase):
    __tablename__ = 'translate'

    languages = ['uk', 'en']

    id = Column(TABLE_TYPES['id_profireader'], primary_key=True, nullable=False)
    cr_tm = Column(TABLE_TYPES['timestamp'])
    ac_tm = Column(TABLE_TYPES['timestamp'])
    md_tm = Column(TABLE_TYPES['timestamp'])
    template = Column(TABLE_TYPES['short_name'], default='')
    name = Column(TABLE_TYPES['name'], default='')
    url = Column(TABLE_TYPES['keywords'], default='')
    uk = Column(TABLE_TYPES['name'], default='')
    en = Column(TABLE_TYPES['name'], default='')

    def __init__(self, id=None, template=None, url='', name=None, uk=None, en=None):
        self.id = id
        self.template = template
        self.name = name
        self.url = url
        self.uk = uk
        self.en = en

    @staticmethod
    def getTranslate(template, phrase, url=None):
        url_adapter = g.get_url_adapter()

        if url is None:
            url_adapter = g.get_url_adapter()
            rules = url_adapter.map._rules_by_endpoint.get(request.endpoint, ())
            url = '' if len(rules) < 1 else rules[0].rule
        else:
            try:
                from werkzeug.urls import url_parse

                parsed_url = url_parse(url)
                rules = url_adapter.match(parsed_url.path, method='GET', return_rule=True)
                url = rules[0].rule
            except Exception:
                url = ''

        if phrase[:2] == '__':
            phrase = phrase[2:]
            template = '__GLOBAL'

        exist = db(TranslateTemplate, template=template, name=phrase).first()

        lang = TranslateTemplate.languages[0]
        if g.user_dict['lang'] in TranslateTemplate.languages:
            lang = g.user_dict['lang']

        if exist:
            if current_app.config['DEBUG']:
                # TODO: OZ by OZ change ac without changing md (md changed by trigger)
                exist.ac_tm = None
                exist.save()
        else:
            exist = TranslateTemplate(template=template, name=phrase,
                                      url=url, **{l: phrase for l in TranslateTemplate.languages}).save()

        return getattr(exist, lang)

    @staticmethod
    def update_last_accessed(template, phrase):
        i = datetime.datetime.now()
        obj = [b for b in db(TranslateTemplate, template=template, name=phrase)]
        obj[0].updates({'ac_tm': i})
        return 'True'

    @staticmethod
    def delete(id):
        obj = TranslateTemplate.get(id)
        TranslateTemplate.delfile(obj)
        return 'True'

    @staticmethod
    def isExist(template, phrase):
        list = [f for f in db(TranslateTemplate, template=template, name=phrase)]
        return True if list else False

    @staticmethod
    def subquery_search(search_text=None, template=None, url=None, **kwargs):

        sub_query = db(TranslateTemplate)
        if template:
            sub_query = sub_query.filter_by(template=template)

        if url:
            sub_query = sub_query.filter_by(url=url)

        if search_text:
            sub_query = sub_query.filter(TranslateTemplate.name.ilike("%" + search_text + "%"))

        sub_query = sub_query.order_by(TranslateTemplate.template)

        return sub_query

    def get_client_side_dict(self, fields='id|name|uk|en|ac_tm|md_tm|cr_tm|template|url'):
        return self.to_dict(fields)
