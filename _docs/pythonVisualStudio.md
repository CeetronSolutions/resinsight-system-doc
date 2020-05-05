---
title: Python In Visual Studio
permalink: /editor/python-in-visual-studio
layout: default
---

## Background
Python code is generated from proto files, and is exported into `\gitroot\ResInsight\ApplicationCode\GrpcInterface\Python`

To be able to use Python from a debug version of ResInsight, the generated Python code must be added to the environment variable PYTHONPATH

This can be done by modifying the properties for ResInsight
![Python Visual Studio]({{site.baseurl}}/assets/images/python_environment_settings.png)

`PYTHONPATH=d:\gitroot\ResInsight\ApplicationCode\GrpcInterface\Python;$PYTHONPATH`
