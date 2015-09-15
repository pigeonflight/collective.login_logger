# -*- coding: utf-8 -*-

from zope.interface import Interface
from zope import schema
from collective.login_monitor import messageFactory as _

class ILoginMinitorLayer(Interface):
    """collective.login_monitor product layer"""

class IRegistry(Interface):
    group_white_list = schema.List(
            title=_(u"Group White List"),
            description=_(u"List the group ids which you want to be available to query, leave it blank to mean all"),
            required=False,
            value_type=schema.TextLine(title=_(u"item")))