# $Id$
from setuptools import setup, find_packages
setup(
    name = "pysftp",
    version = "0.2.0",
    #packages = find_packages(),
    py_modules = ['pysftp'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires = ['paramiko>=1.7.4'],

    package_data = {
        # If any package contains *.txt or *.rst files, include them:
        '': ['README','*.txt', '*.rst'],
    },

    # metadata for upload to PyPI
    author = "Jeff hinrichs",
    author_email = "jeffh@dundeemt.com",
    description = "A friendly face on SFTP",
    license = "BSD - http://code.google.com/p/pysftp/source/browse/trunk/LICENSE.txt",
    keywords = "sftp ssh ftp internet",
    url = "http://code.google.com/p/pysftp/",   # project home page, if any
    long_description = """a simple interface to sftp.  based on zeth's ssh.py""",
    platforms=['any'],
    download_url='http://code.google.com/p/pysftp/',

    # could also include long_description, download_url, classifiers, etc.
)
