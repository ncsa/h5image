from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'description.rst').read_text(encoding='utf-8')

setup(
    name='h5image',
    version='0.2.0',
    description='Load and save images to HDF5 files',
    long_description=long_description,

    author='Rob Kooper',
    author_email='kooper@illinois.edu',

    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate you support Python 3. These classifiers are *not*
        # checked by 'pip install'. See instead 'python_requires' below.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        "Programming Language :: Python :: 3.10",
    ],
    keywords=['hdf5', 'image', 'map'],

    packages=find_packages(),

    python_requires='>=3.6, <4',

    install_requires=[
        'affine',
        'h5py',
        'numpy',
        'rasterio',
    ],

    extras_require={  # Optional
        'dev': ['matplotlib'],
        'test': ['coverage'],
    },

    entry_points={  # Optional
        'console_scripts': [
            'h5create=h5image:h5create',
        ],
    },
)
