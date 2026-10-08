from setuptools import setup, find_packages

setup(
    name="sentinel-governance-sdk",
    version="2.0.0",
    description="Python Client SDK for Sentinel Legacy Enterprise AI Agent Governance Control Plane",
    author="Sentinel Legacy Team",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.27.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires=">=3.10",
)
