#!/usr/bin/env python3
import setuptools

setuptools.setup(
    name="repochecker",
    version="0.0.1",
    description="Git repository checkekr",
    keywords="git",
    author="stdmatt",
    author_email="stdmatt@pixelwizards.io",
    url="http://stdmatt.com",
    license="GPLv3",
    packages=setuptools.find_packages(),
    install_requires=["pathlib"],
    setup_requires=[""],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Development Status :: 3 - Alpha",
        "Natural Language :: English",
    ],
    entry_points={
        "console_scripts": [
            "repochecker = repochecker.repochecker:run"
        ],
    },
)
