import io
import yaml
import markdown as markdown_module
import os
import werkzeug
import locale
import itertools
import datetime
from flask import Flask, Markup, render_template, abort, render_template_string, url_for

### initialization ###
app = Flask(__name__)

### configuration ###
app.config['FREEZER_DESTINATION'] = 'gh-pages'
app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*', 'CNAME', '.gitignore', 'readme.md']
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_BASE_URL'] = 'http://snirp.nl'  # freezer uses this for _external=True URLs

@app.template_filter()
def date_nl(value):
    locale.setlocale(locale.LC_ALL, ('nl_NL', 'utf8@euro'))
    return value.strftime('%e %b %Y')

@app.template_filter()
def jinjatag(text):
    """allow jinja tags to be rendered in flat content"""
    return render_template_string(Markup(text))

@app.template_filter()
def markdown(text, extensions=['codehilite', 'fenced_code']):
    """render markdown to HTML, possibly using custom extensions"""
    return markdown_module.markdown(text, extensions)


### flatpage classes ###
class Pages(object):
    """
    Render flatpages with Flask: static site generator together with Frozen-Flask.
    An application can have multiple instances of Pages for different types
    of flatpages. Organize markup files in separate directories like 'blog' and
    'whitepages'. The filenames (minus suffix) should be valid url's.

    Add a YAML header to your Markdown files to set page-specific properties,
    such as: 'published', 'summary' or 'tags'.

    Caching is implemented for the properties and HTML content of the pages and
    for the automatically generated PDF files.

    Attributes:
        _cache          Stores Page-instance and last-modified per flatpage filepath.
        _pdfcache       Stores last-modified per PDF filepath.
        pdfdir          Directory that holds PDFs (in a subdir for each Pages instance).

    Arguments (instance specific):
        flatdir         Directory that holds the flat markup files.
        suffix          Only files with matching suffix are rendered.
    """
    _cache = {}
    _pdfcache = {}
    pdfdir = 'pdfcache'

    def __init__(self, flatdir='pages', suffix='.md'):
        self.flatdir = flatdir
        self.suffix = suffix

    def flatroot(self):
        return os.path.join(app.root_path, self.flatdir)

    def all_pages(self):
        """Generator that yiels a Page instance for every flatfile"""
        if not os.path.isdir(self.flatroot()):
            abort(404)
        for filename in os.listdir(self.flatroot()):
            if filename.endswith(self.suffix):
                yield self.get_page(filename[:-len(self.suffix)])

    def draft_pages(self):
        """filters unpublished pages and optionally slices to limit"""
        return [p for p in self.all_pages() if not p['published']]

    def published_pages(self):
        """filters published pages, sorts by published date and optionally slices to limit"""
        return sorted([p for p in self.all_pages() if p['published']],
                      reverse=True, key=lambda p: p['published'])

    def lastmod_pages(self):
        """sorts published pages by lastmod property"""
        return sorted(self.published_pages(), key=lambda p: p.lastmod())

    def tagged_pages(self, tag):
        return [p for p in self.published_pages() if tag in p['tags']]

    def get_page(self, name):
        """
        Return a Page instance from cache or instantiate a new one if outdated or absent.
        The file content is split in a (Markdown) body and (YAML) head section.
        Update the cache with the new or updated Page instance.
        """
        filepath = os.path.join(self.flatroot(), name+self.suffix)
        if not os.path.isfile(filepath):
            abort(404)
        mtime = os.path.getmtime(filepath)
        page, old_mtime = self._cache.get(filepath, (None, None))
        if not page or mtime != old_mtime:
            with io.open(filepath, encoding='utf8') as fd:
                head = ''.join(itertools.takewhile(lambda x: x.strip(), fd))
                body = fd.read()
            page = Page(name, head, body, self.flatdir)
            self._cache[filepath] = (page, mtime)
        return page

    def get_pdf(self, name):
        """
        Return a pdf file object for a Page instance.
        Create a pdf if no pdf exists or the underlying flatfile is more recent.
        Update the pdfcache after creating or updating a pdf.
        """
        try:
            from flask_weasyprint import HTML
        except ImportError:
            abort(404)
        flatpath = os.path.join(self.flatroot(), name+self.suffix)
        pdfpath = os.path.join(app.root_path, self.pdfdir, self.flatdir, name+'.pdf')
        if not os.path.isfile(pdfpath):
            try:
                HTML(self.get_page(name).url()).write_pdf(pdfpath)
            except IOError:
                abort(500)  # check if folder exists and you have write permission
            self._pdfcache[pdfpath] = os.path.getmtime(pdfpath)
        else:
            flat_mtime = os.path.getmtime(flatpath)
            if flat_mtime > os.path.getmtime(pdfpath):  # flatfile is more recent > new pdf
                try:
                    HTML(self.get_page(name).url()).write_pdf(pdfpath)
                except IOError:
                    abort(500)  # check if folder exists and you have write permission
                self._pdfcache[pdfpath] = os.path.getmtime(pdfpath)
        return open(pdfpath).read()

    def load_tags(self):
        tags = []
        for page in self.all_pages():
            tags = page['tags'] + tags
        return sorted(set(tags))


class Page(object):
    """
    Renders body to HTML and parse head to meta properties.

    Arguments (instance specific):
        name            Derived from filename of the flatfile.
        head            String to be rendered as YAML to properties
        body            String to be rendered as Markdown to HTML
        flatdir         Used to match Page object to its url's
    """

    def __init__(self, name, head, body, flatdir):
        self.name = name
        self.head = head
        self.body = body
        self.flatdir = flatdir

    def __getitem__(self, name):
        """getter to access the meta properties directly"""
        return self.meta.get(name)

    @werkzeug.cached_property
    def meta(self):
        """Render head section of file to meta properties."""
        return yaml.safe_load(self.head) or {}

    @werkzeug.cached_property
    def html(self):
        """Render Markdown and Jinja tags to HTML."""
        html = render_template_string(Markup(self.body))
        html = markdown_module.markdown(html, ['codehilite', 'fenced_code'])
        return html

    def lastmod(self):
        return self.meta.get('updated', self['published'])

    def url(self, **kwargs):
        """Return the url function for the detail page, based on convention of:
        <flatfile directory>_detail
        """
        return url_for(self.flatdir+'_detail', name=self.name, **kwargs)

    def pdf(self, **kwargs):
        """Return the url function for the pdf, based on convention of:
        <flatfile directory>_pdf
        """
        return url_for(self.flatdir+'_pdf', name=self.name, **kwargs)

### instantiate flatpage class ###
tip = Pages('tip')

### views ###
@app.route('/')
def home():
    return render_template('index.html', pageid='page-home')

@app.route('/contact.html')
def contact():
    return render_template('contact.html', pageid='page-contact')

@app.route('/tips.html')
def tip_index():
    tips = tip.published_pages()
    return render_template('tip-list.html', pageid='page-tip', tips=tips)

@app.route('/tip/atom.xml')
def tip_feed():
    articles = tip.lastmod_pages()[:10]
    feed_updated = articles[0].lastmod()
    xml = render_template('atom.xml', articles=articles, feed_updated=feed_updated)
    return app.response_class(xml, mimetype='application/atom+xml')

@app.route('/tip/<name>.html')
def tip_detail(name):
    t = tip.get_page(name)
    return render_template('tip-detail.html', pageid='page-tip', t=t)

@app.route('/tip/<name>.pdf')
def tip_pdf(name):
    pdf = tip.get_pdf(name)
    return app.response_class(pdf, mimetype="application/pdf")

@app.route('/sitemap.xml')
def generate_sitemap():
    # List of sites with manually added date(time) of last edit.
    sites = [
        (url_for('home', _external=True),       '2014-02-13'),
        (url_for('contact', _external=True),    '2014-02-13'),
        (url_for('tip_index', _external=True),  '2014-02-13'),
        (url_for('tip_feed', _external=True),   '2014-02-15')
    ]
    sites = [(s[0], datetime.date(*[int(ds) for ds in s[1].split('-')])) for s in sites] + \
            [(t.url(_external=True), t.lastmod()) for t in tip.published_pages()]
    xml = render_template('sitemap.xml', sites=sites)
    return app.response_class(xml, mimetype='application/atom+xml')


@app.route('/style.css')
def stylesheet():
    css = render_template('style.css')
    return app.response_class(css, mimetype='text/css')

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', pageid='page-404')

@app.route('/404.html')
def error_freeze():
    """explicitly set a route so that 404.html exists in gh-pages"""
    return render_template('404.html', pageid='page-404')


### launch ###
if __name__ == "__main__":
    app.run(debug=True)
