---
title: Include fields from child objects
permalink: /system/include-fields-from-child-objects
layout: default
---

When designing the property editor content, it might be useful to include content from child objects.

## Include of complete child object
To create a good visual organization it works often well with a group holding the content of a child object.

    caf::PdmUiGroup* mudWeightWindowGroup = uiOrdering.addNewGroup( "Mud Weight Window" );
    m_mudWeightWindowParameters->uiOrdering( uiConfigName, *mudWeightWindowGroup );


## Include a subset of fields from a different object

If you want to include a subset of fields from a different object, there are two options

### 1. Include the fields directly

In defineUiOrdering() of the object to be displayed :

    MyOtherObject* myObj;

    uiOrdering.add(myObj->fieldA());
    uiOrdering.add(myObj->fieldB());

### 2. Use the uiConfigName

In defineUiOrdering() of the object to be displayed :

    MyOtherObject* myObj;
    QString mySpecialConfig = "configName";

    caf::PdmUiGroup* mudWeightWindowGroup = uiOrdering.addNewGroup( "Mud Weight Window" );
    m_mudWeightWindowParameters->uiOrdering( mySpecialConfig, *mudWeightWindowGroup );

