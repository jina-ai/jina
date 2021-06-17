import os
import re
import sys
from os import path

sys.path.insert(0, path.abspath('..'))

project = 'Jina'
slug = re.sub(r'\W+', '-', project.lower())
author = 'Jina AI'
copyright = 'Jina AI Limited. All rights reserved.'
source_suffix = ['.rst', '.md']
master_doc = 'index'
language = 'en'
repo_dir = '../'

try:
    if 'JINA_VERSION' not in os.environ:
        pkg_name = 'jina'
        libinfo_py = path.join(repo_dir, pkg_name, '__init__.py')
        libinfo_content = open(libinfo_py, 'r').readlines()
        version_line = [
            l.strip() for l in libinfo_content if l.startswith('__version__')
        ][0]
        exec(version_line)
    else:
        __version__ = os.environ['JINA_VERSION']
except FileNotFoundError:
    __version__ = '0.0.0'

version = __version__
release = __version__

templates_path = ['template']
exclude_patterns = [
    '_build',
    'Thumbs.db',
    '.DS_Store',
    'tests',
    'page_templates',
    '.github',
]
pygments_style = 'rainbow_dash'
html_theme = 'furo'

base_url = '/'
html_baseurl = 'https://docs.jina.ai'
sitemap_url_scheme = '{link}'
sitemap_locales = [None]
sitemap_filename = "sitemap.xml"

html_theme_options = {
    'light_logo': 'logo-light.svg',
    'dark_logo': 'logo-dark.svg',
    "sidebar_hide_name": True,
}

html_static_path = ['_static']
html_extra_path = ['html_extra']
html_css_files = ['main.css']
htmlhelp_basename = slug
html_show_sourcelink = False

latex_documents = [(master_doc, f'{slug}.tex', project, author, 'manual')]
man_pages = [(master_doc, slug, project, [author], 1)]
texinfo_documents = [
    (master_doc, slug, project, author, slug, project, 'Miscellaneous')
]
epub_title = project
epub_exclude_files = ['search.html']

# -- Extension configuration -------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx_autodoc_typehints',
    'sphinx.ext.viewcode',
    'sphinx.ext.coverage',
    'sphinxcontrib.apidoc',
    'sphinxarg.ext',
    'recommonmark',
    'sphinx_markdown_tables',
    'sphinx_copybutton',
    'sphinx_sitemap',
    'sphinx.ext.intersphinx',
    'sphinxext.opengraph',
    'notfound.extension',
]

# -- Custom 404 page

# sphinx-notfound-page
# https://github.com/readthedocs/sphinx-notfound-page
notfound_context = {
    'title': 'Page Not Found',
    'body': '''
<h1>Page Not Found</h1>
<p>Oops, we couldn't find that page. </p>
<p>You can try using the search box or check our menu on the left hand side of this page.</p>

<p>If neither of those options work, please create a Github issue ticket <a href="https://github.com/jina-ai/jina/">here</a>, and one of our team will respond.</p>

''',
}
notfound_no_urls_prefix = True

apidoc_module_dir = repo_dir
apidoc_output_dir = 'api'
apidoc_excluded_paths = ['tests', 'legacy', 'hub', 'toy*', 'setup.py']
apidoc_separate_modules = True
apidoc_extra_args = ['-t', 'template/']
autodoc_member_order = 'bysource'
autodoc_mock_imports = ['argparse', 'numpy', 'np', 'tensorflow', 'torch', 'scipy']
autoclass_content = 'both'
set_type_checking_flag = False
html_last_updated_fmt = ''
nitpicky = True
nitpick_ignore = [('py:class', 'type')]
linkcheck_ignore = [
    # Avoid link check on local uri
    'http://0.0.0.0:*',
    'pods/encode.yml',
    'https://github.com/jina-ai/jina/commit/*',
    '.github/*',
    'extra-requirements.txt',
    'fastentrypoints.py' '../../101',
    '../../102',
    'http://www.twinsun.com/tz/tz-link.htm',  # Broken link from pytz library
    'https://urllib3.readthedocs.io/en/latest/contrib.html#google-app-engine',  # Broken link from urllib3 library
    'https://linuxize.com/post/how-to-add-swap-space-on-ubuntu-20-04/',
    # This link works but gets 403 error on linkcheck
]
linkcheck_timeout = 20
linkcheck_retries = 2
linkcheck_anchors = False

ogp_site_url = 'https://docs.jina.ai/'
ogp_image = 'https://docs.jina.ai/_static/banner.png'
ogp_use_first_image = True
ogp_description_length = 300
ogp_type = 'website'
ogp_site_name = 'Jina Documentation'

ogp_custom_meta_tags = [
    '<meta name="twitter:card" content="summary_large_image">',
    '<meta name="twitter:site" content="@JinaAI_">',
    '<meta name="twitter:creator" content="@JinaAI_">',
    '<meta name="description" content="Jina is the cloud-native neural search solution powered by the state-of-the-art AI and deep learning">',
    '<meta property="og:description" content="Jina is the cloud-native neural search solution powered by the state-of-the-art AI and deep learning">',
    '''
    <!-- Global site tag (gtag.js) - Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-48ZDWC8GT6"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());

  gtag('config', 'G-48ZDWC8GT6');
</script>
    '''
]

def setup(app):
    from sphinx.domains.python import PyField
    from sphinx.util.docfields import Field
    from sphinx.locale import _

    app.add_object_type(
        'confval',
        'confval',
        objname='configuration value',
        indextemplate='pair: %s; configuration value',
        doc_field_types=[
            PyField(
                'type',
                label=_('Type'),
                has_arg=False,
                names=('type',),
                bodyrolename='class',
            ),
            Field(
                'default',
                label=_('Default'),
                has_arg=False,
                names=('default',),
            ),
        ],
    )
