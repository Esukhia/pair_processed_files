#!/usr/bin/env bash
for i in *.rtf; do libreoffice --headless --convert-to txt:Text "$i"; done

for i in *.docx; do libreoffice --headless --convert-to txt:Text "$i"; done
