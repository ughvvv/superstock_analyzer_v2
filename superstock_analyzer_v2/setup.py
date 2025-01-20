from setuptools import setup, find_packages
import os

# Read README.md safely
try:
    with open('README.md', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A sophisticated stock screening program implementing Jesse Stine's Superstock methodology"

setup(
    name="superstock_analyzer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'yfinance>=0.2.3',
        'pandas>=1.5.0',
        'numpy>=1.21.0',
        'requests>=2.28.0',
        'python-dotenv>=0.19.0',
        'openai>=0.27.0',
        'beautifulsoup4>=4.9.3',
        'matplotlib>=3.5.0',
        'seaborn>=0.11.0',
        'schedule>=1.1.0',
        'scipy>=1.7.0',
        'ta-lib>=0.4.24'
    ],
    author="Blake Cole",
    author_email="blake@example.com",
    description="A sophisticated stock screening program implementing Jesse Stine's Superstock methodology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/blakecole/superstock-analyzer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "Framework :: Jupyter",
    ],
    python_requires='>=3.8',
    keywords='stock analysis, trading, investment, quantitative analysis, technical analysis',
)
