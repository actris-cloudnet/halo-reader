import numpy
from Cython.Build import cythonize
from setuptools import Extension, setup

if __name__ == "__main__":
    extensions = [
        Extension(
            name="haloreader.data_reader",
            sources=["src/haloreader/data_reader/data_reader.pyx"],
        ),
    ]
    setup(
        ext_modules=cythonize(
            extensions,
            language_level="3",
            annotate=True,
        ),
        include_dirs=[numpy.get_include()],
        zip_safe=False,
    )
