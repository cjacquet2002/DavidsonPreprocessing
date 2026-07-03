from setuptools import setup, find_packages

setup(
    name="davidson-preprocessing",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "nibabel",
        "pydicom",
    ],
    entry_points={
        "console_scripts": [
            "extract-dicoms=davidson_preprocessing.extract_dicoms:main",
            "davidson-convert=davidson_preprocessing.convert2bids:main",
        ],
    },
)