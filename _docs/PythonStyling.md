---
title: Python Style Guide
permalink: /editor/python-style-guide
layout: default
---


Should follow PEP 8: https://www.python.org/dev/peps/pep-0008/
## Installation of tools
`pip install autopep8`

## Configuration
File located at top of repository named `setup.cfg`

## Procedure
In folder ResInsight\ApplicationCode\GrpcInterface\Python\rips execute the following

`python -m autopep8 --in-place --recursive .`

## Automatically execute pylint with pep8
https://pypi.org/project/autopep8/#installation

`python -m autopep8 --in-place .\Properties.py`
