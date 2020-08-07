---
title: Progress Counters
permalink: /object/progress
layout: default
---

## Best practices for progress counting
The ResInsight progress update system is available in cafUserInterface as caf::ProgressInfo. Each method that needs to track progress needs to speficy a maximum number of steps
in the constructor of caf::ProgressInfo. 
You typically then have a number of sub-task with different progress messages, taking different amounts of time. You can specify the progress description and the next progress increment with nextProgressIncrement and then calling incrementProgress once the sub-task is complete.

However, this leads to a lot of noise in the code, with lots of code lines dealing with progress updates and not actual algorithm logic. A more consise way is to use the ProgressTask system
through the ProgressInfo::task() method. This returns a RAII (Resource Aquisition Is Initialization) type object that causes the progress update to occur when the object
is deleted by going out of scope. Example:

    {
        auto task = progInfo.task( "Creating formation track", 2 );
        createFormationTrack( plot, fractureModel, eclipseCase );
    }

    {
        auto task = progInfo.task( "Creating facies track", 2 );
        createFaciesTrack( plot, fractureModel, eclipseCase );
    }

    {
        auto task = progInfo.task( "Creating layers track", 2 );
        createLayersTrack( plot, fractureModel, eclipseCase );
    }
    
This technique creates code that more clearly shows different sub-tasks and uses just one line for each sub-task to deal with progress updates.
