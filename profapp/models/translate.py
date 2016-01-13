from .pr_base import PRBase, Base
from ..constants.TABLE_TYPES import TABLE_TYPES
from sqlalchemy import Column, ForeignKey, text
from utils.db_utils import db
import datetime
import re
from flask import g, request, current_app
from sqlalchemy.sql import expression
from .portal import Portal
from sqlalchemy.orm import relationship


class TranslateTemplate(Base, PRBase):
    __tablename__ = 'translate'

    languages = ['uk', 'en']

    id = Column(TABLE_TYPES['id_profireader'], primary_key=True, nullable=False)
    cr_tm = Column(TABLE_TYPES['timestamp'])
    ac_tm = Column(TABLE_TYPES['timestamp'])
    md_tm = Column(TABLE_TYPES['timestamp'])
    template = Column(TABLE_TYPES['short_name'], default='')
    allow_html = Column(TABLE_TYPES['text'], default='')
    name = Column(TABLE_TYPES['name'], default='')
    portal_id = Column(TABLE_TYPES['id_profireader'], ForeignKey('portal.id'))
    url = Column(TABLE_TYPES['keywords'], default='')
    uk = Column(TABLE_TYPES['name'], default='')
    en = Column(TABLE_TYPES['name'], default='')

    portal = relationship(Portal, uselist=False)

    exemplary_portal_id = '560b9fee-3d87-4001-87d9-ad0d4582dd02'

    def __init__(self, id=None, template=None, portal_id=portal_id, url='', name=None, uk=None, en=None, allow_html=''):
        self.id = id
        self.template = template
        self.name = name
        self.allow_html = allow_html
        self.url = url
        self.uk = uk
        self.en = en
        self.portal_id = portal_id

    @staticmethod
    def try_to_get_phrase(template, phrase, url, portal_id=None, allow_html=''):

        exist = db(TranslateTemplate, template=template, name=phrase, portal_id=portal_id).first()

        if portal_id and not exist:
            exist_for_another = db(TranslateTemplate, template=template, name=phrase,
                                   portal_id=TranslateTemplate.exemplary_portal_id).first()
            if not exist_for_another:
                exist_for_another = db(TranslateTemplate, template=template, name=phrase).filter(
                    TranslateTemplate.portal != None).order_by(expression.desc(TranslateTemplate.cr_tm)).first()
            if exist_for_another:
                exist = TranslateTemplate(template=template, name=phrase, portal_id=portal_id,
                                          url=url,
                                          **{l: getattr(exist_for_another, l) for l in
                                             TranslateTemplate.languages}).save()
                return exist

        if not exist:
            exist = TranslateTemplate(template=template, name=phrase, portal_id=portal_id, allow_html=allow_html,
                                      url=url, **{l: phrase for l in TranslateTemplate.languages}).save()
        return exist

    @staticmethod
    def try_to_guess_lang(translation):
        # lang = TranslateTemplate.languages[0]
        # if g.user_dict['lang'] in TranslateTemplate.languages:
        #     lang = g.user_dict['lang']
        return getattr(translation, g.lang)

    @staticmethod
    def try_to_guess_url(url):

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

        return url

    @staticmethod
    def getTranslate(template, phrase, url=None, allow_html=''):

        portal_id = g.portal_id

        url = TranslateTemplate.try_to_guess_url(url)

        (phrase, template) = (phrase[2:], '__GLOBAL') if phrase[:2] == '__' else (phrase, template)

        translation = TranslateTemplate.try_to_get_phrase(template, phrase, url, portal_id=portal_id,
                                                          allow_html=allow_html)

        if translation:
            if translation.allow_html != allow_html:
                translation.updates({'allow_html': allow_html})
            if current_app.config['DEBUG']:

                # TODO: OZ by OZ change ac without changing md (md changed by trigger)
                # ac updated without changing md

                i = datetime.datetime.now()
                if translation.ac_tm:
                    if i.timestamp() - translation.ac_tm.timestamp() > 86400:
                        translation.updates({'ac_tm': i})
                else:
                    translation.updates({'ac_tm': i})
            return TranslateTemplate.try_to_guess_lang(translation)
        else:
            return phrase

    @staticmethod
    def update_last_accessed(template, phrase):
        i = datetime.datetime.now()
        obj = db(TranslateTemplate, template=template, name=phrase).first()
        obj.updates({'ac_tm': i})
        return 'True'

    @staticmethod
    def change_allowed_html(template, phrase, allow_html):
        obj = db(TranslateTemplate, template=template, name=phrase).first()
        obj.updates({'allow_html': allow_html})
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
                sub_query = sub_query.filter_by(url=kwargs['filter']['url'])
            if 'template' in kwargs['filter']:
                sub_query = sub_query.filter_by(template=kwargs['filter']['template'])
        if 'search_text' in kwargs:
            if 'name' in kwargs['search_text']:
                sub_query = sub_query.filter(TranslateTemplate.name.ilike("%" + kwargs['search_text']['name'] + "%"))
            if 'uk' in kwargs['search_text']:
                sub_query = sub_query.filter(TranslateTemplate.uk.ilike("%" + kwargs['search_text']['uk'] + "%"))
            if 'en' in kwargs['search_text']:
                sub_query = sub_query.filter(TranslateTemplate.en.ilike("%" + kwargs['search_text']['en'] + "%"))
        if 'cr_tm' in kwargs['sort']:
            sub_query = sub_query.order_by(TranslateTemplate.cr_tm.asc()) if kwargs['sort']['cr_tm'] == 'asc' else sub_query.order_by(TranslateTemplate.cr_tm.desc())
        elif 'ac_tm' in kwargs['sort']:
            sub_query = sub_query.order_by(TranslateTemplate.ac_tm.asc()) if kwargs['sort']['ac_tm'] == 'asc' else sub_query.order_by(TranslateTemplate.ac_tm.desc())
        else:
            sub_query = sub_query.order_by(TranslateTemplate.cr_tm.desc())

        return sub_query

    def get_client_side_dict(self, fields='id|name|uk|en|ac_tm|md_tm|cr_tm|template|url|allow_html, portal.id|name',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    @staticmethod
    def getListGridDataTranslation(translations):
        grid_data = []
        for translate in translations:
            grid_data.append(translate.get_client_side_dict())
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
                'label': label[0],
                'id': id
            })
            n += 1
        return new_list
