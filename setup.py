from setuptools import setup, find_packages

setup(
    name="arcapi",
    version="0.1.1",
    author="FID-Judaica, Goethe Universitätsbibliothek",
    license="MLP 2.0/EUPL 1.1",
    author_email="a.christianson@ub.uni-frankfurt.de",
    description="web API for Revrit project",
    #long_description=open("README.rst").read(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pica_parse @ git+https://github.com/FID-Judaica/pica_parse.py.git",
        "arc @ git+https://github.com/FID-Judaica/goethe-university-library-arc.git",
        "compose-struct @ git+https://github.com/ninjaaron/compose-struct.git",
        # "cython==0.29.36",
        # "HspellPy",
    ],
)
