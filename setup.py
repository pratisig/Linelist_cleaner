from setuptools import setup, find_packages

setup(
    name="linelist-cleaner",
    version="1.0.0",
    author="Youssoupha MBODJI",
    author_email="pratisig.consulting@gmail.com",
    description="Application de nettoyage épidémiologique et de géocodage spatial en cascade (P-Codes OCHA COD-AB)",
    packages=find_packages(),
    include_package_data=True,
)
