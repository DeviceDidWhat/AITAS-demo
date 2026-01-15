"""Setup script for AITAS"""
from setuptools import setup, find_packages

setup(
    name="aitas",
    version="0.1.0",
    description="AI Terminal Assistant System - Natural language CLI",
    author="Your Name",
    python_requires=">=3.8",
    packages=find_packages(),
    install_requires=[
        "transformers>=4.36.2",
        "torch>=2.1.2",
        "sentencepiece>=0.1.99",
        "protobuf>=4.25.1",
        "rich>=13.7.0",
        "prompt-toolkit>=3.0.43",
        "pyyaml>=6.0.1",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.3",
        "jsonschema>=4.20.0",
    ],
    entry_points={
        "console_scripts": [
            "aitas=main:main",
        ],
    },
)