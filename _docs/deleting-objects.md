---
title: Object Deletion from PdmChildArrayField
permalink: /object/deletion
layout: default
---

## Deleting an object in a caf::PdmChildArrayField
The easisest way to delete an object in a `childArrayField` is to mark the object as deletable using `setDeletable(true)`. Then the Pdm framework will make sure the general delete feature is active on the object. This will make sure the Delete feature is available from the context menu of the object.

The virtual method `PdmObjectHandle::onChildDeleted()` can be used when you need to trigger code after an object is deleted. This method will be called on the object having a `childArrayField` as member.

If additional updates are required, `caf::Signal` can be used.


[PdmObjectHandle::setDeletable()](https://github.com/OPM/ResInsight/blob/d11e109c7ec14bd10197b641c70616fa8d457e38/Fwk/AppFwk/cafProjectDataModel/cafPdmCore/cafPdmObjectHandle.cpp#L206)

[Delete Feature](https://github.com/OPM/ResInsight/blob/533b0001840056572e7d9c22c0a8b2eb17ef02c0/ApplicationCode/Commands/RicDeleteItemFeature.cpp#L75)

[cafSignal](https://github.com/OPM/ResInsight/blob/a9c9471e7fbb5b76d75277de3fa90f3a7f39e365/Fwk/AppFwk/cafProjectDataModel/cafPdmCore/cafPdmCore_UnitTests/cafSignalTest.cpp)
