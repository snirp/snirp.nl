#!/bin/bash

# Make sure we are using the virtualenv
source venv2/bin/activate
read -p "Commit description: " desc

# Freeze application
python freeze.py

# Commit master branch
git add . && \
git add -u && \
git commit -m "$desc" && \
git push origin master

# Commit gh-pages branch
cd gh-pages
git add . && \
git add -u && \
git commit -m "$desc" && \
git push origin gh-pages
cd ..