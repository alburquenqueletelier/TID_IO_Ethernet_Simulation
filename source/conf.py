import os
import sys

sys.path.insert(0, os.path.abspath('..'))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'TID Gamma CF001'
copyright = '2025, Cristian Fuentes, Bryan Alburquenque'
author = 'Cristian Fuentes, Bryan Alburquenque'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

autosummary_generate = True

autodoc_mock_imports = [
    "scapy",
    "tkinter",
    "psutil",
]

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary'
]

templates_path = ['_templates']
exclude_patterns = [
    '**/.git',
    '.github',
    '**/.venv',
    '**/__pycache__',
    'CLAUDE.md',
    '.claude',
    '**.env',
    '.gitignore',
    'private',
    'db.json',
    'docs',
    'poc',
    'pytest.ini',
    'README.md',
    './test_app.py',
    '**/tests'
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
