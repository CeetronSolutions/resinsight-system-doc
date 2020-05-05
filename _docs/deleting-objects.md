---
title: Object Deletion
permalink: /object/deletion
layout: default
---

## Deleting a Single Object

A single object can be deleted using RicDeleteItemFeature. Enable delete by changing the method [isDeletable()](https://github.com/OPM/ResInsight/blob/533b0001840056572e7d9c22c0a8b2eb17ef02c0/ApplicationCode/Commands/RicDeleteItemFeature.cpp#L75), and add the deletion code to [RicDeleteItemExec::redo()](https://github.com/OPM/ResInsight/blob/0b4156da026cd089f0b7ab896aa87b732789eb4d/ApplicationCode/Commands/RicDeleteItemExec.cpp#L74)

## Deleting Multiple Objects

Deleting of a selection of objects can be done in several ways. Multiselect in the tree view, and 'Delete' will issue a single object delete on each object in the collection.

If a collection can have very many objects, it is often convenient to have a command on the parent collection item in the tree view to delete all sub items. This is handled by [RicDeleteSubItemsFeature](https://github.com/OPM/ResInsight/blob/845b1acbbd5caa2172f8927e975227c494f2f4a0/ApplicationCode/Commands/RicDeleteSubItemsFeature.cpp) 
