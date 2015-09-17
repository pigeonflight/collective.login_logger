# -*- coding: utf-8 -*-

from ZODB.POSException import ConflictError
from collective.login_logger import Session, logger
from collective.login_logger.models import User, LoginRecord
from datetime import datetime
from sqlalchemy import and_
from zope.component import getSiteManager
import traceback
from plone import api
import transaction

def register_event(user, event):
    portal = getSiteManager().portal_url.getPortalObject()
    site_id = portal.getId()
    user_id = user.getId()
    groups = '|'+'|'.join(user.getGroups())+'|'
    timestamp = datetime.now()
    # import pdb;pdb.set_trace()
    try:
        # qtext = 'insert into logins_registry VALUES (:user_id, :plone_site_id, :group_id, :timestamp)'
        # qvars = {'user_id': user_id, 'plone_site_id': site_id, 'group_id': groups, 'timestamp': timestamp}
        # res = Session.execute(qtext,qvars)
        # transaction.commit() 
        if Session.query(User).filter(and_(User.user_id == user_id,
                                          User.plone_site_id == site_id)).count() == 0:
            user = User(user_id.decode('utf-8'), site_id.decode('utf-8'))
            Session.add(user)
        else:
            user = Session.query(User).filter(and_(User.user_id == user_id,
                                                  User.plone_site_id == site_id)).one()

        timestamp = datetime.now()
        record = LoginRecord(user_id.decode('utf-8'), site_id.decode('utf-8'),groups, timestamp)
        Session.add(record)
    except ConflictError:
        raise
    except Exception:
        logger.error("Unable to store login informations")
        print traceback.format_exc()
