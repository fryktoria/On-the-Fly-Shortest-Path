# On-the-Fly Shortest Path plugin


## Introduction
The “On-the-Fly Shortest Path” QGIS plugin offers an interactive measurement of distances along a line network, operating directly on the map. It calculates Distance and the Fiber Loss Budget in fiber optic networks (backbone or FTTH).

The plugin makes use of the Dijkstra algorithm of the core Network Analysis library of QGIS in order to calculate the shortest path and measure the distance from start to end.

Subsequently, it calculates the Fiber Loss Budget of this path, considering several configured parameters (connector loss, splice loss, fiber attenuation, splitters etc.).

In contrast to similar algorithms of the Processing toolbox, this plugin does not create a new layer for every measurement but rather presents the path and the calculated parameters directly on screen, allowing for massively continuous measurements. This functionality is similar to the original RoadGraph plugin of QGIS2.

In addition, the plugin allows the setting of optional middle points, forcing the path to go first from the start point to each one of the middle points and finally to the end point. This is helpful in networks with multiple paths between the start and stop point where the user wants to direct the algorithm to use a preferred path.

Visit the [Online documentation](https://fryktoria.github.io/On-the-Fly-Shortest-Path/) web page for details on installing and using the plugin.