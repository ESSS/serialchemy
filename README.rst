======================================================================
Serialchemy
======================================================================


.. image:: https://img.shields.io/pypi/v/serialchemy.svg
    :target: https://pypi.python.org/pypi/serialchemy

.. image:: https://img.shields.io/pypi/pyversions/serialchemy.svg
    :target: https://pypi.org/project/serialchemy

.. image:: https://img.shields.io/travis/ESSS/serialchemy.svg
    :target: https://travis-ci.org/ESSS/serialchemy

.. image:: https://ci.appveyor.com/api/projects/status/github/ESSS/serialchemy?branch=master
    :target: https://ci.appveyor.com/project/ESSS/serialchemy/?branch=master&svg=true

.. image:: https://codecov.io/gh/ESSS/serialchemy/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ESSS/serialchemy

.. image:: https://img.shields.io/readthedocs/pip.svg
    :target: https://serialchemy.readthedocs.io/en/latest/

What is Serialchemy ?
================================================================================

Serializers for SQLAlchemy models.


Contributing
------------

For guidance on setting up a development environment and how to make a
contribution to serialchemy, see the `contributing guidelines`_.

.. _contributing guidelines: https://github.com/ESSS/serialchemy/blob/master/CONTRIBUTING.rst


Release
-------
A reminder for the maintainers on how to make a new release.

Note that the VERSION should folow the semantic versioning as X.Y.Z
Ex.: v1.0.5

1. Create a ``release-VERSION`` branch from ``upstream/master``.
2. Update ``CHANGELOG.rst``.
3. Push a branch with the changes.
4. Once all builds pass, push a ``VERSION`` tag to ``upstream``.
5. Merge the PR.
