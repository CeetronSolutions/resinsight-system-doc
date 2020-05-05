---
title: Regression Tests
permalink: /regression-tests
layout: default
---

## Regression Tests

The folder containing the test, must start with `TestCase_`

One project file named `RegressionTest.rsp` must be put into the test folder. This project file will automatically be imported, and snapshot will be taken of all views in this project.

## Command Files
To use a command file, create a text file named `commandfile-your_file_name.txt` and store this file in the same folder as the project file. When the regression test is started, the content of this file is executed.
