from .pr_base import PRBase, Base
from ..constants.TABLE_TYPES import TABLE_TYPES
from sqlalchemy import Column, ForeignKey, text
from utils.db_utils import db
import datetime
import re
from flask import g, request, current_app
from sqlalchemy.sql import expression

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
                # ac updated without changing md

                i = datetime.datetime.now()
                if exist.ac_tm:
                    if i.timestamp()-exist.ac_tm.timestamp() > 86400:
                        exist.updates({'ac_tm': i})
                else:
                    exist.updates({'ac_tm': i})

        else:
            exist = TranslateTemplate(template=template, name=phrase,
                                      url=url, **{l: phrase for l in TranslateTemplate.languages}).save()
        return getattr(exist, lang)

    @staticmethod
    def update_last_accessed(template, phrase):
        i = datetime.datetime.now()
        obj = db(TranslateTemplate, template=template, name=phrase).first()
        obj.updates({'ac_tm': i})
        return 'True'

    @staticmethod
    def delete(objects):
        for obj in objects:
            f = db(TranslateTemplate, template=obj['template'], name=obj['name']).first()
            TranslateTemplate.delfile(f)
        return 'True'

    @staticmethod
    def isExist(template, phrase):
        list = [f for f in db(TranslateTemplate, template=template, name=phrase)]
        return True if list else False

    @staticmethod
    def subquery_search(template=None, url=None, **kwargs):
        sub_query = db(TranslateTemplate)
        if 'filter' in kwargs:
            if 'url' in kwargs['filter']:
                sub_query = sub_query.filter_by(url=kwargs['filter']['url'][0])
            if 'template' in kwargs['filter']:
                sub_query = sub_query.filter_by(template=kwargs['filter']['template'][0])
        if 'search_text' in kwargs:
            if 'name' in kwargs['search_text']:
                sub_query = sub_query.filter(TranslateTemplate.name.ilike("%" + kwargs['search_text']['name'] + "%"))
            if 'uk' in kwargs['search_text']:
                sub_query = sub_query.filter(TranslateTemplate.uk.ilike("%" + kwargs['search_text']['uk'] + "%"))
            if 'en' in kwargs['search_text']:
                sub_query = sub_query.filter(TranslateTemplate.en.ilike("%" + kwargs['search_text']['en'] + "%"))
        if 'sort' in kwargs:
            if 'cr_tm' in kwargs['sort']:
                sub_query = sub_query.order_by(TranslateTemplate.cr_tm.asc()) if kwargs['sort']['cr_tm'] == 'asc' else sub_query.order_by(TranslateTemplate.cr_tm.desc())
            if 'ac_tm' in kwargs['sort']:
                sub_query = sub_query.order_by(TranslateTemplate.ac_tm.asc()) if kwargs['sort']['ac_tm'] == 'asc' else sub_query.order_by(TranslateTemplate.ac_tm.desc())
        else:
            sub_query = sub_query.order_by(TranslateTemplate.template)
        # if kwargs['sort_creation_time']:
        #     sub_query = sub_query.order_by(TranslateTemplate.cr_tm.asc()) if kwargs['sort_creation_time'] == 'asc' else sub_query.order_by(TranslateTemplate.cr_tm.desc())
        # elif kwargs['sort_last_accessed_time']:
        #     sub_query = sub_query.order_by(TranslateTemplate.ac_tm.asc()) if kwargs['sort_last_accessed_time'] == 'asc' else sub_query.order_by(TranslateTemplate.ac_tm.desc())
        # else:
        #     sub_query = sub_query.order_by(TranslateTemplate.template)

        return sub_query

    def get_client_side_dict(self, fields='id|name|uk|en|ac_tm|md_tm|cr_tm|template|url',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    @staticmethod
    def getListGridDataTranslation(translations):
        grid_data = []
        for translate in translations:
            grid_data.append({
                            'cr_tm' : translate.cr_tm,
                            'ac_tm' : translate.ac_tm,
                            'template' : translate.template,
                            'url' : translate.url,
                            'name': translate.name,
                            'uk' : translate.uk,
                            'en' : translate.en
                        })
        return grid_data

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
