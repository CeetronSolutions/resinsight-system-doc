---
title: C++ Code Standards
permalink: /codestandards
layout: default
---

# Code Standards 

New code should be based on C++17 and follow the C++ Core Guidelines to the best of our ability:

## No "naked new/delete" in application code
Use PdmField / PdmChildField for PdmObjects which own other PdmObjects. Otherwise use smart pointers (std::unique_ptr, std::shared_ptr, cvf::ref).

Use the new C++14 creation rather than new. I.e use:
```
auto object = std::make_unique<Object>();
auto cvfObject = cvf::make_ref<cvf::Object>();
```
rather than 
```
std::unique_ptr ptr (new Object);
cvf::ref<cvf::Object> = new cvf::Object;
```
PdmPointer<T> should only be used for referencing objects owned somewhere else and not for ownership as it contains no reference counting.
  
### Exception for Qt
Qt widgets and layouts takes over ownership of widgets assigned to them. It would thus be dangerous to pass a unique_ptr into it.
The following is thus ***dangerous*** since the unique_ptr and layout both assumes ownership.
```
auto label = std::make_unique<QLabel>();
layout->addWidget(label.get());
```

However, the following is acceptable (and safer than using new, because you don't risk leaks if you forget to assign a widget):
```
auto label = std::make_unique<QLabel>();
layout->addWidget(label.release());
```

## Avoid passing bare pointers to methods which require the pointer to not be null. 
Use 
```
bool save(gsl::not_null<QString*> errorMsg);
```
instead of 
```
bool save(QString* errorMsg)
{
  CAF_ASSERT(errorMsg);
  ...
}
```

## Use structured binding assignment for pairs and tuples. 
Use
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
