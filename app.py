from flask import Flask, render_template, render_template_string, Markup
from flask_flatpages import FlatPages, pygmented_markdown

# initialization
app = Flask(__name__)
pages = FlatPages(app)

#settings
def prerender_jinja(text):
    return pygmented_markdown(render_template_string(Markup(text)))

app.config['FLATPAGES_EXTENSION'] = '.md'
app.config['FLATPAGES_MARKDOWN_EXTENSIONS'] = ['codehilite', 'headerid', 'fenced_code']
app.config['FLATPAGES_HTML_RENDERER'] = prerender_jinja

app.config['FREEZER_DESTINATION'] = 'gh-pages'
app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*', 'CNAME', '.gitignore']
app.config['FREEZER_RELATIVE_URLS'] = True

SITEMAP_DOMAIN = 'http://snirp.nl/'

# controllers
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/404.html')
def static_404():
    return render_template('404.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/tips.html')
def tip_list():
    tips = (p for p in pages if 'published' in p.meta)
    tips = sorted(tips, reverse=True, key=lambda p: p.meta['published'])
    return render_template('tip_list.html', tips=tips)

@app.route('/tip/<path:path>.html')
def tip_detail(path):
    tip = pages.get_or_404(path)
    return render_template('tip_detail.html', tip=tip)

@app.route('/sitemap.xml')
def generate_sitemap():
    webs = [
        ('', '2014-02-06'),
        ('tips.html', '2014-02-06'),
    ]
    sites = [(SITEMAP_DOMAIN + w[0], w[1]) for w in webs] + \
            [(SITEMAP_DOMAIN + 'tip/' + p.path + '.html', p.meta['lastmod']) for p in pages]
    return render_template('sitemap_template.xml', sites=sites)

# launch
if __name__ == "__main__":
    app.run(debug=True)

