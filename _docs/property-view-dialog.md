---
title: Property View Dialog
permalink: /property-view-dialog
layout: default
---

# Property View Dialog

An object can be displayed in the Property Editor as a dock widget. In features, if user input is reqired on an pdm object, it is often convinient to display UI for the object in a caf::PdmUiPropertyViewDialog


## Example

```cpp
RiuCreateMultipleFractionsUi* multipleFractionsUi = proj->dialogData()->multipleFractionsData();
if (multipleFractionsUi)
{
    QString incomingObject = multipleFractionsUi->writeObjectToXmlString();

    caf::PdmUiPropertyViewDialog propertyDialog(
        Riu3DMainWindowTools::mainWindowWidget(), multipleFractionsUi, "Create Multiple Fractions", "");

    if (propertyDialog.exec() != QDialog::Accepted)
    {
        multipleFractionsUi->readObjectFromXmlString(incomingObject, caf::PdmDefaultObjectFactory::instance());
    }
}
```

If the dialog is cancelled, the original state of the object is restored using `readObjectFromXmlString()`
