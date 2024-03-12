---
title: Virtual functions
permalink: /object/virtual-functions
layout: default
---

## Overview of virtual functions

A PDM object inherits PdmObject which inherits PdmUiObjectHandle. This documents gives an overview of virtual functions that can be overridden with short examples of usage.
[cafPdmUiObjectHandle()](https://github.com/OPM/ResInsight/blob/dev/Fwk/AppFwk/cafProjectDataModel/cafPdmUiCore/cafPdmUiObjectHandle.h)

## appendMenuItems
Used to append menu items to the right click menu of an object. Previous pattern created these menus centralized in RimContextCommandBuilder which will be obsoleted.

void RimPolygon::appendMenuItems( caf::CmdFeatureMenuBuilder& menuBuilder ) const
{
    menuBuilder << "RicDuplicatePolygonFeature";
    menuBuilder << "Separator";
    menuBuilder << "RicExportPolygonCsvFeature";
}

## userDescriptionField
If defined, the string defined by this field will be used when displaying object text in the Property Tree.

caf::PdmFieldHandle* RimNamedObject::userDescriptionField()
{
    return nameField();
}

## objectToggleField
If defined, displays a checkbox next to the object in the Project Tree. The field must be of the boolean type.

caf::PdmField<bool>                         m_isActive;
caf::PdmFieldHandle* RimCellFilter::objectToggleField()
{
    return &m_isActive;
}

## fieldChangedByUi
Use this method to react on user interaction in the user interface. A pointer to the field being changed, old and new value is available.

## objectToggleField
If defined, displays a checkbox next to the object in the Project Tree. The field must be of the boolean type.

void RimPolygon::fieldChangedByUi( const caf::PdmFieldHandle* changedField, const QVariant& oldValue, const QVariant& newValue )
{
    if ( changedField == &m_pointsInDomainCoords )
    {
        coordinatesChanged.send();
        objectChanged.send();
    }
}



