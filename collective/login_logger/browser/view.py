# -*- coding: utf-8 -*-

import json
from AccessControl import Unauthorized
from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from collective.login_logger import Session
from collective.login_logger import messageFactory as _
from collective.login_logger.models import LoginRecord
from datetime import date, datetime, timedelta
from plone import api
from plone.memoize.view import memoize
from sqlalchemy import and_, not_
from sqlalchemy import func, distinct
from zope.component import getMultiAdapter
from zope.component.interfaces import ComponentLookupError


class UsersLoginLoggerView(BrowserView):
    
    ignored_groups = ('Administrators', 'Reviewers', 'AuthenticatedUsers', 'Site Administrators')
    try:
        group_whitelist = api.portal.get_registry_record('collective.login_logger.group_whitelist')
    except ComponentLookupError:
        group_whitelist = False
        
    def __init__(self, context, request):
        self.context = context
        self.request = request
        request.set('disable_border', True)
        self._form = None
        self.last_query_size = 0

    def __call__(self, *args, **kwargs):
        # import pdb;pdb.set_trace()
        self._form = kwargs or self.request.form
        if self._form.get('export'):
            self._exportCSV()
            return
        if self._form.get('json'):
            return self._exportJSON()
        if self._form.get('send'):
            if not self.can_use_contact_form():
                raise Unauthorized("You can't use the contact user feature")
            send_result = self._sendMessage()
            if send_result:
                self.request.response.redirect("%s/@@%s" % (self.context.absolute_url(),
                                                            self.__name__))
                return
        return self.index()

    def _sendMessage(self):
        """Send en email message to found email address"""
        subject = self._form.get('subject')
        message = self._form.get('message')
        results = self.search_results()
        plone_utils = getToolByName(self.context, 'plone_utils')
        if not subject or not message:
            plone_utils.addPortalMessage(_('send_message_missing_data',
                                           default=u"You must provide a subject and a text message "
                                                   u"for the mail to be sent"),
                                         type="error")
            return False
        results = [x['user_email'] for x in results if x['user_email']]
        if not results:
            plone_utils.addPortalMessage(_('no_users_found',
                                           default=u"Your search doesn't find any valid email address"),
                                         type="error")
            return False
        mail_host = getToolByName(self.context, 'MailHost')
        mfrom = getToolByName(self.context, 'portal_url').getPortalObject().getProperty('email_from_address')
        if not mfrom:
            plone_utils.addPortalMessage(_('mail_configuration_error',
                                           default=u"Cannot send messages. Check mailhost configuration."),
                                         type="error")
            return False
        for email in results:
            mail_host.secureSend(message, mto=email, mfrom=mfrom, subject=subject)
        plone_utils.addPortalMessage(_('mail_sent',
                                       default=u"Message sent to $count recipients",
                                       mapping={'count': len(results)}),
                                     type="info")
        return True

    @memoize
    def can_use_contact_form(self):
        sm = getSecurityManager()
        return sm.checkPermission('collective.login_logger: contact users', self.context)

    def _exportCSV(self):
        """Write a CSV output"""
        translate = lambda text: translation_service.utranslate(
            msgid=text,
            domain="collective.login_logger",
            context=context)

        context = self.context
        translation_service = getToolByName(context,'translation_service')
        response = self.request.response
        response.setHeader('Content-Type', 'text/csv')
        response.addHeader('Content-Disposition',
                           'attachment;filename=login-report-%s.csv' % datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        response.write(("%s,%s,%s,%s,%s\n" % (translate(u"User ID"),
                                              translate(u"Full Name"),
                                              translate(u"E-mail"),
                                              translate(u"Login count"),
                                              translate(u"Last login date"))).encode('utf-8'))
        results = self.search_results()
        for row in results:
            response.write(("%s,%s,%s,%s,%s\n" % (row.get('user_id'),
                                                  row.get('user_fullname'),
                                                  row.get('user_email'),
                                                  row.get('login_count'),
                                                  row.get('last_login_date'))).encode('utf-8'))

    def _exportJSON(self):
        """return an application/json output of the search"""
        response = self.request.response
        response.setHeader('Content-Type', 'application/json')
        response.addHeader('Content-Disposition',
                           'attachment;filename=login-report.json')
        results = self.search_results()
        output = []
        for row in results:
            output.append(dict(user_id=row.get('user_id'),
                               user_fullname=row.get('user_fullname'),
                               user_email=row.get('user_email'),
                               login_count=row.get('login_count'),
                               last_login_date=row.get('last_login_date').strftime('%Y-%m/%d %H:%M:%S')))
        return json.dumps(output)

    def default_start_date(self, canonical=False):
        today = date.today()
        monthago = today - timedelta(28)
        i = 0
        while today.day > monthago.day and i<3:
            i+=1
            monthago-=timedelta(1)
        if canonical:
            return monthago.strftime('%Y-%m-%d')
        return monthago.strftime('%d/%m/%Y')

    def default_end_date(self, canonical=False):
        if canonical:
            return date.today().strftime('%Y-%m-%d')
        return date.today().strftime('%d/%m/%Y')       

    @property
    def groups(self):
        '''
        Returns the groups of this site for filling the select in the form
        
        To add sample users do something like that
        [pas.userFolderAddUser(str(x).zfill(8), str(x).zfill(8), 
        ('Member',), (), ('Test 1',),) for x in range(4)]
        '''
        pas = getToolByName(self.context, 'acl_users')
        for group in pas.searchGroups():
            if not group['id'] in self.ignored_groups:
                yield group
                
    @property
    def groups_whitelist(self):
        '''
        Returns the groups of this site for filling the select in the form
        
        To add sample users do something like that
        [pas.userFolderAddUser(str(x).zfill(8), str(x).zfill(8), 
        ('Member',), (), ('Test 1',),) for x in range(4)]
        '''
        pas = getToolByName(self.context, 'acl_users')
        if group_whitelist:
            for group in self.groups:
                if group['id'] in self.group_whitelist:
                    yield group

    def _load_exclude_users(self, site_id):
        """Load user ids from login in the range. Used for performing negative logic"""
        exclude = self._form.get('exclude', '')
        if exclude:
            results = Session.query(distinct(LoginRecord.user_id)).filter(
                            LoginRecord.plone_site_id==site_id,
                            LoginRecord.timestamp>=self._start,
                            LoginRecord.timestamp<=self._end).all()
            return [user[0] for user in results]
        return None

    def _get_results(self, results):
        acl_users = getToolByName(self.context, 'acl_users')
        #self.last_query_size = len(results)
        self.last_query_size = 1  # hardcoded. using session.execute returns a resultproxy object which has no len
        

        processed = []
        for row in results:
            result = {'user_id': row[0],
                      'login_count': row[1],
                      'user_fullname': None,
                      'user_email': None,
                      'last_login_date': row[2]}
            # unluckily searchUsers is not returnig the email address
            #user = acl_users.searchUsers(login=row.user_id, exact_match=True)
            
            user = acl_users.getUserById(row[0])
            
            if user:
                result['user_fullname'] = user.getProperty('fullname')
                result['user_email'] = user.getProperty('email')
            processed.append(result)
        return processed

    def _sole_query(self, site_id):
        exclude_ids = self._load_exclude_users(site_id)
        datefilter = self._form.get('datefilter', '')
        user_id = self._form.get('user_id', '')
        group_id = self._form.get('group_id', '')
        qtext = 'select user_id,count(user_id),max(timestamp)  from logins_registry '
        qvars = {}
        
        if user_id:
            qtext += ' where user_id like :user_id '
            qvars['user_id'] = '%'+user_id+'%'
        
        if datefilter:
            if 'where' in qtext:
                qtext += ' and timestamp > :lodate and timestamp < :hidate '
            else:
                qtext += ' where timestamp > :lodate and timestamp < :hidate '
            
            qvars['lodate'] = self._start
            qvars['hidate'] = self._end
            
        if group_id:
            if 'where' in qtext:
                qtext += ' and group_id like :group_id '
            else:
                qtext += ' where group_id like :group_id '
            qvars['group_id'] = '%|'+group_id + '|%'
        
        qtext += ' group by user_id; '
        
        print qtext
        results = Session.execute(qtext,qvars)
              
        return self._get_results(results)
    
    
    def _prepare_interval(self):
        # we don't have strptime on Python 2.4
        sy,sm,sd = self._form.get('start_date').split('-')
        ey,em,ed = self._form.get('end_date').split('-')
        self._start = datetime(int(sy), int(sm), int(sd))
        self._end = datetime(int(ey), int(em), int(ed), 23, 59, 59)

    def search_results(self):
        """Search results"""
        self._prepare_interval()
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        
        try:
           return self._sole_query(portal.getId())
           
        except ComponentLookupError:
            self.request.response.redirect("%s/%s" % (portal.absolute_url(), self.__name__))
            portal.plone_utils.addPortalMessage(_('component_lookup_error',
                                                  default=u"Could not connect to the database engine. "
                                                          u"Please check your configuration"),
                                                type="error")
            return []

    def toLocalizedTime(self, date):
        ploneview = getMultiAdapter((self.context, self.request), name=u'plone')
        return ploneview.toLocalizedTime(date, long_format=True)
    
