'''
ivideon-demo-task
-----------------

Реализация тестового задания для компании Ivideon.

'''
from setuptools import find_packages, setup

install_requires = [
    'click==6.6',
    'tornado==4.3'
]


setup(
    name='ivideon-demo-task',
    version='0.1.0',

    description='Реализация тестового задания для компании Ivideon',
    long_description=__doc__,

    url='https://github.com/droppoint/ivideon-demo-task',

    author='Alexei Partilov',
    author_email='partilov@gmail.com',

    entry_points={
        'console_scripts': [
            'idt = ivideon_demo_task.cli:main',
        ]
    },

    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Environment :: Console',
        'Private :: Do Not Upload'
    ],

    keywords='Ivideon',
    packages=find_packages(exclude=('tests', 'tests.*')),

    install_requires=install_requires
)
