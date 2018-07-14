import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
about = dict()
with open(os.path.join(here, 'rarbgapi', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(
    name='RarbgAPI',
    version=about['__version__'],
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
