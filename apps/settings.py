# -*- coding: utf-8 -*-
import os
from datetime import timedelta


# from secret_keys import CSRF_SECRET_KEY, SESSION_KEY


class Config(object):
    # Set secret keys for CSRF protection
    SECRET_KEY = "hi-stranger-y4-secret-key"
    debug = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)



class Production(Config):
    DEBUG = True
    CSRF_ENABLED = False
    ADMIN = os.environ['ADMIN_EMAIL']

    SQLALCHEMY_DATABASE_URI = os.environ['DB_URI']

    migration_directory = 'migrations'
