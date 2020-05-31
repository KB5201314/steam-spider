from Cython.Build import cythonize
from distutils.core import setup, Extension

setup(
    name='item_based_cf',
    ext_modules = cythonize("item_based_cf.py")
)