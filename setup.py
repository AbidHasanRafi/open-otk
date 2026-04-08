from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="open-otk",
    version="2.0.0",
    author="Md. Abid Hasan Rafi",
    author_email="ahr16.abidhasanrafi@gmail.com",
    description=(
        "Open Ollama Toolkit - Intelligent framework for local LLM orchestration, "
        "hybrid RAG, automated evaluation, and pipeline composition"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aiextension/open-otk",
    packages=find_packages(),
    py_modules=["otk"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
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
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "numpy>=1.24.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "rag": ["hnswlib>=0.7.0"],
        "server": [
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "websockets>=11.0",
        ],
        "eval": ["scipy>=1.10.0"],
        "structured": ["pydantic>=2.0.0"],
        "tokenizer": ["tiktoken>=0.5.0"],
        "all": [
            "hnswlib>=0.7.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.20.0",
            "websockets>=11.0",
            "scipy>=1.10.0",
            "pydantic>=2.0.0",
            "tiktoken>=0.5.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "otk=otk:main",
            "otk-server=otk.server:main",
        ],
    },
)
