from setuptools import find_packages, setup
import os

setup(
    name="pacs2go",
    packages=find_packages(),
    version=os.getenv('PACS2GO_VERSION'),
    description="exchange medical data with xnat",
    author="Tamara Krafft",
    license="-",
)
