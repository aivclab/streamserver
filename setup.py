from setuptools import setup, find_packages


def get_requirements():
    requirements_out = []
    with open('requirements.txt') as f:
        requirements = f.readlines()

        for requirement in requirements:
            requirements_out.append(requirement.strip())

    return requirements_out


def get_entry_points():
    return {
        'console_scripts': [
            'ss-run = streamserver:run_streamserver',
            'ss-cv2 = streamserver.samples.ss_cv2:main',
            'ss-imageio = streamserver.samples.ss_imageio:main'
        ]
    }


def get_readme():
    with open('README.md') as f:
        return f.read()


def get_keyword():
    with open('KEYWORDS.md') as f:
        return f.read()


def get_license():
    return 'Apache License, Version 2.0'


def get_classifiers():
    return [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
        # 'Topic :: Scientific/Engineering :: Artificial Intelligence'
        # 'Topic :: Software Development :: Bug Tracking',
    ]


setup(name='streamserver',
      version='0.4.0',
      description='Server to stream multi-part images over HTTP',
      author='Soeren Rasmussen',
      package_data={'': ['viewer_mini.html']},
      include_package_data=True,
      python_requires='>=3',
      packages=find_packages(),
      install_requires=get_requirements(),
      entry_points=get_entry_points(),
      license=get_license(),
      classifiers=get_classifiers(),
      long_description_content_type='text/markdown',
      long_description=get_readme(),
      url='',
      download_url=''
      )
