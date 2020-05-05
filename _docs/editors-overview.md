---
title: Editors Overview
permalink: /editor/overview
layout: default
---

# Editors Overview
Editors are used to build user interface for fields.

Setting the list editor on a field is done by

`<field>.uiCapability()->setUiEditorTypeName(caf::PdmUiListEditor::uiEditorTypeName());`

## Default editors

The default editors are defined at [PdmUiDefaultObjectEditor](https://github.com/OPM/ResInsight/blob/b87c5fb8c86a86f9e9335ff7604f7c9d08102c22/Fwk/AppFwk/cafUserInterface/cafPdmUiDefaultObjectEditor.cpp#L52-L65)


| Editor Type | Field types using editor by default
| ------------------------ | -------------
| PdmUiLineEditor | QString
| | int
| | double
| | float
| | quint64
| |
| PdmUiDateEditor | QDate
| | QDateTime
| |
| PdmUiListEditor | `std::vector<QString>`
| | `std::vector<int>`
| | `std::vector<unsigned int>`
| | `std::vector<float>`
| |
| PdmUiCheckBoxEditor | bool

## Editor attributes
Some editors can be customized by using editor attributes. These attributes can be manipulated in a PdmObject by overriding

`virtual void defineEditorAttribute(const caf::PdmFieldHandle* field, QString uiConfigName, caf::PdmUiEditorAttribute* attribute) {}`
