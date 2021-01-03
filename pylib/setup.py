import requires
from setuptools import setup

setup(
    name="megalinter-pylib",
    version="0.1",
    description="Mega-Linter PyLib",
    url="http://github.com/nvuillam/mega-linter",
    author="Nicolas Vuillamy",
    author_email="nicolas.vuillamy@gmail.com",
    license="MIT",
    install_requires=requires.megalinter_install_requires,
    zip_safe=False,
)
