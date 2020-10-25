---
title: vcpkg
permalink: /editor/vcpkg
layout: default
---


# vcpkg
We are using vcpkg to take care of some of the external dependencies ResInsight has.

## Make sure the submodules are updated
In the main folder of ResInsight, issue the following commands

    git submodule init
    git submodule update

Check in the Thirdpary/vcpkg folder to make sure source files are downloaded correctly from GitHub

## Windows Configuration
On Windows, open a x64 Native Tools Command Prompt for VS 2019
![x64 Native tool]({{site.baseurl}}/assets/images/x64_native_tool.png)

Go to the source code folder ResInsight/Thirdparty

Run the following commands

    vcpkg/boostrap-vcpkg.bat
    vcpkg/vcpkg install grpc boost-filesystem eigen3 --triplet x64-windows


## Linux Configuration
Go to the source code folder ResInsight/Thirdparty

    vcpkg/boostrap-vcpkg.sh
    vcpkg/vcpkg install grpc boost-filesystem eigen3 --triplet x64-linux
    
## cmake configuration
When vcpkg is compiled, and the grpc dependencies are compiled, the ResInsight cmake configuration must be updated to use the vcpkg configuration. This is done using the following define for cmake

    -DCMAKE_TOOLCHAIN_FILE=../ThirdParty/vcpkg/scripts/buildsystems/vcpkg.cmake

Using the GUI, the toolchain must be specified as the first step when you are creating your build folder 

![cmake toolchain file]({{site.baseurl}}/assets/images/cmake_toolchain_file.png)


## Links 
[vcpkg main documentation](https://vcpkg.readthedocs.io/en/latest/)
