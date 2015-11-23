from sqlalchemy import Integer, String, TIMESTAMP, SMALLINT, BOOLEAN, Column, ForeignKey, UnicodeText, BigInteger, Binary
from sqlalchemy.dialects.postgresql import BIGINT, INTEGER
from sqlalchemy_utils.types.phone_number import PhoneNumberType
from sqlalchemy_utils import URLType
# read this about UUID:
# http://stackoverflow.com/questions/183042/how-can-i-use-uuids-in-sqlalchemy
# http://stackoverflow.com/questions/20532531/how-to-set-a-column-default-to-a-postgresql-function-using-sqlalchemy
TABLE_TYPES = {
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

    # http://sqlalchemy-utils.readthedocs.org/en/latest/data_types.html#module-sqlalchemy_utils.types.phone_number
    # 'phone': PhoneNumberType(country_code='UA'),  # (country_code='UA')
    'phone': String(50),  # (country_code='UA')

    # http://sqlalchemy-utils.readthedocs.org/en/latest/data_types.html#module-sqlalchemy_utils.types.url
    # read also https://github.com/gruns/furl
    # 'link': URLType,  # user = User(website=u'www.example.com'),
    'link': String(100),  # user = User(website=u'www.example.com'),
    'email': String(100),
    'name': String(200),
    'string_30': String(30),
    'short_name': String(50),
    'title': String(100),
    'short_text': String(120),
    'keywords': String(1000),
    'credentials': String(1000),
    'text': UnicodeText(length=65535),
    'gender': String(6),
    'language': String(3),
    'avatar_url': String(100), #URLType,
    'binary': Binary
}
