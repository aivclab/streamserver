from setuptools import setup

setup(name='streamserver',
      version='0.3.0',
      description='Server to stream multi-part images over HTTP',
      author='Soeren Rasmussen',
      packages=['streamserver'],
      install_requires=['numpy','imageio'],
      package_data={'': ['viewer_mini.html']},
      include_package_data=True
)
