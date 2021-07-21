#!/bin/sh

echo \
'<!DOCTYPE html>
<html>
  <head>
    <style>
body {
  font-family: sans-serif;
  max-width:700px;
  margin:auto;
  text-align:top;
}
    </style>
  </head>

<body>'

markdown "$1"

echo \
' </body>

</html>'
