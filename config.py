import os

basedir = os.path.abspath(os.path.dirname(__file__))
DEFAULT_KEY = "Now it's personal business"

# FIXME: mongodb connection is using production no matter whatever env it is in
class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or DEFAULT_KEY
    # TODO: remove password from here
    MONGODB_HOST = os.environ.get('MONGO_DATABASE_URL') or \
        "mongodb+srv://werewolf-god:password@cluster0.1qpql.mongodb.net/production?retryWrites=true&w=majority"

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('MAIL_ADMIN')

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MONGODB_HOST = os.environ.get('MONGO_DATABASE_URL') or \
        "mongodb+srv://werewolf-god:password@cluster0.1qpql.mongodb.net/development?retryWrites=true&w=majority"


class TestingConfig(Config):
    TESTING = True
    MONGODB_HOST = os.environ.get('MONGO_DATABASE_URL') or \
        "mongodb+srv://werewolf-god:password@cluster0.1qpql.mongodb.net/test?retryWrites=true&w=majority"

class ProductionConfig(Config):
    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}
