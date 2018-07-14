from setuptools import setup
from rarbgapi.__version__ import __version__


setup(
    name="RarbgAPI",
    version=__version__,
    author="verybada",
    author_email="verybada.lin@gmail.com",
    description=("A simple interface of RARBG.to"),
    license="BSD",
    keywords=['rarbg', 'rarbg-torrentapi', 'api', 'python'],
    packages=['rarbgapi'],
    install_requires=[
        'requests'
    ],
    extras_require={
        'travis': ['pep8', 'pylint']
    },
    url='https://github.com/verybada/rarbgapi/',
    entry_points={
        'console_scripts': ['rarbgapi=rarbgapi.__main__:main']
    }
)
