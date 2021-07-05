#!/bin/sh
mkdir -p ~/.config/deromanize/
mv ./config.yml ~/.config/deromanize/
python3 -m venv venv
. venv/bin/activate
pip install -U pip
pip install "git+https:///github.com/FID-Judaica/arcapi.git"
