---
title: Application Unit Test
permalink: /editor/application-unit-test
layout: default
---


# Application Unit Test
ResInsight has several application unit tests located in the `ApplicationCode/UnitTests` folder.

## Test datasets
Files used by the unit tests can be stored in the folder `ApplicationCode/UnitTests/TestData`

To use the data here, use the define **TEST_DATA_DIR** before appending the specific folder used in the test.

`QString testDataRootFolder = QString("%1/ParsingOfDataKeywords/").arg(TEST_DATA_DIR);\ `

## Running a subset of tests

If you want to execute a subset of tests, add the following to `RiaApplication::launchUnitTests()`

 `::testing::GTEST_FLAG( filter ) = "RigReservoirTest.BasicTest*";`
 
 [More info](https://stackoverflow.com/questions/12076072/how-to-run-specific-test-cases-in-googletest)
