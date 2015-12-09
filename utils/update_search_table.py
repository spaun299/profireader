from profapp.models.articles import Article, ArticleCompany, ArticleCompanyHistory, \
    ArticlePortalDivision
from profapp.models.company import Company, UserCompany
from profapp.models.files import File, FileContent
from profapp.models.users import User
from sqlalchemy import create_engine
import re
from sqlalchemy.orm import scoped_session, sessionmaker
from config import ProductionDevelopmentConfig
classes = [ArticlePortalDivision, Article, ArticleCompany, ArticleCompanyHistory,
           Company, UserCompany, FileContent, File, User]
engine = create_engine(ProductionDevelopmentConfig.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
if __name__ == '__main__':
    for cls in classes:
        variables = vars(cls).copy()
        variables = variables.keys()

        for key in variables:
            if type(key) is not bool:
                keys = getattr(cls, str(key), None)
                try:
                    stripped_key = str(keys).split('.')[1]
                    type_of_field = str(cls.__table__.c[stripped_key].type)
                    chars_int = int(re.findall(r'\b\d+\b', type_of_field)[0])
                    if chars_int > 36:
                        for c in db_session.query(cls).all():
                            original_field = getattr(c, stripped_key)
                            modify_field = original_field + ' '
                            print(modify_field)
                except Exception as e:
                    pass
                    # print(e.__repr__())
    db_session.commit()
