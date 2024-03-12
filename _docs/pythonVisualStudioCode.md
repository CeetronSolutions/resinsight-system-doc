---
title: Python In Visual Studio Code
permalink: /editor/python-in-visual-studio-code
layout: default
---

# Background
For enhanced interaction and debugging functionality of python code, the IDE [Visual Studio Code](https://code.visualstudio.com/) can be utilized. 

Python code is found in folder `\gitroot\ResInsight\GrpcInterface\Python\rips`. The `rips` library code represents the Python API for interaction with ResInsight, contianing both source code and tests. The Python API is developed by use of [`gRPC`](https://grpc.io/) and provides provedure calls from Python to ResInsight C++ code.

To modify and test the Python API, an instance of ResInsight can be built and runned locally (e.g. using `Visual Studio`) or by running a released version from [https://resinsight.org/getting-started/download-and-install/](https://resinsight.org/getting-started/download-and-install/).

# Setting up virtual environment
The `rips` code can be run by creating a virtual environment, installing the `rips`-package into the virtual environment.
Using [`venv`](https://docs.python.org/3/library/venv.html) for Python and a local folder named `"ResInsightPythonScripts"`, the venv and python files
can be set up to test the `rips`-package.

With the following steps, the rips package is available in the venv named `ResInsightVenv`. A python file can be created, and usage of `rips`-package can be
tested in the venv. 

Note: If any missing packages occur, these can be installed in the venv using pip.

### For Windows
With a local folder `D:\ResInsight Python Scripts` for venv and scripts.
```
D:\ResInsightPythonScripts>python -m venv .ResInsightVenv
D:\ResInsightPythonScripts>".ResInsightVenv\Scripts\activate"
(.ResInsightVenv) D:\Git\ResInsight>

# Navigate to ResInsight Python folder and pip install the rips package in venv
(.ResInsightVenv) D:\ResInsightPythonScripts>cd ..\Git\ResInsight\GrpcInterface\Python
(.ResInsightVenv) D:\Git\ResInsight\GrpcInterface\Python>pip3 install -e .

# Navigate back to script folder
(.ResInsightVenv) D:\Git\ResInsight\GrpcInterface\Python>cd D:\ResInsightPythonScripts
```

### For Ubuntu
The same steps can be done for Ubutu, providing the same folder, venv and `rips`-package install. VS Code can be utilized (for WSL distro if used from Windows) as for Windows in the `"Run and debug scripts"`-section below.

# Run and debug scripts
Open VS Code and select `"Open Folder..."`. Navigate to the `"ResInsightPythonScripts"`-folder.

With a running instance of ResInsight (with gRPC build), the virtual environment, with installed `rips`, must be activated, and the Python API (gRPC interface) can be tested.

### Select virtual evnironment
Pushing `F1` and write `"Python: Select Interpreter"`, then navigate to the virtual environment create in previous stage.

![image](https://github.com/CeetronSolutions/resinsight-system-doc/assets/82032112/7dca545a-6bf3-4c58-9424-96bcde385c11)

### Create python script
Create a file for testing `rips`-packageWith a test file `my_python_file.py`. The file can be run by `python .\my_python_file.py`, or by using debug python code in Visual Studio Code.

- A debugger for Python File can be customized by selecting `"create a launch.json file"`, and select `"Python File"` among Debug Configuration options:

  ![image](https://github.com/CeetronSolutions/resinsight-system-doc/assets/82032112/bd570cbf-8250-4ffb-a8c0-9d261f8932c9)

- With a customized debugger, the test file can then be debugged with breakpoints in VS Code:

  ![image](https://github.com/CeetronSolutions/resinsight-system-doc/assets/82032112/042d1b5f-b5a9-4460-9497-afc6c5088f24)








