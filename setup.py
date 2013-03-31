from setuptools import setup, find_packages

setup(
    name = 'opencitations',
    version = '0.3',
    packages = find_packages(),
    install_requires = [
        "lxml",
        "pyoai",
        "python-dateutil",
        "requests==1.1.0"
    ],
    url = 'http://opencitations.wordpress.com',
    author = 'Cottage Labs, Heinrich Hartmann, JISC Open Citations project',
    author_email = 'us@cottagelabs.com',
    description = 'toolkit for building and maintaining the Open Citations Corpus',
    license = 'MIT',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
