#!/bin/bash
read -p "Commit to master, freeze and publish to gh-pages; Commit description: " desc
find /pdfcache -type f -name '*.pdf' -print0 |  xargs -0 rm
git add . && \
git add -u && \
git commit -m "$desc" && \
git push origin master
python freeze.py
cd gh-pages
gh-pages/git add . && \
git add -u && \
git commit -m "$desc" && \
git push origin gh-pages
cd ..