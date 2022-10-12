from setuptools import setup, find_packages

setup(
    name='OuchServer',
    version='0.0.1',
    install_requires=[
        'ConfigArgParse==0.13.0',
        'pytz==2017.3',
    ],
    packages=find_packages(
        include=['OuchServer']
    ),

)
