from setuptools import find_packages, setup

setup(
    name="animation-converter",
    version="0.1",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    data_files=[("bins", ["bins/linux/64tass", "bins/macos/64tass"])],
)
