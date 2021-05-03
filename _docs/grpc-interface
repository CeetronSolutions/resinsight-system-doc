---
title: GRPC Interface
permalink: /editor/grpc-interface
layout: default
---

## Description of grpc interface

There are two main ways to use the grpc interface.
1. Share implementation with command file commands
2. Direct methods on PDM objects

### Command file commands and Python commands
When sharing the implementation with both command file and Python, the command objects must derive from `RicfCommandObject`. Each scriptable field must be made availabla using
the `CAF_PDM_InitScriptableField` macro.

Command file commands are read and parsed in `RicfCommandFileReader::readCommands`
Python command objects are read and parsed in `RiaGrpcCommandService::Execute`

Parameters to grpc commands are defined in `Commands.proto` The, ResInsight creates the file `Commands_pb2.py` based on the definitions in the proto file. Then these commands 
are used from the relevant Python object. 

**Example**
export_well_path_completions is a method defined in case.py. This method is a forward to `ExportWellPathCompRequest` defined in `Commands_pb2.py`.

### Direct functions on PDM objects
Use CAF_PDM_InitScriptableObject to make a class available for scripting in Python. Then, fields can be made scriptable using `CAF_PDM_InitScriptableField`

A function can be made available in Python by adding extra function objects to an existing Pdm object by deriving  from `PdmObjectMethod`. These are parsed, and added to the corresponding generated Python code in .

**Example**
RimSummaryCase is available as class SummaryCase in `generated_classes.py`. RimSummaryCase_summaryVectorValues is defining a function used to get vector values from a summary string. This function is available in through the wrapping of the Pdm data model in generated_classes.py as function `summary_vector_values()` 

