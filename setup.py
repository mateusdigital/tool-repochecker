## -----------------------------------------------------------------------------
from setuptools import setup, find_packages

## -----------------------------------------------------------------------------
setup(
    name="repochecker",
    version="3.1.0",
    author="mateus.digital",
    author_email="hello@mateus.digital",
    description="A tool to check the status of git repositories and submodules.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mateusdigital/repochecker",  
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    entry_points={
        "console_scripts": [
            "repochecker=repochecker.main:run",  
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
