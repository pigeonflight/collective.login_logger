# -*- coding: utf-8 -*-


def prepare(engine):
    from collective.login_logger import ORMBase
    import collective.login_logger.models
    ORMBase.metadata.create_all(engine)
