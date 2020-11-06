---
title: Install Flow on Windows using WSL
permalink: /editor/install-flow-windows
layout: default
---

# Flow Simulator
The Open Porous Media project coordinates development of open source tools for simulation and visualization. 

OPM Flow is a fully-implicit, black-oil simulator capable of running industry-standard simulation models. 

Flow can be used as a drop-in replacement of the Eclipse simulatior.

This document describes how to use the Linux variant of Flow on Windows.

# Installation and use of Flow on Windows

## Installation of WSL
[Windows Subsystem for Linux Installation Guide for Windows 10](https://docs.microsoft.com/en-us/windows/wsl/install-win10)

## Installation of Ubuntu
[Ubuntu for WSL[(https://ubuntu.com/wsl)

## Installation of Flow

Based on [INSTALLING FROM BINARY PACKAGES](https://opm-project.org/?page_id=245)

```
sudo apt-get update
sudo apt-get install software-properties-common

sudo apt-add-repository ppa:opm/ppa
sudo apt-get update

sudo apt-get install mpi-default-bin
sudo apt-get install libopm-simulators-bin
```

# Use Flow

To access files on the Windows filesystem, use the `/mnt` folder in Linux. This folder displays the mapped drives.

Go to a simulation folder containing `*.DATA`
Execute
`flow myfile.DATA`

This will produce a simulation(*.EGRID *.UNRST *.UNSMRY). Use ResInsight to investigate the simulation.

# Links
[Open Porous Media (OPM)](https://opm-project.org/)
[Flow](https://opm-project.org/?page_id=19)
