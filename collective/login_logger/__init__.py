# -*- extra stuff goes here -*-

import logging
from sqlalchemy.ext import declarative

import zope.i18nmessageid
from z3c.saconfig import named_scoped_session

logger = logging.getLogger('collective.login_logger')
messageFactory = zope.i18nmessageid.MessageFactory("collective.login_logger")

ORMBase = declarative.declarative_base()
Session = named_scoped_session('plone_logins')
