# On-the-Fly Shortest Path plugin


## Introduction
The "On-the-Fly Shortest Path" QGIS plugin offers an interactive measurement of distances along a line network, operating directly on the map. It calculates Distance and the Fiber Loss Budget in fiber optic networks (backbone or FTTH). 

The plugin uses the core Network Analysis library of QGIS in order to calculate the shortest path via the Dijkstra algorithm. 

Subsequently, it calculates the Fiber Loss Budget of this path, considering several configured parameters (connector loss, splice loss, fiber attenuation, splitters etc.). 

In contrast to similar algorithms of the Processing toolbox, this plugin does not create a new layer for every measurement but rather presents the path and the calculated parameters directly on screen. This functionality is similar to the original RoadGraph plugin of QGIS2. 

In addition, the plugin allows the setting of optional middle points, forcing the path to go first from the start point to each one of the middle points and finally to the end point. This is helpful in networks with multiple paths between the start and stop point where the user wants to direct the algorithm to use a preferred path. 

## Quick links
  - [Usage instructions](#usage)
  - [Configuration parameters](#configuration)
  - [Installation](#installation)
  - [Handling of multiple layers](#handling-of-multiple-layers)

## Support, Issues and new features

The plugin documentation is found in [the project page](https://fryktoria.github.io/On-the-Fly-Shortest-Path/). Currently, this documentation is the current file. Additional content may be added in the future.

Please report bugs in the [Github issues URL](https://github.com/fryktoria/On-the-Fly-Shortest-Path/issues)

You can participate in the development with new ideas, using the [Github discussions URL](https://github.com/fryktoria/On-the-Fly-Shortest-Path/discussions/). Although the plugin functionality has been developed over several iterations and has finally reached the original vision, the priority was set to the functionality itself as well as the documentation, to help users make the best of the plugin. Several parts of the code require clean-ups, being mostly remnants of previous trial-and-error, as well as architectural concepts that were finally impelemented in a different manner or not implemented at all. It is not expected to have improvements in speed and performance. Future development will focus mainly on tidying up for cleaner code, unless something more exciting comes up. 

For any other issue, you can send a mail to mailto:info@fryktoria.com

## <a name="installation"></a> Installation

### Install from the official QGIS plugin repository
1. From the QGIS toolbar, select `Plugins -> Manage and Install Plugins...`.

2. From the panel on the left side of the `Plugins|Settings` window, select `All`. Navigate to the list to locate the plugin name `On-the-Fly Shortest Path` and press `Install Plugin`. Optionally, you can use the `Search...` facility to locate the plugin by typing its name `On-the-Fly Shortest Path`.

### <a name="install-from-a-zip-file"></a>Install from a zip file

1. Download the zip file containing the plugin to a directory of your choice.

2. From the QGIS toolbar, select `Plugins -> Manage and Install Plugins...`. 

3. From the panel on the left side of the new form, select `Install from ZIP`. Select the file downloaded in step 1.

After installation is complete, you should be able to see the plugin name in the list of installed plugins. 

Also, to confirm that installation was made properly, from the QGIS toolbar, select `View -> Panels`. You should see the `On-the-Fly Shortest Path` in the list of panels. Activate it by clicking on the checkbox. 

## Build from Github sources

Follow these instructions if you want to create manually a zip file to install into QGIS using the process described in the __[Install from a zip file](#install_from_a_zip_file)__  section.

1. Download all files from Github
2. Create a directory named `On-the-Fly-Shortest-Path` and move all files to this directory
3. Use your favorite compression tools to create a zip file __which contains the directory__ and not the individual files. This structure is mandatory so that the set of files is understood by QGIS as a plugin.
4. Install the plugin using the procedure in __[Installation](#installation)__ section.


## <a name="activation"></a>Activation

The plugin panel should be visible on the left-hand side of the QGIS screen. If you do not see it, first make sure that the plugin is activated.

1. From the QGIS toolbar, select `Plugins -> Manage and Install Plugins...`.

2. The window `Plugins|Settings` will open. From the panel on the left side of the window, select `Installed`. Navigate  the list to locate the plugin name `On-the-Fly Shortest Path`. Activate it by clicking on the checkbox on the side of the plugin name.

Next, activate the plugin panel.
1. Select `View -> Panels`. You should see the `On-the-Fly Shortest Path` in the list of panels. Activate it by clicking on the checkbox. You should now see the panel, or just the name of the plugin in the lower left side of the left panel. In the later case, adjust the size of the plugin panel by dragging the top border of the panel upwards using the mouse.


## <a name="configuration"></a>Configuration

The plugin offers several user-defined options that can be set via the configuration dialog. To activate this dialog, press the `Configure...` button in the plugin panel. A new dialog form opens, containing parameters grouped in sections. Note: If the plugin panel does not appear, follow the instructions in the __[Activation](#activation)__ section.

The new settings will be stored locally. The user may reset the settings to the factory defaults by pressing on the `Defaults` button.


### Section: Display

The `Rubberband` is the visual element displaying the path from the start point to the end point. You can select the desired color/opacity and size of the Rubberband. 

The `Markers` are the visual elements showing the start, middle and stop points of the shortest path analysis. You can select the desired color/opacity and size of the Markers.

The `Coordinate format` may be selected from a variety of options (with or without a comma separator, xy or yx), so that they can be easily copied and pasted to other applications that require a specific format.


### Section: Network Analysis

`Use ellipsoid of the following CRS`: Distance measurements are taken based on the ellipsoid associated with the selected CRS. This feature allows viewing the map and coordinates on one CRS and take measurements on another. The following options are provided:

`Project CRS`: The CRS of the project, as appears on the bottom right side of the QGIS status bar and can be modified for 'on-the-fly' CRS transformations is used for measurements.

`Layer CRS`: When one single line layer is selected, the CRS of this line layer is used. __When multiple layers are selected, this option is ignored. The Project CRS is used instead.

`Custom CRS`: A custom CRS can be selected. For users who do not work mainly on a global scale and operate several projects in an area covered by one ellipsoid, it is advised to use this option. Measurements using the ellipsoid and local datum of the custom CRS provide more accurate length results within the extents of e.g. a country. 

After selecting the CRS, information labels regarding the ellipsoid associated with the selected CRS, as well as the units of the CRS are updated.

`Topology tolerance`: Set the topology tolerance to account for topological discontinuities of the line network. Using topology tolerance 0 requires the line network to have topological continuity. Please note that the crossing from a line segment to the other occurs between vertices of both lines. The topology tolerance value signifies the minimum distance between vertices of two lines that the algorithm will consider as eligible to cross. Please note that the algorithm of the QGIS Network Analysis Library presents a peculiarity that the crossing of the gap between the two lines will not take place between the nearest vertices but from the previous (or the next) vertex. Also note that the units of this setting should conform to the `CRS units` indication above. __WARNING: If the CRS units is in degrees, please note that there will be a significant difference between the measured distance of a gap between lines against the value set in the topology tolerance. It is advised to use a CRS having an invariable map unit, such as meters. Normally, the CRS of the local area or country will be the most suitable. It is advised not to use WGS84 for that purpose.__

`Tolerance units`: Set the distance units associated with the `Topology tolerance` setting.

`Result units`: Set the type of distance units to present the result. Note: All measurements are made internally in meters. A simple conversion factor is applied.   

`Decimal digits`: Set the number of decimal points for the displayed Length

`Show result in`: You can select from the following options:

   `Panel, Length and loss`: The results of the analysis will appear in the plugin panel. The result will contain the total length, including the entry length, length on the path along the line network and the exit length.
   
   `Panel, Length only`: For users who are not interested in fiber calculations, these data can be hidden.
   
   `Window, length and loss`: The results will appear both in the plugin panel as well as in a window that will appear on screen. This new window will contain the details of entry, on line network and exit. Only length information is shown.  

   `Window, length only`: The results will appear both in the plugin panel as well as in a window. Only length data are presented. The fiber calculations both in the panel and the result window are hidden.   

`Include entry/exit points`: When checked, the path is drawn from the start point to the nearest point on the line, along the line and finally to the exit point. When unchecked, only the path along the line is drawn. 

`Add result layer`: When checked, the result of the analysis will create a new temporary layer. This layer contains as fields all results of the analysis.

`Add merged layer`: When checked and provided that more than one layers have been selected for the analysis, the merged layer will appear as a temporary layer. __WARNING: For efficient memory usage, please use this feature only when absolutely necessary, e.g. for debugging of a routing analysis. It is advised to reset it, after debugging is complete. __ 
    
### Section: Fiber Loss Budget

`Connector loss`: Set the average loss of the fiber optic connectors in use. Unit:`db`.

`Connectors at entry`: Set the number of connectors expected at the start point of the analysis. As an example, this can include the connector at the Optical Line Terminal (OLT), the connectors at the Optical Distribution Frames (ODF) etc.

`Connectors at exit`: Set the number of connectors expected at the end point of the analysis. As an example, this can include the connectors at the customer premises, such as the customer-side ODF and the customer Optical Network Terminal (ONT).

`Splice loss`: Set the average loss at every optical splice made on the fiber cable. Unit:`db`.

`Splice every`: Set the frequency of splices of the fiber optic network. Usually, a design parameter of a fiber optic network sets a splice every so many kilometers.

`Fiber attenuation`: Set the average attenuation of the fiber optic cables used in the network. Unit:`db`.

`Fixed`: This is a fixed value that is added to the loss calculations. It accounts for loss created by certain components, such as optical splitters in an FTTH network. Please note that this value is allocated only to the on-graph cost and not to the entry or exit cost.


# <a name="usage"></a>Usage

__NOTE: The text below refers to the names of buttons as per their functionality. Since plugin version 1.2.0, the text of the buttons has been replaced by icons. The icons are self-explainable. Alternatively, you may hover over a button with the mouse . A tooltip will appear and present the action to be taken when the button is pressed.__  
 
1. Load the layer(-s) containing the line network where the analysis of the shortest path will be made, using the normal QGIS procedures for loading projects or individual layers.

2. From the plugin panel, select the desired layers for the analysis in the `Layers` selector. Please note that only the layers having a line geometry will appear. The CRS of the layers will appear enclosed in brackets. If a line layer is not associated with a CRS, analysis will not be able to take place. Multiple layers may be selected. See __[Handling of multiple layers](#handling-of-multiple-layers)__ for additional information.

3. Press the `Start` button. The button will appear as pressed and the cursor will change to a cross. Navigate on the map and click on the Start point of your choice. 

4. Press the `End` button. The button will appear as pressed and the cursor will change to a cross (if it is not already a cross). Navigate on the map and click on the End point of your choice. 

5. Press the `Calculate/Measure` button. The content of the Length box will change to `Processing...` and the algorithm will start running. After the algorithm ends, the results will appear. In case a path is not found, a message will appear for a few seconds on the QGIS message bar.

In cases where the user would like to force the routing of the algorithm to pass from a selected point, the `Middle` point functionality can be used. In such case, the algorithm will calculate the shortest path from the Start point to the Middle point(s) and finally to the End point. The calculations are totally independent, therefore the path from any point to the next may partially coincide with the previous path. The user must select the location of the points in a way that the calculations will provide a usable resulting path. These middle points could be considered as the "Stop points" or "Rest points", i.e. go from start to stop, making stops along the way. To avoid terminology conflicts with the end point of the path and the exit point of the line layer, I avoided the "stop" term and used the term "middle", although not precisely correct!

At any time the user may press any of the `Start`, `Middle1`, `Middle2`, `Middle3` and `End` buttons and set each of them on map. First, the user click the button. The shape of the button becomes more round, to show that selections on map has been made and a pair of coordinates are now associated with this marker. If the user decides to set another point on map, the coordinates of the clicked point will be associated to this marker, provided that the button is still pressed. After the user clicks on the map, the border of the buttons becomes darker, to show that a selection has been made and the coordinates have been stored to this marker point. 

The `MiddleX` buttons, where X=1,2,3, are also equipped with the additional functionality of re-setting the associated marker if pressed after the point has already been set.

The algorithm considers a strict sequence __Start -> Middle1 -> Middle2 -> Middle3 -> End__. If any of the middle markers is not set, it is simply ignored. For example, if only Middle3 marker has been set, the sequence will be Start -> Middle3 -> End. This allows to set and/or clear middle markers depending on the particular use case, without requiring to modify middle markers that have been previously set. Always keep in mind that when middle markers are set, the algorithm does not really care about finding the shortest path from start to end, but rather finding the shortest path from start to the first set middle marker, then to the next middle marker etc. and finally to the end point.

In case the user wishes to present the coordinates of the assigned buttons, the `eye` button presents the `Marker coordinates` window with the required information. The user may see and even copy the coordinates of each marker. The coordinate format can be set in the configuration dialog. The coordinate values appear depending on the project CRS, exactly as they are shown in the Coordinate box of the QGIS status bar. The window can be opened and be placed on screen continuously, without interfering with the rest of the operations. The coordinates of all markers are updated in real-time, both in value as well as the coordinate format set by the Configuration dialog.

In Fiber Loss measurements, you can decide if you would like to add the `Fixed Loss` amount of the Configuration dialog to the measurement. Check the `Add Fixed loss amount` if you want to add the amount to the result. Uncheck if you would like to have the measurement without the Fixed loss amount.

Press the `Reset` button to hide all visual elements (markers and rubberbands) and clear the existing values for all points.

If you would like to store the results of an analysis to a new layer, you can press the `Add as layer` button. A new temporary layer will be created. The fields of this layer contain the coordinates of all markers, along with the result data of the analysis. The format of the coordinates (x y, y x, etc.)  will be the one set in the Configuration dialog. The result length units and the format of the length will also appear as set in the Configuration dialog. Please note that the coordinate format will follow the current setting of the Configuration dialog, yet the measurement format and units will be those of the measurement that is currently active.

You can press the `Configure` button to enter the Configuration dialog. For detailed explanation of the configuration parameters, visit the [Configuration](#configuration) section.

You can press the `Help` button to present the content of the online help page.

   
## Length measurements

The `Entry` length and loss is associated with the distance from the start point to the nearest point of the line layer, the __entry point__. This entry point is calculated by the core QGIS network analysis library.

The `Exit` length and loss is associated with the distance from the end point to the nearest point of the line layer, the __exit point__. This exit point is calculated by the core QGIS network analysis library.

The `On path` length and loss is associated with the path over the selected line layer, from the entry point to the exit point of the line layer, excluding the pieces of length from the start and end point to the line layer. The core QGIS network analysis library Dijkstra algorithm is used to calculate the shortest path.

The measurements of the lines from the start point/exit point to the graph and the distance of the path on graph are being made as per the active CRS of the QGIS project. The QGIS 'on the fly' transformation feature can be used to take measurements with different CRS. The Results window presents the CRS and ellipsoid which have been used for the measurement.

NOTE: When the `Include entry/exit points` of the configuration dialog is checked, the total length from entry point, along the line and to the exit point appears in the panel. When unchecked, only the length along the line network appears in the panel. The Results window continues to show all lengths. 


## Fiber Loss Budget measurements

The loss for the entry/exit path is calculated as the sum of:

1. The number of connectors at the entry/exit point multiplied by the loss of each connector

2. The splice loss multiplied by the distance from the start point to the entry point on the line layer

3. The fiber attenuation multiplied by the distance from the start point to the entry point on the line layer
  
The loss along the line layer is calculated as the sum of:

1. The splice loss multiplied by the distance from the entry point to the exit point on the line layer

2. The splice loss multiplied by the distance from the start point to the entry point on the line layer

3. The Fixed cost, only if the checkbox `+Fixed` of the plugin panel is checked

NOTE: When the `Include entry/exit points` of the configuration dialog is checked, the total loss from entry point, along the line and to the exit point appears in the panel. When unchecked, only the loss along the line appears in the panel. This includes only the splice loss along the line network and the Fixed loss. 


## <a name="handling-of-multiple-layers"></a> Handling of multiple layers

The plugin allows the selection of multiple layers to perform the shortest path analysis. This feature can be helpful in cases where a path is not fully contained in one layer. As an example, there may be one layer for a primary road network, another layer for the secondary road network, a third one for the tertiary road network and so on. To calculate a path from an arbitrary point to another, the user would normally have to merge all those layers and then run the shortest-path algorithm on the merged layer. The multiple layer selection of the plugin performs the layer merging automatically. 

The topology tolerance functionality can also be used in order to cross topologically disconnected lines from one layer to the other. The tolerance refers to vertices of lines and not to the lines themselves. Therefore, if two lines are crossing each other, the rubberband will not jump from one line to the other. Yet, if there are vertices in each line within the topology tolerance, the rubberband will jump from one vertex to the other. This functionality may be desired in some cases, such as a secondary road passing over or under a primary road, where it is not possible to drive from one road to the other. 

__The user should know that the ease of use comes with a cost. Some precautions also need to be taken:__

1. The merging of layers consumes heavily system resources (memory and CPU). In addition, calculations of the plugin are performed in Python, which is not as fast and efficient as the core QGIS language C++. Please select the minimum number of layers required for your work.

2. When multiple layers are selected, the configuration option to use an ellipsoid based on `Layer CRS` will not work. Since several layers are concerned and each layer may have its own CRS, the plugin selects to override ths option and to use the Project CRS. This is performed in the background and the configuration option of the Configuration dialog does not present this fact, because the user may decide later to select one single layer. In that case, the `Layer CRS` option will be used, without the user having to re-visit the Configuration dialog.

3. When two or more layers are selected, the plugin will be dealing with one single merged layer, consisting of all lines of the initial layers. The user should keep in mind that those layers may have not been created with the consideration that somebody will merge them. Therefore, lines of originally separate layers may cross without a connection, coincide geometrically, run in parallel at a very short distance and other situations that may visually confuse the users, if they do not have a clear view of the vertices of each line. Therefore, the result of finding a path between all those lines should be taken with a grain of salt. Especially when the Topology tolerance feature is activated, the results may be surprising. Users are advised to use layers with a strict topological association between the features of those layers. As an example, a point layer containing the common points between the line layers can help identify the points of transition from one layer to the other. A value of topology tolerance equal to zero, or the minimum possible to cope for snapping inconsistencies, is desirable in that case. 

4. User must be careful with coordinate transformations from one CRS to another, in regards to the topological association between vertices of different layers. For example, if the vertex of layer 1 has been snapped topologically to a vertex of layer 2, if layer 1 is saved to a different CRS, the same vertex of the layer 1 in the new CRS may not be topologically connected to the vertex of CRS 2. Use the topology tolerance to overcome such situations. A few millimeters will suffice.