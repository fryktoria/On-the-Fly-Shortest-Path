# On-the-Fly Shortest Path plugin


## Introduction
The "On-the-Fly Shortest Path" QGIS plugin offers an interactive measurement of distances along a line network, operating directly on the map. It calculates Distance and the Fiber Loss Budget in fiber optic networks (backbone or FTTH). 

The plugin uses the core Network Analysis library of QGIS in order to calculate the shortest path via the Dijkstra algorithm. 

Subsequently, it calculates the Fiber Loss Budget of this path, considering several configured parameters (connector loss, splice loss, fiber attenuation, splitters etc.). 

In contrast to similar algorithms of the Processing toolbox, this plugin does not create a new layer for every measurement but rather presents the path and the calculated parameters directly on screen. This functionality is similar to the original RoadGraph plugin of QGIS2. 

Additionaly, it allows the setting of an optional middle point, forcing the path to go through it. This is helpful in networks with multiple paths between the start and stop point. 


## Installation

### Install from the official QGIS plugin repository
Pending approval.

### Install from the author's repository

1. From the QGIS toolbar, select `Plugins -> Manage and Install Plugins...`.

2. The window `Plugins|Settings` will open. From the panel on the left side of the window, select `Settings`.

3. Add a new repository by clicking the `Add...` button. The form `Repository details` will open. Complete the parameters: 
- `Name` Set to `fryktoria.com`
- `URL`  Set to  `www.fryktoria.com/qgis_plugin_repository`
- `Authentication` Leave empty
- `Enabled` Make sure that it is checked

The new repository will appear on the list and if the repository server has processed the request properly, the status of the repository will show as **connected**.

4. From the panel on the left side of the `Plugins|Settings` window, select `All`. Navigate to the list to locate the plugin name `On-the-Fly Shortest Path` and press `Install Plugin` or `Install Experimental Plugin`. 

5. On the list, of the `Plugins|Settings` window, make sure that the checkbox on the side of the plugin name is checked. This will activate the plugin.


### Install from a zip file

1. Download the zip file containing the plugin to a directory of your choice.

2. From the QGIS toolbar, select `Plugins -> Manage and Install Plugins...`. 

3. From the panel on the left side of the new form, select `Install from ZIP`. Select the file downloaded in step 1.

After installation is complete, you should be able to see the plugin name in the list of installed plugins. 

Also, to confirm that installation was made properly, from the QGIS toolbar, select `View -> Panels`. You should see the `On-the-Fly Shortest Path` in the list of panels. Activate it by clicking on the checkbox. 


## Activation

The plugin panel should be visible on the left hand side of the QGIS screen. If you do not see it, firt make sure that the plugin is activated.

1. From the QGIS toolbar, select `Plugins -> Manage and Install Plugins...`.

2. The window `Plugins|Settings` will open. From the panel on the left side of the window, select `Installed`.  Navigate  the list to locate the plugin name `On-the-Fly Shortest Path`. Activate it by clicking on the checkbox on the side of the plugin name.

Next, activate the plugin panel.
1. Select `View -> Panels`. You should see the `On-the-Fly Shortest Path` in the list of panels. Activate it by clicking on the checkbox. You should now see the panel, or just the name of the plugin in the lower left side of the left panel. In the later case, adjust the size of the plugin panel by dragging the top border of the panel upwards using the mouse.


## Configuration

The plugin offers several user-defined options that can be set via the configuration dialog. To activate this dialog, press the `Configure...` button in the plugin panel. A new dialog form opens, containg parameters grouped in sections. Note: If the plugin panel does not appear, follow the instructions in the **[Activation](#Activation)** section.

The new settings will be stored locally. The user may reset the settings to the factory defaults by pressing on the `Defaults` button.


### Section: Display

The `Rubberband` is the visual element displaying the path from the start point to the end point. You can select the desired color/opacity and size of the Rubberband. 

The `Markers` are the visual elements showing the start, middle and stop points of the shortest path analysis. You can select the desired color/opacity and size of the Markers.


### Section: Network Analysis

`Decimal digits`: Set the number of decimal points for the displayed Length

`Topology tolerance`: Set the topology tolerance to account for topological discontinuities of the line network. ** NOTE: This feature does not operate as expected, if the value is higher than 0. This is attributed to the underlying QGIS core network analysis functions and not to the plugin. Using topology tolerance 0 requires the line network to have topological continuity.**

`Show cost as`: You can select from the following options:
   `Summary`: The results of the analysis will appear in the plugin panel. The result will contain the total cost, including the entry cost, cost on graph and the exit cost.
    `Detailed window`: The results will appear both in the plugin panel as well as in a window that will appear on screen. This new window will contain the details of entry, on graph and exit.
    
    
### Section: Fiber Loss Budget

`Connector loss`: Set the average loss of the fiber optic connectors in use. Unit:`db`.

`Connectors at entry`: Set the number of connectors expected at the start point of the analysis. As an example, this can include the connector at the Optical Line Terminal (OLT), the connectors at the Optical Distribution Frames (ODF) etc.

`Connectors at exit`: Set the number of connectors expected at the end point of the analysis. As an example, this can include the connectors at the customer premises, such as the customer-side ODF and the customer Optical Network Terminal (ONT).

`Splice loss`: Set the average loss at every optical splice made on the fiber cable. Unit:`db`.

`Splice every`: Set the frequency of splices of the fiber optic network. Usully, a design parameter of a fiber optic network sets a splice every so many kilometers.

`Fiber attenuation`: Set the average attenuation of the fiber optic cables used in the network. Unit:`db`.

`Fixed`: This is a fixed value that is added to the loss calculations. It accounts for loss created by certain components, such as optical splitters in an FTTH network. Please note that this value is allocated only to the on-graph cost and not to the entry or exit cost.


# Usage
 
1. Load the layer(-s) containing the line network where the analysis of the shortest path will be mase using the normal QGIS procedures.
2. From the plugin panel, select the desired layer for the analysis in the `Layer` selector. Please note that only the layers having a line geometry will appear. The CRS of the layers will appear enclosed in brackets. If a line layer is not associated with a CRS, analysis will not be able to take place.
3. Press the `Start` button. The button will appear as pressed and the cursor will change to a cross. Navigate on the map and click on the Start point of your choice. 
4. Press the `End` button. The button will appear as pressed and the cursor will change to a cross (if it is not already a cross). Navigate on the map and click on the End point of your choice. 
5. Press the `Calculate...` button. The content of the Length box will change to `Processing...` and the algorithm will start running. After the algorithm ends, the results will appear. In case a path is not found, a message will appear for a few seconds on the QGIS message bar.

In cases where the user would like to force the routing of the algorithm to pass from a selected point, the `Middle` point functionality can be used. In such case, the algorithm will calculate the shortest path from the Start point to the Middle point and then, from the Middle point to the End point. The two calculations are totally independent, therefore the second path may partially coincide with the first path. The user must select the location of the points in a way that the two calculations will provide a usable resulting path.

At any time the user may press any of the `Start`, `Middle` and `End` buttons and set each of them on map. The selection remains active and a new location for the point may be set.

Press the `Reset` button to hide all visual elements and clear the existing settings for the points.

   
## Length measurements

The `Entry cost` is associated with the distance from the start point to the nearest point of the line layer, the entry point. This entry point is calculated by the core QGIS network analysis library.

The `Exit cost` is associated with the distance from the end point to the nearest point of the line layer, the exit point. This exit point is calculated by the core QGIS network analysis library.

The `Cost on graph` is associated with the path over the selected line layer, from the entry point to the exit point. The core QGIS network analysis library Dijkstra algorithm is used to calculate the shortest path.

The measurements of the lines from the start point/exit point to the graph and the distance of the path on graph are being made with different algorithms. There is a possibility that the results produce different length units. This case is identified and an error message is displayed in the Results window.

## Fiber Loss Budget measurements

The loss for the entry/exit path is calculated as the sum of:
1. The number of connectors at the entry/exit point multiplied by the loss of each connector
2. The splice loss multiplied by the distance from the start point to the entry point on the line layer
3. The fiber attenuation multiplied by the distance from the start point to the entry point on the line layer
  
The loss along the line layer is calculated as the sum of:
1. The splice loss multiplied by the distance from the entry point to the exit point on the line layer
2. The splice loss multiplied by the distance from the start point to the entry point on the line layer
3. The Fixed cost, only if the checkbox `+Fixed` of the plugin panel is checked


## Build from Github sources

Follow these instructions if you want to create manually a zip file to install into QGIS using the process described in the **[Install from a zip file](#Install%20from%20a%20zip%20file)**  section.

1. Download all files from Github
2. Create a directory named `On-the-Fly-Shortest-Path` and move all files to this directory
3. Use your favorite compression tools to create a zip file **which contains the directory** and not the individual files. This structure is mandatory so that the set of files is understood by QGIS as a plugin.
4. Install the plugin using the procedure in **[Installation](#Installation)** section.