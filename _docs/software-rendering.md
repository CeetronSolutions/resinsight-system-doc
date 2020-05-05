---
title: Software Rendering
permalink: /software-rendering
layout: default
---
# Qt5 with software rendering
When using ResInsight in Remote Desktop on Windows, software rendering is required. This mode can be activated by renaming a DLL in the same folder as ResInsight.exe: Rename opengl32sw.dll to opengl32.dll


## NB OBSOLETE, relevant for Qt4

In some cases, shader support is not available. This is the case when ResInsight is used over a Remote Desktop connection on Windows. 

Download [OS Mesa](https://www.mesa3d.org/osmesa.html) and

Copy the files following files from **mesa-binaries\x64**  into the same folder as ResInsight.exe :

    libglapi.dll 
    opengl32.dll 
