import os
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
about = dict()
with open(os.path.join(here, 'rarbgapi', '__version__.py'), 'r') as f:
    exec(f.read(), about)

long_description = None
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='RarbgAPI',
    version=about['__version__'],
    author="verybada",
    author_email="verybada.lin@gmail.com",
    description=("A python3 wrapper for RARBG.to"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="BSD",
    keywords=['rarbg', 'rarbg-torrentapi', 'api', 'python'],
    packages=['rarbgapi'],
    install_requires=[
        'requests'
    ],
    extras_require={
        'travis': ['pycodestyle', 'pylint']
    },
    url='https://github.com/verybada/rarbgapi/',
    entry_points={
        'console_scripts': ['rarbgapi=rarbgapi.__main__:main']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
