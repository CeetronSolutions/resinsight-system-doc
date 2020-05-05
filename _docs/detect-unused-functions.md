---
title: Detect unused functions
permalink: /editor/detect-unused-functions
layout: default
---

# Build server overview
The build server is building ResInsight source code, and has an additional job performing CppCheck on the code base. The report from CppCheck can look like this

1. Create a file in /ResInsight/doc/<date>-delete-unused-function.txt
2. Move with all functions reported as unused into categories
3. Check with previously identified functions in category 'Nothing to do'
4. Try to remove function in code, if successful, move to category 'Deleted'

# References
[Build Server including CppCheck](http://10.10.0.26:8080/job/ResInsight-static-code-analysis/)
