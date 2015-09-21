from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='collective.login_logger',
      version=version,
      description="Log login access to your Plone site",
      long_description=open("README.rst").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.rst")).read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 4.0",
        "Framework :: Plone :: 4.1",
        "Framework :: Plone :: 4.2",
        "Framework :: Plone :: 4.3",
        "Programming Language :: Python",
        ],
      keywords='plone plonegov login user access logger',
      author='Alteroo',
      author_email='sviluppoplone@redturtle.it',
      url='http://plone.org/products/collective.login_logger',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.CMFPlone',
          'SQLAlchemy',
          'collective.js.jqueryui',
          'z3c.saconfig',
          'plone.api',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
