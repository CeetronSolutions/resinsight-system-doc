---
title: Reduce build times using ccache
permalink: /ccache
layout: default
---

## Compilation times

A rebuild of the full solutions can be as long as 10 mins, depending on the configuration. A few tricks can be used to reduce build times.

1. Do not include more than you need. Use forward declares as much as possible, and never include anything you dont need. 
2. Unity build: Cmake offers an option to batch source files to reduce the number of files for faster compilation. This is used on some build servers and on some development workstations.
3. Caching using `BuildCache`. When GitHub actions was introduced, there was a need to have a build cache working for both Linux and Windows. At that time, buildcache was the only option. This caching is now used on ResInsight github actions.
4. `ccache`. Recent deveopment has now make `ccache` easily available on Windows. The speedup in compilation time can be quite impressive.


## Configuration and use of ccache (Windows)
1. Download and install ccache https://ccache.dev/download.html
2. In the `ResInsight` cmake defines, set the full path to the ccache.exe in the define "ccache_exe"
3. Make sure that all `CXX_*` compiler flags use `/Z7` instead of `/Zi`. If `/Zi` is used, ccache will not work.
4. To see where your cache is located, use the ccache -p


## References
https://github.com/mbitsnbites/buildcache
https://cmake.org/cmake/help/latest/prop_tgt/UNITY_BUILD.html
https://github.com/OPM/ResInsight/blob/dev/.github/workflows/ResInsightWithCache.yml

CMake config for ccache
https://github.com/OPM/ResInsight/blob/14d4022ada59aa6903e54a2bccca26d0d4907509/CMakeLists.txt#L48-L60

CMake config for Unity build
https://github.com/OPM/ResInsight/blob/14d4022ada59aa6903e54a2bccca26d0d4907509/CMakeLists.txt#L141-L153
