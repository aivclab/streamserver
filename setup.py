def python_version_check(major=3, minor=6):
    import sys

    assert sys.version_info.major == major and sys.version_info.minor >= minor, (
        f"This project is utilises language features only present Python {major}.{minor} and greater. "
        f"You are running {sys.version_info}."
    )


python_version_check()
import pathlib
import re

from setuptools import find_packages, setup

with open(
    pathlib.Path(__file__).parent / "streamserver" / "__init__.py", "r"
) as project_init_file:
    str_reg_exp = "['\"]([^'\"]*)['\"]"
    content = project_init_file.read()  # get strings from module
    version = re.search(rf"__version__ = {str_reg_exp}", content, re.M).group(1)
    project_name = re.search(rf"__project__ = {str_reg_exp}", content, re.M).group(1)
    author = re.search(rf"__author__ = {str_reg_exp}", content, re.M).group(1)
__author__ = author


def get_requirements():
    requirements_out = []
    with open("requirements.txt") as f:
        requirements = f.readlines()

        for requirement in requirements:
            requirements_out.append(requirement.strip())

    return requirements_out


def get_entry_points():
    return {
        "console_scripts": [
            "ss-cv2 = streamserver.entry_points.ss_cv2:main",
            "ss-imageio = streamserver.entry_points.ss_imageio:main",
        ]
    }


def get_readme():
    with open("README.md") as f:
        return f.read()


def get_keyword():
    with open("KEYWORDS.md") as f:
        return f.read()


def get_license():
    return "Apache License, Version 2.0"


def get_extras():
    these_extras = {
        # 'ExtraName':['package-name; platform_system == "System(Linux,Windows)"'
    }

    path: pathlib.Path = pathlib.Path(__file__).parent

    for file in path.iterdir():
        if file.name.startswith("requirements_"):

            requirements_group = []
            with open(str(file.absolute())) as f:
                requirements = f.readlines()

                for requirement in requirements:
                    requirements_group.append(requirement.strip())

            group_name_ = "_".join(file.name.strip(".txt").split("_")[1:])

            these_extras[group_name_] = requirements_group

    all_dependencies = []

    for group_name in these_extras:
        all_dependencies += these_extras[group_name]
    these_extras["all"] = all_dependencies

    return these_extras


setup(
    name=project_name,
    version=version,
    description="Server to stream multi-part images over HTTP",
    author=author,
    package_data={"": ["viewer_mini.html"]},
    include_package_data=True,
    python_requires=">=3.6",
    packages=find_packages(),
    install_requires=get_requirements(),
    entry_points=get_entry_points(),
    license=get_license(),
    extras_require=get_extras(),
    long_description_content_type="text/markdown",
    long_description=get_readme(),
    url="",
    download_url="",
)
