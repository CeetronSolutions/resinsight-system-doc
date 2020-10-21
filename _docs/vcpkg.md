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
    vcpkg/vcpkg install grpc --triplet x64-windows


## Linux Configuration
Go to the source code folder ResInsight/Thirdparty

    vcpkg/boostrap-vcpkg.sh
    vcpkg/vcpkg install grpc --triplet x64-linux

## Links 
[vcpkg main documentation](https://vcpkg.readthedocs.io/en/latest/)
