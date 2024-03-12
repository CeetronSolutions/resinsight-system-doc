---
title: Virtual functions
permalink: /object/virtual-functions
layout: default
---

## Overview of virtual functions

A PDM object inherits PdmObject which inherits PdmUiObjectHandle. This documents gives an overview of virtual functions that can be overridden with short examples of usage. It is optional to override these functions, and most of them have a default implementation.
[cafPdmUiObjectHandle()](https://github.com/OPM/ResInsight/blob/dev/Fwk/AppFwk/cafProjectDataModel/cafPdmUiCore/cafPdmUiObjectHandle.h)

## appendMenuItems
Used to append menu items to the right click menu of an object. Previous pattern created these menus centralized in RimContextCommandBuilder which will be obsoleted.
```
void RimPolygon::appendMenuItems( caf::CmdFeatureMenuBuilder& menuBuilder ) const
{
    menuBuilder << "RicDuplicatePolygonFeature";
    menuBuilder << "Separator";
    menuBuilder << "RicExportPolygonCsvFeature";
}
```

## userDescriptionField
If defined, the string defined by this field will be used when displaying object text in the Property Tree.
```
caf::PdmFieldHandle* RimNamedObject::userDescriptionField()
{
    return nameField();
}
```

## objectToggleField
If defined, displays a checkbox next to the object in the Project Tree. The field must be of the boolean type.
```
caf::PdmField<bool>                         m_isActive;
caf::PdmFieldHandle* RimCellFilter::objectToggleField()
{
    return &m_isActive;
}
```

## fieldChangedByUi
Use this method to react on user interaction in the user interface. A pointer to the field being changed, old and new value is available.
```
void RimPolygon::fieldChangedByUi( const caf::PdmFieldHandle* changedField, const QVariant& oldValue, const QVariant& newValue )
{
    if ( changedField == &m_pointsInDomainCoords )
    {
        coordinatesChanged.send();
        objectChanged.send();
    }
}
```

## childFieldChangedByUi
When an object is contained in another object, the changes in the child object cna be tracked using this functions. The pointer to the field in the child object is given as parameter.

```
void RimPolygonFilter::childFieldChangedByUi( const caf::PdmFieldHandle* changedChildField )
{
    updateConnectedEditors();
}
```

## calculateValueOptions
When a list of available options is required, calculateValueOptions is used to populate the list with PdmOptionItemInfo. This is done automatically for enums.
```
QList<caf::PdmOptionItemInfo> RimCellFilter::calculateValueOptions( const caf::PdmFieldHandle* fieldNeedingOptions )
{
    QList<caf::PdmOptionItemInfo> options;

    if ( fieldNeedingOptions == &m_gridIndex )
    {
        RimTools::eclipseGridOptionItems( &options, eclipseCase() );
        RimTools::geoMechPartOptionItems( &options, geoMechCase() );
    }

    return options;
}
```

## defineUiOrdering
Defines the order and organization of fields in the Property Editor.
```
void RimCellFilter::defineUiOrdering( QString uiConfigName, caf::PdmUiOrdering& uiOrdering )
{
    uiOrdering.add( &m_name );
    auto group = uiOrdering.addNewGroup( "General" );
    group->add( &m_filterMode );

    // Used to skip display of other fields in the object
    uiOrdering.skipRemainingFields( true );
}
```

## defineUiTreeOrdering
Defines the order and organization of objects in the Project Tree.
```
void RimCompletionTemplateCollection::defineUiTreeOrdering( caf::PdmUiTreeOrdering& uiTreeOrdering, QString uiConfigName /*= ""*/ )
{
    uiTreeOrdering.add( m_valveTemplates );
    uiTreeOrdering.add( m_fractureGroupStatisticsCollection );
    uiTreeOrdering.skipRemainingChildren( true );
}
```

## defineEditorAttribute
Defines field editor specific configuration. The field editor is displayed in the Property Editor.
```
void RimEclipsePropertyFilter::defineEditorAttribute( const caf::PdmFieldHandle* field, QString uiConfigName, caf::PdmUiEditorAttribute* attribute )
{
    if ( field == &m_lowerBound || field == &m_upperBound )
    {
        if ( auto doubleAttributes = dynamic_cast<caf::PdmUiDoubleSliderEditorAttribute*>( attribute ) )
        {
            doubleAttributes->m_minimum = m_minimumResultValue;
            doubleAttributes->m_maximum = m_maximumResultValue;
        }
    }
}
```

## defineObjectEditorAttribute
Defines object editor specific configuration. The object editor can be used to manipulate objects from a 3D view.
```
void RimPolygonInView::defineObjectEditorAttribute( QString uiConfigName, caf::PdmUiEditorAttribute* attribute )
{
    if ( auto attrib = dynamic_cast<RicPolyline3dEditorAttribute*>( attribute ) )
    {
        attrib->pickEventHandler = m_pickTargetsEventHandler;
        attrib->enablePicking    = m_enablePicking;
    }

    if ( m_polygon() )
    {
        if ( auto* treeItemAttribute = dynamic_cast<caf::PdmUiTreeViewItemAttribute*>( attribute ) )
        {
            auto tag = caf::PdmUiTreeViewItemAttribute::createTag( RiaColorTools::toQColor( m_polygon->color() ),
                                                                   RiuGuiTheme::getColorByVariableName( "backgroundColor1" ),
                                                                   "---" );

            tag->clicked.connect( m_polygon(), &RimPolygon::onColorTagClicked );

            treeItemAttribute->tags.push_back( std::move( tag ) );
        }
    }
}
```

## defineCustomContextMenu
Defines a custom menu when a right-click menu is displayed when editing a field. This feature must be activated on the field.
```
// Activate the custom context menu
m_targets.uiCapability()->setCustomContextMenuEnabled( true );

void RimPolygonInView::defineCustomContextMenu( const caf::PdmFieldHandle* fieldNeedingMenu, QMenu* menu, QWidget* fieldEditorWidget )
{
    if ( m_polygon() && m_polygon->isReadOnly() ) return;

    caf::CmdFeatureMenuBuilder menuBuilder;

    menuBuilder << "RicNewPolylineTargetFeature";
    menuBuilder << "Separator";
    menuBuilder << "RicDeletePolylineTargetFeature";

    menuBuilder.appendToMenu( menu );
}
```
