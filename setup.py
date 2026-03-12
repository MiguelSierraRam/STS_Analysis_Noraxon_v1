#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup configuration for STS Analysis Tool.
"""

from setuptools import setup, find_packages

with open("docs/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sts-analysis-tool",
    version="2.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Professional STS (Sit-to-Stand) analysis with advanced metrics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MiguelSierraRam/STS_Analysis_Noraxon_v1",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=2.0.0",
        "pandas>=2.0.0",
        "matplotlib>=3.8.0",
        "openpyxl>=3.1.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sts-analysis=sts_analysis_tool_enhanced_v2:main",
        ],
    },
)
