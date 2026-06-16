from setuptools import setup, find_packages

setup(
    name="stackbridge-platform",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "boto3",
        "rich",
        "PyYAML"
    ],
    entry_points={
        "console_scripts": [
            "stackbridge=stackbridge.cli:cli"
        ]
    }
)
