#!/bin/bash
# Make sure we are using the virtualenv
source venv2/bin/activate
read -p "Commit description: " desc

# Delete .pdf files in pdfcache
find /pdfcache -type f -name '*.pdf' -print0 |  xargs -0 rm

# Commit master branch
git add . && \
git add -u && \
git commit -m "$desc" && \
git push origin master

# Freeze and commit gh-pages branch
python freeze.py
cd gh-pages
git add . && \
git add -u && \
git commit -m "$desc" && \
git push origin gh-pages
cd ..