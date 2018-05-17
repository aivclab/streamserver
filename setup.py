from setuptools import setup

setup(name='streamserver',
      version='0.2.1',
      description='Server to stream multi-part JPEG over HTTP',
      author='Soeren Rasmussen',
      packages=['streamserver'],
      install_requires=['numpy','imageio']
)
