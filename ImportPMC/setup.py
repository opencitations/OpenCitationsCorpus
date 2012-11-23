from distutils.core import setup

setup(
    name='pubmed-rdf',
    description='A set of tools to convert NLM XML article data to RDF.',
    author='JISC OpenCitations Project',
    author_email='alexander.dutton@zoo.ox.ac.uk',
    version='0.9',
    packages=['pubmed'],
    scripts=[],
    long_description=open('README.rst').read(),
    classifiers=['Development Status :: 4 - Beta',
                 'License :: OSI Approved :: MIT License',
                 'Intended Audience :: Science/Research',
                 'Programming Language :: Python',
                 'Topic :: Text Processing :: Markup :: XML',
                 'Topic :: Scientific/Engineering :: Bio-Informatics'],
    data_files=['pubmed/data/catalog.xml'],
)
