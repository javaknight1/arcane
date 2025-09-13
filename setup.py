#!/usr/bin/env python3
"""Setup configuration for roadmap-notion package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="roadmap-notion",
    version="0.1.0",
    author="Rob Avery",
    author_email="your.email@example.com",
    description="Parse CSV roadmaps and import them into Notion as a project management system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/javaknight1/notion-roadmap",
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
            "roadmap-parse=roadmap_notion.parser:main",
            "roadmap-import=roadmap_notion.importer:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/javaknight1/notion-roadmap/issues",
        "Source": "https://github.com/javaknight1/notion-roadmap",
    },
)