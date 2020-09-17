from setuptools import find_packages, setup

setup(
    name="StreamServer",
    version="0.5.0",
    description="Server to stream multi-part images over HTTP",
    author='Soeren Rasmussen',
    package_data={"": ["viewer_mini.html"]},
    include_package_data=True,
    python_requires=">=3",
    packages=find_packages(),
    install_requires=['numpy','imageio']
)
