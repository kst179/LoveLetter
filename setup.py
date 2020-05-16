from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="loveletter",
      version="0.0.3",
      author="Konstantin Kozlovtsev",
      packages=find_packages(),
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/kst179/LoveLetter",
      classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
      ],
      entry_points={
          'console_scripts': [
                'loveletter = loveletter.bot:main'
          ],
      }
      )
