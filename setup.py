from setuptools import find_packages
from setuptools import setup

with open("README.rst", encoding="UTF-8") as readme_file:
    readme = readme_file.read()

with open("CHANGELOG.rst", encoding="UTF-8") as changelog_file:
    history = changelog_file.read()

requirements = ["sqlalchemy>=1.4,<2.0"]
extras_require = {
    "docs": ["sphinx >= 1.4", "sphinx_rtd_theme", "sphinx-autodoc-typehints", "typing_extensions"],
    "testing": [
        "codecov",
        "mypy",
        "pytest",
        "pytest-cov",
        "pytest-regressions",
        "pytest-freezegun",
        "pre-commit",
        "setuptools",
        "sqlalchemy_utils",
        "tox",
    ],
}

setup(
    author="ESSS",
    author_email="foss@esss.co",
    use_scm_version={"git_describe_command": "git describe --dirty --tags --long --match v*"},
    setup_requires=["setuptools_scm"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    description="Serializers for SQLAlchemy models.",
    extras_require=extras_require,
    install_requires=requirements,
    license="MIT",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    python_requires=">=3.8",
    keywords="serialchemy",
    license_files=('LICENSE',),
    name="serialchemy",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    url="https://github.com/ESSS/serialchemy",
    zip_safe=False,
)
