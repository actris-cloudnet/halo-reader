import numpy
from Cython.Build import cythonize
from setuptools import Extension, setup

if __name__ == "__main__":
    extensions = [
        Extension(
            name="halo_reader.data_reader",
            sources=["src/halo_reader/data_reader/data_reader.pyx"],
        ),
        Extension(
            name="halo_reader.background_reader",
            sources=[
                "src/halo_reader/background_reader/background_reader.pyx"
            ],
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
