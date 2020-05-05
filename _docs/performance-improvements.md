---
title: Performance improvements
permalink: /editor/performance
layout: default
---

# Performance improvements
During performance improvement work, some observations was made. Listing the actions giving most performance gain.

## Moving variable definitions out of loop
Moving variable definitions out of loop, generally lead to performance gain. However, in some cases the performance gain is marginal. It seems that the stack variable creation itself is a cheap operation, while assigning/copying values into the variable is more expensive, especially when dealing with large classes.
Most performance gain is achieved by moving out definitions of variables that are not being assigned a value, but sent as in/out argument to an other method. The bottom line here is to minimize the number of times a variable is being copied.

### Concrete results
In a concrete test, four variable definitions were moved out of a loop. All variables were sent as output arguments to other methods in the loop. The actual method tested was executed a huge number of times and time consumption was measured. There was as much as 20% reduction in time consumption after moving the variable definitions.

## Running loop iteration in parallel
Parallel loops by using OpenMP will in many cases give a significant performance gain. Most performance gain is achieved for loops with many time consuming iterations. Ensure that the iterations are separated data wise. If the iterations have to write data to a shared collection, try to avoid costly synchronizing mechanisms. Instead, use an array (for instance) where each iteration has 'its own' element.
Some post processing may have to be performed in this case.

### Concrete results
In a concrete test the time consumption after parallelized a for loop of two iteration was measued to about 35%. This number will likely increase significantly as the number of iterations increases.
