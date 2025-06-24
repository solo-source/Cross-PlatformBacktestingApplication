from setuptools import setup, find_packages

setup(
    name="backtester_app",
    version="0.1.0",
    author="solo-source",
    author_email="",
    description="A cross-platform Python/Qt trading backtester with live data support",
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "backtrader",
        "yfinance",
        "PySide6",
        "matplotlib",
        "pandas",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "backtester=gui.main_window:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9"
)
