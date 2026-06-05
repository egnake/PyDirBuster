from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pydirbuster",
    version="5.0.0",
    author="Hamza Atmacaa & Egnake",
    description="Advanced Asynchronous Directory Brute-Forcer with WAF Evasion",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/egnake/PyDirBuster",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "pydirbuster": ["wordlists/*.txt"],
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "pydirbuster=pydirbuster.main:main",
        ],
    },
)
