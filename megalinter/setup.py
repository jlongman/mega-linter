from setuptools import setup
from pylib.requires import megalinter_install_requires
setup(
    name="megalinter",
    version="0.1",
    description="Mega-Linter",
    url="http://github.com/nvuillam/mega-linter",
    author="Nicolas Vuillamy",
    author_email="nicolas.vuillamy@gmail.com",
    license="MIT",
    packages=[
        "megalinter",
        "megalinter.linters",
        "megalinter.reporters",
        "megalinter.reporters.bb",
        "megalinter.reporters.bb.line_parser",
    ],
    install_requires=megalinter_install_requires,

    zip_safe=False,
)
