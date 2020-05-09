#!/usr/bin/python3
import re

import setuptools


def extract_version(filename):
    with open(filename, 'r') as fh:
        for line in fh:
            match = re.match('''VERSION\s*=\s*["']([-_.0-9a-z]+)(\+?)["']''', line)
            if match:
                if match[2] == '':
                    return match[1]
                else:
                    return match[1] + '.post'
    exit("Cannot extract version number from %s" % filename)


with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name="zeitgitterd",
    version=extract_version('zeitgitter/version.py'),
    author="Marcel Waldvogel",
    author_email="marcel.waldvogel@trifence.ch",
    description="Zeitgitter timestamping server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/zeitgitter/zeitgitterd",
    license='AGPLv3',
    packages=setuptools.find_packages(),
    install_requires=['pygit2', 'python-gnupg', 'configargparse', 'requests',
        'setuptools', 'git-timestamp'],
#    package_data={'zeitgitter': ['sample.conf', '*.{html,css,svg}']},
    data_files=[('zeitgitter', ['zeitgitter/sample.conf', 'zeitgitter/web/contact.html', 'zeitgitter/web/index.html', 'zeitgitter/web/privacy.html', 'zeitgitter/web/tos.html', 'zeitgitter/web/zeitgitter.css', 'zeitgitter/web/zeitgitter.svg'])],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'zeitgitterd=zeitgitter.server:run',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Information Technology",
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Security",
    ],
)
