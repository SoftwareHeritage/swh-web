#!/usr/bin/env python3

import os
from setuptools import setup, find_packages


def parse_requirements(name=None):
    if name:
        reqf = 'requirements-%s.txt' % name
    else:
        reqf = 'requirements.txt'

    requirements = []
    if not os.path.exists(reqf):
        return requirements

    with open(reqf) as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)
    return requirements


setup(
    name='swh.web',
    description='Software Heritage Web UI',
    author='Software Heritage developers',
    author_email='swh-devel@inria.fr',
    url='https://forge.softwareheritage.org/diffusion/DWUI/',
    packages=find_packages(),
    scripts=[],
    install_requires=parse_requirements() + parse_requirements('swh'),
    setup_requires=['vcversioner'],
    extras_require={'testing': parse_requirements('test')},
    vcversioner={},
    include_package_data=True,
)
