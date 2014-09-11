from setuptools import setup, find_packages
import os

version = '0.9.0'

setup(
    name='proso-apps',
    version=version,
    description='General library for applications in PROSO projects',
    author='Jan Papousek',
    author_email='jan.papousek@gmail.com',
    namespace_packages = ['proso', 'proso.django'],
    packages=['proso_models', 'proso_questions', 'proso_common', 'proso_ab', 'proso', 'proso.django', 'proso.models'],
    install_requires=[
        'Django>=1.6',
        'django-debug-toolbar>=1.1',
        'django-ipware>=0.0.8',
        'django-lazysignup>=0.12.2',
        'Markdown>=2.4.1',
        'PIL>=1.1.7',
        'South>=0.8'
    ],
    license='Gnu GPL v3',
)
