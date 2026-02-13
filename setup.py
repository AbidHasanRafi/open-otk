from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="open-otk",
    version="1.0.1",
    author="Md. Abid Hasan Rafi",
    author_email="ahr16.abidhasanrafi@gmail.com",
    description="Open Ollama Toolkit - Professional Python library for building AI applications with Ollama",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aiextension/open-otk",
    packages=find_packages(),
    py_modules=['otk'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
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
        "ollama>=0.1.0",
    ],
    extras_require={
        "scraper": [
            "requests>=2.31.0",
            "beautifulsoup4>=4.12.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "otk=otk:main",
        ],
    },
)
