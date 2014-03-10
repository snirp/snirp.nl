#!/bin/bash
read -p "Commit to master, freeze and publish to gh-pages; Commit description: " desc
git add . && \
git add -u && \
git commit -m "$desc" && \
git push heroku master