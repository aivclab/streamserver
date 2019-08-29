def python_version_check():
    import sys

    assert sys.version_info.major == 3 and sys.version_info.minor >= 6, (
        f"This project is utilises language features only present Python 3.6 and greater. "
        f"You are running {sys.version_info}."
    )


python_version_check()
import pathlib
import re

from setuptools import setup

with open(
    pathlib.Path(__file__).parent / "streamserver" / "__init__.py", "r"
) as project_init_file:
    content = project_init_file.read()
    # get version string from module
    version = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", content, re.M).group(1)
    project_name = re.search(
        r"PROJECT_NAME = ['\"]([^'\"]*)['\"]", content, re.M
    ).group(1)


setup(
    name=project_name,
    version=version,
    description="Server to stream multi-part images over HTTP",
    author="Soeren Rasmussen",
    packages=["streamserver"],
    install_requires=["numpy", "imageio"],
    package_data={"": ["viewer_mini.html"]},
    include_package_data=True,
)
