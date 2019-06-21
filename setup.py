from distutils.core import setup


setup(
    name='ctrl-localite',
    version='0.0.1',
    description='Control Magventure with LocaliteJSON',
    long_description='Toolbox to control a Magventure TMS with localites JSON-TCP-IP Interface',
    author='Robert Guggenberger',
    author_email='robert.guggenberger@uni-tuebingen.de',
    url='https://github.com/pyreiz/ctrl-localite',
    download_url='https://github.com/pyreiz/ctrl-localite',
    license='MIT',
    packages=['localite'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces',
        'Topic :: Scientific/Engineering :: Medical Science Apps.',
        'Topic :: Software Development :: Libraries',
        ]
)
