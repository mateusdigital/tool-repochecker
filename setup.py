## -----------------------------------------------------------------------------
from setuptools import setup, find_packages
import json

with open("package.json", encoding="utf-8") as package_file:
    package_metadata = json.load(package_file)

## -----------------------------------------------------------------------------
setup(
    name="repochecker",
    version=package_metadata["version"],
    author="Saturno Software",
    author_email="hello@saturno.software",
    description=package_metadata["description"],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SaturnoSoftware/repochecker",
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
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
