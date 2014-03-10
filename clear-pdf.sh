#!/bin/bash
find /pdfcache -type f -name '*.pdf' -print0 |  xargs -0 rm