def python_version_check():
    import sys

    assert sys.version_info.major == 3 and sys.version_info.minor >= 6, (
        f"This project is utilises language features only present Python 3.6 and greater. "
        f"You are running {sys.version_info}."
    )


python_version_check()
import pathlib
import re

from setuptools import find_packages, setup

with open(
    pathlib.Path(__file__).parent / "streamserver" / "__init__.py", "r"
) as project_init_file:
    content = project_init_file.read()
    # get version string from module
    version = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", content, re.M).group(1)
    project_name = re.search(
        r"PROJECT_NAME = ['\"]([^'\"]*)['\"]", content, re.M
    ).group(1)


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


def get_classifiers():
    return [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Natural Language :: English",
    ]


setup(
    name=project_name,
    version=version,
    description="Server to stream multi-part images over HTTP",
    author="Soeren Rasmussen",
    package_data={"": ["viewer_mini.html"]},
    include_package_data=True,
    python_requires=">=3",
    packages=find_packages(),
    install_requires=get_requirements(),
    entry_points=get_entry_points(),
    license=get_license(),
    classifiers=get_classifiers(),
    long_description_content_type="text/markdown",
    long_description=get_readme(),
    url="",
    download_url="",
)
