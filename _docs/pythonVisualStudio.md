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

Powershell

`$Env:PYTHONPATH += ";E:\gitroot-second\ResInsight\GrpcInterface\Python"`

## Debugging from Visual Studio
To be able to Python code without a GUI, ResInsight can be started in console mode. When running in console mode, the Python tests can be started using `--existing`. Then pytest will launch the tests using an existing running instance of ResInsight.

Start ResInsight in console mode by adding `--console` to start up arguments in "Debugging->Command Arguments"

From the command line (powershell), set working folder to rips and launch **pytest** using this statement
    
    cd GrpcInterface\Python\rips 
    python -m pytest --existing
