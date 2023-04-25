---
title: Python In Visual Studio Code
permalink: /editor/python-in-visual-studio-code
layout: default
---

## Background
For enhanced interaction and debugging functionality of python code, the IDE [Visual Studio Code](https://code.visualstudio.com/) can be utilized. 

Python code is to be found in `\gitroot\ResInsight\GrpcInterface\Python\rips`. The `rips` library code represents the Python API for interaction with ResInsight, contianing both source code and tests by use of `pytest`.

To modify and test the Python API, an instance of ResInsight can be built and runned locally (e.g. using `Visual Studio`) or by running a released version at [https://resinsight.org/getting-started/download-and-install/](https://resinsight.org/getting-started/download-and-install/).

## Setting up Visual Studio Code
Create `New Window` and select `Open Folder...`, and browse to `\gitroot\ResInsight\GrpcInterface\Python\rips`:

![image](https://user-images.githubusercontent.com/82032112/234197647-6b5c393e-974d-4789-8c97-6718cbcb4426.png)

## Install required:

`Visual Studio Code`detects suggests recommended extension for Python if not already installed:

![image](https://user-images.githubusercontent.com/82032112/234199057-a1498d3a-6643-4236-9d1d-9f7302fdeef9.png)

If not suggested, got to the extension toolbar and write `"Python"` in the search - select the extension developed by `Microsoft`:

![image](https://user-images.githubusercontent.com/82032112/234199476-cbbefccb-653d-49cc-94ed-edaf03535eff.png)


## Python Tests in Visual Studio Code

- Open files in `tests\` to modify automatic tests implemented using `pytest`.
- Have a running instance of `ResInsight`
- Open the `Testing` tab in left side toolbar to show all detected tests in the folder.
- One can run all detected test files, individual files or even individual tests within a test file.

![image](https://user-images.githubusercontent.com/82032112/234201312-abf6dff6-ee84-4c70-820f-d10368e2ed17.png)


## Debug Python Tests in Visual Studio Code

- Each of the test run selections can be runned in Debug mode, providing the possibility to set breakpoint within the test code.

![image](https://user-images.githubusercontent.com/82032112/234201568-0ade70bd-3155-46c5-b86f-1ec6e731a481.png)

