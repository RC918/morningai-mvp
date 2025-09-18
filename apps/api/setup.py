from setuptools import setup, find_packages

setup(
    name='morningai_api',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'Flask',
        'Flask-Cors',
        'PyJWT',
        'SQLAlchemy',
        'Flask-SQLAlchemy'
    ],
    python_requires='>=3.8',
)


