---
title: Table Editor
permalink: /editor/table
layout: default
---

# Table Editor

## Usage

## Header
    caf::PdmChildArrayField<RicCreateMultipleFracturesOptionItemUi*> m_options;

## Implentation

### Constructor

    CAF_PDM_InitFieldNoDefault(&m_options, "Options", "Options", "", "", "");
    m_options.uiCapability()->setUiEditorTypeName(caf::PdmUiTableViewEditor::uiEditorTypeName());

