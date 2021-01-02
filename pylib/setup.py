from setuptools import setup

megalinter_install_requires = [
    "gitpython",
    "jsonschema",
    "multiprocessing_logging",
    "pygithub",
    "pytablewriter",
    "pytest-cov",
    "pytest-timeout",
    "pyyaml",
    "requests==2.24.0",
    "terminaltables",
    "webpreview",
    "yq",
    "mkdocs-material",
    "mdx_truly_sane_lists",
    "beautifulsoup4",
    "giturlparse",
]

setup(
    name="megalinter-pylib",
    version="0.1",
    description="Mega-Linter PyLib",
    url="http://github.com/nvuillam/mega-linter",
    author="Nicolas Vuillamy",
    author_email="nicolas.vuillamy@gmail.com",
    license="MIT",
    install_requires=megalinter_install_requires,
    zip_safe=False,
)
