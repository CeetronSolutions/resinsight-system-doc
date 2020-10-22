---
title: C++ Code Standards
permalink: /codestandards
layout: default
---

# Code Standards 

New code should be based on C++17 and follow the C++ Core Guidelines to the best of our ability:

## No "naked new/delete" in application code ##
Use PdmField / PdmChildField for PdmObjects which own other PdmObjects. Otherwise use smart pointers (std::unique_ptr, std::shared_ptr, cvf::ref).

Use the new C++14 creation rather than new. I.e:
```
auto object = std::make_unique<Object>();
```
rather than 
```
std::unique_ptr ptr (new Object).
```
PdmPointer<T> should only be used for referencing objects owned somewhere else and not for ownership as it contains no reference counting.

  
* Avoid passing of bare pointers for methods that require the pointer to not be nullptr. I.e. instead of bool save(QString* errorMsg) Instead use bool save(gsl::not_null<QString*> errorMsg).
  This removes the need for a CAF_ASSERT(errorMsg) inside the method body.
* As much as possible use for (auto [startMD, endMD] : wellSegments()) instead of (auto segmentPair : wellSegments) { auto startMD = segmentPair.first; auto endMD = segmentPair.second ...
