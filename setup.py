from setuptools import setup


setup(
    name="RarbgAPI",
    version="0.1",
    author="Lin Chi Lung",
    author_email="verybada.lin@gmail.com",
    description=("A simple interface of RARBG.to"),
    license="BSD",
    keywords="rarbg api",
    packages=['rarbgapi'],
    install_requires=[
        'requests'
    ],
    extras_require={
        'travis': ['pep8', 'pylint']
    }
)
