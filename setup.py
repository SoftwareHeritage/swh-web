#!/usr/bin/env python3

from setuptools import setup


def parse_requirements():
    requirements = []
    with open('requirements.txt') as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            requirements.append(line)

    return requirements


setup(
    name='swh.web.ui',
    description='Software Heritage Web UI',
    author='Software Heritage developers',
    author_email='swh-devel@inria.fr',
    url='https://forge.softwareheritage.org/diffusion/DWUI/',
    packages=['swh.web.ui', 'swh.web.ui.views', 'swh.web.ui.tests'],
    scripts=[],
    install_requires=parse_requirements(),
    setup_requires=['vcversioner'],
    vcversioner={},
    include_package_data=True,
)
