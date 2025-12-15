# Project information

project = 'kuristo'
copyright = '2025, David Andrs'
author = 'David Andrs'
release = '0.8.0'

# General configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_design',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# HTML output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

todo_include_todos = True
