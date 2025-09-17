#!/usr/bin/env python3
"""Setup configuration for Arcane CLI."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="arcane-cli",
    version="2.0.0",
    author="Rob Avery",
    author_email="your.email@example.com",
    description="AI-powered roadmap generation CLI with project management integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/javaknight1/arcane",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Scheduling",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "arcane=arcane.__main__:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/javaknight1/arcane/issues",
        "Source": "https://github.com/javaknight1/arcane",
    },
)