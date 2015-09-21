# -*- coding: utf-8 -*-

from collective.login_logger import logger

def uninstall(portal, reinstall=False):
    if not reinstall:
        setup_tool = portal.portal_setup
        setup_tool.runAllImportStepsFromProfile('profile-collective.login_logger:uninstall')
        logger.info("Uninstall done")
