# from db_init import g.db, Base
from ..constants.TABLE_TYPES import TABLE_TYPES
from sqlalchemy import Table, Column, Integer, Text, ForeignKey, String, Boolean, or_, and_, text
from sqlalchemy.orm import relationship, backref, make_transient, class_mapper
from sqlalchemy.sql import func
import datetime
import re
from flask import g
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event
from utils.validators import validators
from ..controllers import errors
from utils.db_utils import db
from html.parser import HTMLParser
from ..constants.SEARCH import RELEVANCE
import json

Base = declarative_base()

# this event is called whenever an attribute
# on a class is instrumented
# @event.listens_for(Base, 'attribute_instrument')
# def configure_listener(class_, key, inst):
#     if not hasattr(inst.property, 'columns'):
#         return
#     # this event is called whenever a "set"
#     # occurs on that instrumented attribute
#
#     @event.listens_for(inst, "set", retval=True)
#     def set_(instance, value, oldvalue, initiator):
#         validator = validators.get(inst.property.columns[0].type.__class__)
#         if validator:
#             return validator(value)
#         else:
#             return value
class Search(Base):
    __tablename__ = 'search'
    id = Column(TABLE_TYPES['id_profireader'], nullable=False, primary_key=True, unique=True)
    index = Column(TABLE_TYPES['id_profireader'], nullable=False)
    table_name = Column(TABLE_TYPES['short_text'], nullable=False)
    text = Column(TABLE_TYPES['text'], nullable=False)
    relevance = Column(TABLE_TYPES['int'], nullable=False)
    kind = Column(TABLE_TYPES['short_text'])

    def __init__(self, index=None, table_name=None, text=None, relevance=None, kind=None):
        # super(Search, self).__init__()
        self.index = index
        self.table_name = table_name
        self.text = text
        self.relevance = relevance
        self.kind = kind

    @staticmethod
    def search(*args, **kwargs):
        """ *args: dictionary with following values - class = sqlalchemy table class object,
                                                      filter: sqlalchemy filter with your own parameters,
                                                      on: fields parameter for join,
                                                      fields: (tuple) with fields name in table Search.kind,
                                                      join: subquery wich you want to join without filters.
            For example: {'class': Company, 'filter': ~db(User, company_id=1).exists(),
                          'on': Company.id=Portal.company_id, join=Article,
                          'fields' = (tuple) with fields name in table Search.kind}
            **kwargs: search_text = string text for search,
                      index = id """

        search_params = []
        for cls in args:
            search_params.append(and_(Search.kind.in_(cls['fields']),
                                 Search.text.ilike("%" + kwargs.get('search_text') + "%"),
                                 Search.table_name == cls['class'].__tablename__), )
        subquery_search = db(Search.index,
                             func.sum(Search.relevance).label('relevance'),
                             func.min(Search.table_name).label('table_name')).filter(
            or_(*search_params)).group_by(Search.index).subquery()
        # s = db(subquery_search).join(args[0]['class'], args[0]['class'].id == subquery_search.c.index)
        # subquery_search = subquery_search.join(args[1]['class'], args[1]['class'].id == Search.index)
        # print(getattr(args['cl']))
        # s = db(subquery_search).join(args[0]['class'], args[0]['class'].id == subquery_search.c.index)
        # a = next(cls for cls in args if cls['class'].__tablename__=='company')['class']
        cls_obj = lambda table_name: [cls for cls in args if cls['class'].__tablename__ == table_name][0].get('class')
        # print(a.about)
        # join_search = db(subquery_search).join(args[0]['class'], args[0]['class'].id == subquery_search.c.index)
        join_search = []
        for arg in args:
            join_params = text(arg.get('join')) if arg.get('join') else False
            filter_params = text(arg.get('filter')) if arg.get('filter') else False
            join_search.append(db(subquery_search).join(
                join_params or arg['class'],
                filter_params or (arg['class'].id == subquery_search.c.index)).subquery())
        # s = db(subquery_search).join(cls_obj(subquery_search.c.table_name), args[0]['class'].id == subquery_search.c.index)
        # print(join_search.all())

        for a in join_search:
            for b in db(a).all():
                print(b.relevance)


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        # TODO OZ BY VK : WHY WE ARE USING reset() method?
        # self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

    def strip_tags(self, html):
        self.feed(html)
        data = self.get_data()
        if data is '':
            data = html
        return data

class PRBase:
    def __init__(self):
        self.query = g.db.query_property()

    def validate(self, is_new):
        return {'errors': {}, 'warnings': {}, 'notices': {}}

    def delfile(self):
        g.db.delete(self)
        g.db.commit()

    def save(self):
        g.db.add(self)
        g.db.flush()
        return self

    # TODO: OZ by OZ: why we need two identical functions??!?!
    def updates(self, dictionary):
        for f in dictionary:
            setattr(self, f, dictionary[f])
        return self

    def attr(self, dictionary):
        for k in dictionary:
            setattr(self, k, dictionary[k])
        return self

    def detach(self):
        g.db.expunge(self)
        make_transient(self)
        self.id = None
        return self

    def expunge(self):
        g.db.expunge(self)
        return self

    def get_client_side_dict(self, fields='id',
                             more_fields=None):
        return self.to_dict(fields, more_fields)

    @classmethod
    def get(cls, id):
        return g.db().query(cls).get(id)

    def to_dict_object_property(self, object_name):
        object_property = getattr(self, object_name)
        if isinstance(object_property, datetime.datetime):
            return object_property.strftime('%c')
        elif isinstance(object_property, dict):
            return object_property
        else:
            return object_property

            # TODO: OZ by OZ:**kwargs should accept lambdafunction for fields formattings

    def to_dict(self, *args, prefix=''):
        ret = {}
        __debug = True

        req_columns = {}
        req_relationships = {}

        def add_to_req_relationships(column_name, columns):
            if column_name not in req_relationships:
                req_relationships[column_name] = []
            req_relationships[column_name].append(columns)

        def get_next_level(child, nextlevelargs, prefix, standard_fields_required):
            in_next_level_dict = child.to_dict(*nextlevelargs, prefix=prefix)
            if standard_fields_required:
                in_next_level_dict.update(child.get_client_side_dict())
            return in_next_level_dict

        for arguments in args:
            if arguments:
                for argument in re.compile('\s*,\s*').split(arguments):
                    columnsdevided = argument.split('.')
                    column_names = columnsdevided.pop(0)
                    for column_name in column_names.split('|'):
                        if len(columnsdevided) == 0:
                            req_columns[column_name] = True
                        else:
                            add_to_req_relationships(column_name, '.'.join(columnsdevided))

        columns = class_mapper(self.__class__).columns
        relations = {a: b for (a, b) in class_mapper(self.__class__).relationships.items()}

        for col in columns:
            if col.key in req_columns or (__debug and '*' in req_columns):
                ret[col.key] = self.to_dict_object_property(col.key)
                if col.key in req_columns:
                    del req_columns[col.key]
        if '*' in req_columns and __debug:
            del req_columns['*']

        if len(req_columns) > 0:
            columns_not_in_relations = list(set(req_columns.keys()) - set(relations.keys()))
            if len(columns_not_in_relations) > 0:
                raise ValueError(
                    "you requested not existing attribute(s) `%s%s`" % (
                        prefix, '`, `'.join(columns_not_in_relations),))
            else:
                for rel_name in req_columns:
                    add_to_req_relationships(rel_name, '~')
                    # raise ValueError("you requested for attribute(s) but "
                    #                  "relationships found `%s%s`" % (
                    #                      prefix, '`, `'.join(set(relations.keys()).
                    #                          intersection(
                    #                          req_columns.keys())),))

        for relationname, relation in relations.items():
            if relationname in req_relationships or (__debug and '*' in req_relationships):
                if relationname in req_relationships:
                    nextlevelargs = req_relationships[relationname]
                    del req_relationships[relationname]
                else:
                    nextlevelargs = req_relationships['*']
                related_obj = getattr(self, relationname)
                standard_fields_required = False
                while '~' in nextlevelargs:
                    standard_fields_required = True
                    nextlevelargs.remove('~')

                if relation.uselist:
                    add = [get_next_level(child, nextlevelargs, prefix + relationname + '.', standard_fields_required)
                           for child in related_obj]
                else:
                    add = None if related_obj is None else \
                        get_next_level(related_obj, nextlevelargs, prefix + relationname + '.', standard_fields_required)

                ret[relationname] = add

        if '*' in req_relationships:
            del req_relationships['*']

        if len(req_relationships) > 0:
            relations_not_in_columns = list(set(
                req_relationships.keys()) - set(columns))
            if len(relations_not_in_columns) > 0:
                raise ValueError(
                    "you requested not existing relation(s) `%s%s`" % (
                        prefix, '`, `'.join(relations_not_in_columns),))
            else:
                raise ValueError("you requested for relation(s) but "
                                 "column(s) found `%s%s`" % (
                                     prefix, '`, `'.join(set(columns).intersection(
                                         req_relationships)),))

        return ret

    @staticmethod
    def validate_before_update(mapper, connection, target):
        ret = target.validate(False)
        if len(ret['errors'].keys()):
            raise errors.ValidationException(ret)

    @staticmethod
    def validate_before_insert(mapper, connection, target):
        ret = target.validate(True)
        if len(ret['errors'].keys()):
            raise errors.ValidationException(ret)

    # @staticmethod
    # def validate_before_delete(mapper, connection, target):
    #     ret = target.validate('delete')
    #     if len(ret['errors'].keys()):
    #         raise errors.ValidationException(ret)

    @staticmethod
    def add_to_search(mapper, connection, target):

        if hasattr(target, 'search_fields'):
            target_fields = ','.join(target.search_fields.keys())
            target_dict = target.get_client_side_dict(fields=target_fields+',id')
            options = {'relevance': lambda field_name: getattr(RELEVANCE, field_name),
                       'processing': lambda text: MLStripper().strip_tags(text),
                       'index': lambda target_id: target_id}
            for field in target_fields.split(','):
                field_options = target.search_fields[field]
                field_options.update({key: options[key] for key in options
                                      if key not in field_options.keys()})
                g.db.add(Search(index=field_options['index'](target_dict['id']),
                                table_name=target.__tablename__,
                                relevance=field_options['relevance'](field), kind=field,
                                text=field_options['processing'](str(target_dict[field]))))

    @staticmethod
    def update_search_table(mapper, connection, target):

        if hasattr(target, 'search_fields'):
            options = {'processing': lambda text: MLStripper().strip_tags(text)}
            for field in target.search_fields:
                field_options = target.search_fields[field]
                field_options.update({key: options[key] for key in options
                                      if key not in field_options.keys()})
                db(Search, index=target.id, kind=field).update(
                    {'text': field_options['processing'](str(getattr(target, field)))})

    @classmethod
    def __declare_last__(cls):
        event.listen(cls, 'before_update', cls.validate_before_update)
        event.listen(cls, 'before_insert', cls.validate_before_insert)
        # event.listen(cls, 'before_delete', cls.validate_before_delete)
        event.listen(cls, 'after_insert', cls.add_to_search)
        event.listen(cls, 'before_update', cls.update_search_table)

#
#
#
#
# @event.listens_for(PRBase, 'before_insert')
# def validate_insert(mapper, connection, target):
#     ret = target.validate('insert')
#     if len(ret['errors'].keys()):
#         raise errors.ValidationException(ret)
#
# @event.listens_for(PRBase, 'before_delete')
# def validate_delete(mapper, connection, target):
#     ret = target.validate('delete')
#     if len(ret['errors'].keys()):
#         raise errors.ValidationException(ret)
#
# @event.listens_for(PRBase, 'before_update')
# def validate_update(mapper, connection, target):
#     ret = target.validate('update')
#     if len(ret['errors'].keys()):
#         raise errors.ValidationException(ret)
#
# event.listen(PRBase, 'before_update', validate_update)
# event.listen(ArticlePortal, 'before_insert', set_long_striped)
# event.listen(ArticleCompany, 'before_update', set_long_striped)
# event.listen(ArticleCompany, 'before_insert', set_long_striped)
