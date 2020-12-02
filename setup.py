
from setuptools import setup

setup(name='renode_colab_tools',
      version='0.1',
      description='Python helper lib for Renode in Colab',
      author='Antmicro',
      author_email='dwojciechowski@antmicro.com',
      install_requires=[
          'ffmpeg-python', 'pyaudioconvert', 
      ],
      license='MIT',
      packages=['renode_colab_tools'])