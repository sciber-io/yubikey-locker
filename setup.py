from setuptools import find_packages, setup

setup(
    name="sciber_yklocker",
    python_requires=">=3.11",
    packages=find_packages(
        where="src", include=["sciber_yklocker", "sciber_yklocker.*"]
    ),
    package_dir={"": "src"},
    versions="0.0.1",
)
