---
title: C++ Code Standards
permalink: /codestandards
layout: default
---

# Code Standards 

New code should be based on C++17 and follow the C++ Core Guidelines to the best of our ability:

## No "naked new/delete" in application code
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

## Avoid passing bare pointers to methods which require the pointer to not be null. 

I.e. instead of 
```
bool save(QString* errorMsg)
{
  CAF_ASSERT(errorMsg);
  ...
}
```
use 
```
bool save(gsl::not_null<QString*> errorMsg);
```

## Use structured binding assignment for pairs and tuples. 
I.e.
```
for (auto [startMD, endMD] : wellSegments())
{
...
}
```
not
```
for (auto segmentPair : wellSegments)
{ 
  auto startMD = segmentPair.first;
  auto endMD = segmentPair.second;
  ...
}
