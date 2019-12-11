import setuptools
from distutils.core import setup
from pathlib import Path

with (Path(__file__).parent / "readme.md").open("r") as f:
    long_description = f.read()

setup(
    name="localite",
    version="0.3.0",
    description="Stream from and control TMS using Localite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Robert Guggenberger",
    author_email="robert.guggenberger@uni-tuebingen.de",
    url="https://github.com/pyreiz/ctrl-localite",
    download_url="https://github.com/pyreiz/ctrl-localite",
    license="MIT",
    packages=["localite", "localite.flow"],
    entry_points={
        "console_scripts": [
            "localite-flow=localite.cli:flow",
            "localite-mock=localite.mock:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries",
    ],
)
