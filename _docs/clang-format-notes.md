---
title: Clang Format Notes
permalink: /system/clang-format-notes
layout: default
---

# Clang Format Notes

The intention is to activate format-on-save in Visual Studio. Either use integration in Visual Studio for format-on-save, or use Clang Power Tools.

## Install Clang Power Tools

1. Install plugin
[Clang Power Tools Plugin](https://marketplace.visualstudio.com/items?itemName=caphyon.ClangPowerTools)

2. Install LLVM 15 in Clang Power Tools
![Clang Power Tools LLVM]({{site.baseurl}}/assets/images/clang-power-tools-llvm.png)

4. The version selected in GUI can be overriden by manually setting the to clang-format
Set the path to clang-format in "Custom executable" for Clang Power Tools. clang-format installed by Clang Power Tools will put the executable
in path similar to :

```
C:\Users\ruben\AppData\Roaming\ClangPowerTools\LLVM\LLVM15.0.0\bin\clang-format.exe
```



## GitHub Action
A GitHub Action is running clang-format when changes is pushed to a branch. If clang-format issues are detected, a new PR is created.

[clang-format action for ResInsight](https://github.com/OPM/ResInsight/blob/dev/.github/workflows/clang-format.yml)

## Use with PowerShell
If you need to do apply clang format on all files, it is useful to use PowerShell

1. Add clang-format to path

```
$env:Path += ";C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\IDE\VC\vcpackages\"
```

2. Powershell syntax command to apply clang-format on header/cpp files in a folder recursively. **Start in ResInsight/ApplicationCode**

```
dir -recurse -include *.cpp,*.h,*.inl | %{clang-format -fallback-style=none -i $_.FullName}
```

## References
https://clang.llvm.org/docs/ClangFormat.html

