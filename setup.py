"""PEPPER - Project Execution and Planning Platform for Enhanced Resource Management."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Pepper",
    version="0.1.0",
    author="Mmaddhatter13",
    author_email="info@scalingsuccess.io",
    description="Project Execution and Planning Platform for Enhanced Resource Management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/FairGigAI/pepper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=10.0.0",
        "loguru>=0.7.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0.0",
        "jinja2>=3.0.0",
        "markdown>=3.4.0",
        "aiohttp>=3.8.0",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.5.0",
        "pytz>=2023.3",
        "gitpython>=3.1.0",
        "slack-sdk>=3.19.0",
        "openai>=1.0.0",
        "tenacity>=8.2.0",
        "watchdog>=3.0.0",
        "pygithub>=2.1.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=2.17.0",
            "flake8>=6.0.0",
            "pre-commit>=3.3.0",
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.10.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
            "myst-parser>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pepper=main:main",
        ],
    },
    package_data={
        "pepper": [
            "templates/*.md",
            "templates/*.yaml",
            "config/*.yaml",
            "config/agents/*.yaml",
            "config/environments/*.yaml",
        ],
    },
) 