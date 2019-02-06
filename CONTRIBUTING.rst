.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.


Get Started!
------------

Ready to contribute? Here's how to set up `serialchemy` for local development.

#. Fork the `serialchemy` repo on GitHub.
#. Clone your fork locally::

    $ git clone git@github.com:your_github_username_here/serialchemy.git

#. Create a virtual environment and activate it::

    $ python -m virtualenv .env

    $ .env\Scripts\activate  # For Windows
    $ source .env/bin/activate  # For Linux

#. Install the development dependencies for setting up your fork for local development::

    $ cd serialchemy/
    $ pip install -e .[testing,docs]

   .. note::

       If you use ``conda``, you can install ``virtualenv`` in the root environment::

           $ conda install -n root virtualenv

       Don't worry as this is safe to do.

#. Install pre-commit::

    $ pre-commit install

#. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

#. When you're done making changes, run the tests::

    $ pytest

#. If you want to check the modification made on the documentation, you can generate the docs locally::

    $ tox -e docs

   The documentation files will be generated in ``docs/_build``.

#. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

#. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated.
