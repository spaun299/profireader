from sqlalchemy import Integer, String, TIMESTAMP, SMALLINT, BOOLEAN, Column, ForeignKey, UnicodeText, BigInteger, \
    Binary, Float
from sqlalchemy.dialects.postgresql import BIGINT, INTEGER, JSON
from functools import reduce


class BinaryRightsMetaClass1(type):
    def all(self):
        return [name for (name, val) in self.__dict__.items() if name not in ['__doc__', '__module__']]

    def todict(self, bin):
        return {name: (True if (2 ** (type.__getattribute__(self, name) - 1) & bin) else False) for (name, val) in
                self.__dict__.items() if name not in ['__doc__', '__module__']}

    def tobin(self, dict):
        all_rights = {name: type.__getattribute__(self, name) for (name, val) in
                      self.__dict__.items() if name not in ['__doc__', '__module__']}
        ret = 0
        for (rightname, bitposition) in all_rights.items():
            if bitposition == -1:
                ret = 0x7fffffffffffffff
            else:
                ret = ret | ((2 ** (bitposition - 1)) if dict.get(rightname) else 0)
        return ret

    def __getattribute__(self, key):
        return type.__getattribute__(self, key) if key in ['or_', 'all', 'todict', 'tobin'] or (
            key[:2] == '__' and key[-2:] == '__') else key


class BinaryRights(metaclass=BinaryRightsMetaClass1):
    _ALL_RIGHT_IN_ADVANCE = -1
    pass


class RIGHTS(BIGINT):
    _rights_class = None

    def __init__(self, rights):
        if isinstance(rights, BinaryRightsMetaClass1):
            self._rights_class = rights
        else:
            raise Exception(
                    'rights attribute should be BinaryRights class')

        super(RIGHTS, self).__init__()

    def result_processor(self, dialect, coltype):
        def process(value):
            return self._rights_class.todict(value)

        return process

    def bind_processor(self, dialect):
        def process(array):
            return self._rights_class.tobin(array)

        return process

    def adapt(self, impltype):
        return RIGHTS(self._rights_class)


# class PRColumn(Column):
#
#     right_class = None
#
#     def __init__(self, *args, **kwargs):
#         if 'rights' in kwargs:
#             self.right_class = kwargs['rights']
#             args = [RIGHTS] + list(args)
#             del kwargs['rights']
#             pass
#
#         if 'searchable' in kwargs:
#             pass
#
#         Column.__init__(self, *args, **kwargs)




# read this about UUID:
# http://stackoverflow.com/questions/183042/how-can-i-use-uuids-in-sqlalchemy
# http://stackoverflow.com/questions/20532531/how-to-set-a-column-default-to-a-postgresql-function-using-sqlalchemy
TABLE_TYPES = {
    'binary_rights': RIGHTS,
    'id_profireader': String(36),

    'password_hash': String(128),  # String(128) SHA-256
    'token': String(128),
    'timestamp': TIMESTAMP,
    'id_soc_net': String(50),
    'role': String(36),
    'location': String(64),

    'boolean': BOOLEAN,
    'status': String(36),
    'rights': String(40),
    'bigint': BIGINT,
    'int': INTEGER,
    'position': INTEGER,
    'float': Float,

    # http://sqlalchemy-utils.readthedocs.org/en/latest/data_types.html#module-sqlalchemy_utils.types.phone_number
    # 'phone': PhoneNumberType(country_code='UA'),  # (country_code='UA')
    'phone': String(50),  # (country_code='UA')

    # http://sqlalchemy-utils.readthedocs.org/en/latest/data_types.html#module-sqlalchemy_utils.types.url
    # read also https://github.com/gruns/furl
    # 'link': URLType,  # user = User(website=u'www.example.com'),
    'link': String(100),  # user = User(website=u'www.example.com'),
    'email': String(100),
    'name': String(200),
    'subtitle': String(1000),
    'string_30': String(30),
    'short_name': String(50),
    'title': String(100),
    'short_text': String(120),
    'keywords': String(1000),
    'credentials': String(1000),
    'text': UnicodeText(length=65535),
    'gender': String(6),
    'language': String(3),
    'url': String(1000),  # URLType,
    'binary': Binary,
    'json': JSON
}
