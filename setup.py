from setuptools import find_packages, setup

setup(
    name="sciber_yklocker",
    python_requires=">=3.13",
    install_requires=["pywin32==311; sys_platform == 'win32'"],
    packages=find_packages(
        where="src", include=["sciber_yklocker", "sciber_yklocker.*"]
    ),
    package_dir={"": "src"},
    version="0.0.1",
)
