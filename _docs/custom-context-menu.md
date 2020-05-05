---
title: Custom Context Menu
permalink: /editor/custom-context-menu
layout: default
---

# Custom Context Menu

## Header
    caf::PdmChildArrayField<RicCreateMultipleFracturesOptionItemUi*> m_options;

## Constructor

    CAF_PDM_InitFieldNoDefault(&m_options, "Options", "Options", "", "", "");
    m_options.uiCapability()->setUiEditorTypeName(caf::PdmUiTableViewEditor::uiEditorTypeName());
    m_options.uiCapability()->setCustomContextMenuEnabled(true);

## Usage

    void RiuCreateMultipleFractionsUi::defineCustomContextMenu(const caf::PdmFieldHandle* fieldNeedingMenu,
                                                           QMenu*                     menu,
                                                           QWidget*                   fieldEditorWidget)
    {
        // Make sure selection manager is set up correctly
        // ...
        // then
	
        caf::CmdFeatureMenuBuilder menuBuilder;

        menuBuilder << "RicMyFeature";
        menuBuilder << "Separator";

        menuBuilder.appendToMenu(menu);
    }

## Context Menu in 3D views
When a command is supposed to be available in the 3D view in addition to right-clicking on objects in the **Property Editor**, the following pattern can be used. This allows the use of a feature from both **Property Editor** and 3D views at the same time. Usually, the current context widget should be investigated first before checking the currently selected object.

- Before the construction of items to be used in a menu, set the current context menu widget
- Add menu items and show the menu
- In the feature triggered, use the current context menu widget to find the relevant object to work on

Example taken from RicExportContourMapToTextFeature

    RimEclipseContourMapView* existingEclipseContourMap = nullptr;
    RimGeoMechContourMapView* existingGeoMechContourMap = nullptr;

    auto contextMenuWidget = dynamic_cast<RiuViewer*>(
        caf::CmdFeatureManager::instance()->currentContextMenuTargetWidget() );

    if ( contextMenuWidget )
    {
        {
            auto candidate = dynamic_cast<RimEclipseContourMapView*>( contextMenuWidget->ownerReservoirView() );
            if ( candidate )
            {
                existingEclipseContourMap = candidate;
            }
        }
        {
            auto candidate = dynamic_cast<RimGeoMechContourMapView*>( contextMenuWidget->ownerReservoirView() );
            if ( candidate )
            {
                existingGeoMechContourMap = candidate;
            }
        }
    }

    if ( !existingEclipseContourMap && !existingGeoMechContourMap )
    {
        existingEclipseContourMap = caf::SelectionManager::instance()->selectedItemOfType<RimEclipseContourMapView>();
        existingGeoMechContourMap = caf::SelectionManager::instance()->selectedItemOfType<RimGeoMechContourMapView>();
    }

    auto pair = std::make_pair( existingEclipseContourMap, existingGeoMechContourMap );

    return pair;
