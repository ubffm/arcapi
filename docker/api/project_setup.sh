#!/bin/sh
mkdir -p ~/.config/deromanize/
mv ./config.yml ~/.config/deromanize/
python3 -m venv venv
venv/bin/pip install -U pip
venv/bin/pip installa -r requirements.txt
venv/bin/pip install "git+https:///github.com/ubffm/arcapi.git"
