"""
setup.py - Package configuration for Review Clustering System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="review-clustering",
    version="1.0.0",
    author="Your Name/Organization",
    author_email="your.email@example.com",
    description="Production-grade Python application for clustering and analyzing customer reviews",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/review-clustering",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/review-clustering/issues",
        "Documentation": "https://github.com/yourusername/review-clustering/tree/main/docs",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Flask",
        "Intended Audience :: Developers",
        "Intended Audience :: Business and Finance",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "flake8>=6.0",
            "mypy>=1.0",
        ],
        "prod": [
            "gunicorn>=21.0",
            "psycopg2-binary>=2.9",
        ],
    },
    entry_points={
        "console_scripts": [
            "review-clustering=review_clustering.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
