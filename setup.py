from setuptools import find_packages, setup

with open("requirements.txt") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="animation-converter",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=requirements,
    data_files=[
        ("bins", ["bins/linux/64tass", "bins/macos/64tass", "bins/windows/64tass.exe"])
    ],
)
