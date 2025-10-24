"""Package setup configuration."""

from setuptools import setup, find_packages

setup(
    name="unity_build_log",
    version="0.1.0",
    packages=find_packages(include=['config', 'config.*', 'src', 'src.*']),
    install_requires=[
        "watchdog>=2.1.0",
    ],
    python_requires=">=3.8",
)