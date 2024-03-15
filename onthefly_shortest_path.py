# -*- coding: utf-8 -*-
"""
***************************************************************************
    __init__.py
    ---------------------
    
    Date                 : March 2024
    Copyright            : (C) 2024 by Ilias Iliopoulos
    Email                : info at fryktoria dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 3 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************

 Original shortest path code from the Network analysis library section of 
 the PyQGIS Cookbook,  subject to the associated license
 https://docs.qgis.org/3.34/en/docs/pyqgis_developer_cookbook/network_analysis.html


"""

import os
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog, QMessageBox
from qgis.PyQt.QtCore import Qt
from qgis.core import (QgsProject,
                       QgsVectorLayer,
                       QgsPointXY,
                       QgsSettings,
                       QgsWkbTypes,
                       Qgis,
                       QgsDistanceArea,
                       QgsUnitTypes,  
                       QgsFeatureRequest                       
                       )
from qgis.gui import (QgsMapToolEmitPoint, 
                      QgsDockWidget, 
                      QgsVertexMarker, 
                      QgsLayoutDesignerInterface,
                      QgsRubberBand,
                      )
from qgis.analysis import *

# Test to clone layer using processing algorithms
#import processing



class OnTheFlyShortestPath:

    factoryDefaultSettings = {
        "rubberBandColorRed" : 0,
        "rubberBandColorGreen" : 0,
        "rubberBandColorBlue" : 50,
        "rubberBandSize" : 2,
        "rubberBandOpacity" : 255,
        "markerColorRed" : 255,
        "markerColorGreen" : 30,
        "markerColorBlue" : 50,
        "markerOpacity" : 255,       
        "markerSize" : 10,
        "decimalDigits" : 2,
        "topologyTolerance" : 0.0,
        "resultDialogTypeIndex" : 0, 
        "connectorLoss" : 0.4, # db per connector
        "numberOfConnectorsAtEntry" : 3,
        "numberOfConnectorsAtExit" : 2,
        "spliceLoss" : 0.15, # db per splice
        "spliceFrequency" : 1.0, # Km
        "cableLoss" : 0.25,       # db/Km    
        "fixedLoss" : 0  # db e.g. Acccount for splitters 1:2->4db, 1:4->7db, 1:8->11db, 1:16->15db, 1:32->19db, 1:64->23db
    }

    def __init__(self, iface):
        # pluginName used as prefix in storing and reading configuration settings
        self.pluginName = "OtFShortestPath"
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # Initialize the plugin path directory
        self.plugin_dir = os.path.dirname(__file__)

        # Set up the Panel using the docked widget
        self.dockDlg = uic.loadUi(os.path.join(os.path.dirname(__file__), "./", "DlgDockWidget.ui"))   
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockDlg)
        
        # Load the results form
        self.resultsDlg = uic.loadUi(os.path.join(os.path.dirname(__file__), "./", "DlgResults.ui"))
        self.resultsDlg.modal = True

        # Load the configuration form
        self.configurationDlg = uic.loadUi(os.path.join(os.path.dirname(__file__), "./", "DlgConfiguration.ui"))

        # set up the tool to click on screen and get the coordinates
        self.pointTool = QgsMapToolEmitPoint(self.canvas)
        self.pointTool.canvasClicked.connect(self.display_point)
        
        # Variables to know which button was last pressed
        self.start_button_pressed = False
        self.middle_button_pressed = False
        self.end_button_pressed = False
        self.active_button = ""

        # A list to hold the option items in the resultDialogType combobox of the 
        # configuration dialog
        self.resultTypes = ["Summary", "Detailed window"]

        # A dictionary to store configuration parameters
        self.currentConfig = {}
             
        # A list to store markers
        # We currently use 3 (start, stop and middle) but we may
        # add more middle markers in the future
        self.markers = []
       
        # A dictionary to pass data to the results dialog
        self.resultsDict = {
            "costUnits" : "m",
            "entryCost" : 0,
            "costOnGraph" : 0,
            "exitCost" : 0,
            "totalCost" : 0,
            "ellipsoid" : "",
            "crs" : "",
            "lengthUnits" : "m",
            "fiberLossEntry" : 0,
            "fiberLossOnGraph" : 0,
            "fiberLossExit" : 0,
            "fiberTotalLoss" : 0,
            "fiberLossUnits" : "db"      
        }
        
        # A list to store the tuples (layer name and layer unique id) for all valid line layers
        self.layerList = []
        self.previousLayerId = ""
        
        # Set the decimal digits for the presentation of fiber loss in the results window
        # Fiber loss precision is fixed and not associated to the length decimal digits.
        # I do not think that needs a configuration parameter
        self.fiber_loss_precision = 2

        # Read the stored settings from the QgsSettings mechanism 
        # In Windows could be C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\QGIS\QGIS3.ini      
        self.readQgsSettings()
        return


    def initGui(self):
    
        # Hide the unit labels on the dock widget. I do not want to set them to null 
        # in Qt designer because I want everything to be visible to the developer
        self.dockDlg.lengthUnits.setText("")
        self.dockDlg.fiberLossUnits.setText("")
        
        # Set the function to run on the press of each button of the form
        # self.dockDlg.BUTTON_NAME.clicked.connect(self.METHOD_NAME)
        self.dockDlg.start_coordinates_button.clicked.connect(self.on_dockDlg_start_coordinates_button_clicked)
        self.dockDlg.middle_coordinates_button.clicked.connect(self.on_dockDlg_middle_coordinates_button_clicked)
        self.dockDlg.end_coordinates_button.clicked.connect(self.on_dockDlg_end_coordinates_button_clicked)
        self.dockDlg.calculate_button.clicked.connect(self.on_dockDlg_calculate_button_clicked)  
        self.dockDlg.reset_button.clicked.connect(self.on_dockDlg_reset_button_clicked)
        self.dockDlg.configure_button.clicked.connect(self.on_dockDlg_configure_button_clicked)  
        self.dockDlg.layer_combobox.activated.connect(self.on_dockDlg_layer_selected)
        
        self.resultsDlg.OkButton.clicked.connect(self.on_resultsDlg_results_ok)
        
        # The configuration dialog does not have two independent buttons but a "buttonBox" with two visual buttons
        # where the entire buttonBox widget activates the accepted (click OK) and rejejeted (click cancel) events
        self.configurationDlg.buttonBox.accepted.connect(self.on_configurationDlg_config_complete_ok)
        self.configurationDlg.buttonBox.rejected.connect(self.on_configurationDlg_config_complete_cancel)
        self.configurationDlg.defaultsButton.clicked.connect(self.on_configurationDlg_config_reset_defaults)
        
        # Identify when a new layer is added, removed, re-named to the project in order to re-populate the layers
        QgsProject.instance().layersAdded.connect(self.populateLayerSelector)
        QgsProject.instance().layersRemoved.connect(self.populateLayerSelector)
        QgsProject.instance().layerTreeRoot().nameChanged.connect(self.populateLayerSelector)
        
        # We create marker 0 and 1 for start and stop points,
        # as well as 2 for the middle point. Total of 3.
        # Additional middle points may be added in the future
        self.createMarkers(3)
        # Change the default icon only for the start and stop markers 
        self.markers[0].setIconType(QgsVertexMarker.ICON_TRIANGLE)
        self.markers[1].setIconType(QgsVertexMarker.ICON_INVERTED_TRIANGLE)             
        # Hide all markers. We will show each one when needed
        self.hideMarkers()  
        
        return
        

    def unload(self):
        ''' Clean up resources '''
        self.canvas.unsetMapTool(self.pointTool)
        return

 
    def readQgsSettings(self) -> None:
        ''' Read from the QGIS repository and update the local dictionary of the current configuration.
            If setting is not found, use the existing value from the factory default settings  '''  
        p = self.pluginName + "/"
        s = QgsSettings()
        conf = self.currentConfig
        factory = self.factoryDefaultSettings       
        # I need to cast the values to int or float.        
        floats = ["topologyTolerance", "connectorLoss", "spliceLoss", "spliceFrequency", "cableLoss", "fixedLoss"]        
        for key in self.factoryDefaultSettings.keys(): 
            if key in floats:        
                conf[key] = float(s.value(p + key, factory[key]))
            else:
                conf[key] = int(s.value(p + key, factory[key]))
        return

         
    def storeQgsSettings(self) -> None:
        ''' Stores the current configuration in the QGIS repository '''
        p = self.pluginName + "/"
        conf = self.currentConfig
        s = QgsSettings()
        
        for key in self.currentConfig.keys(): 
            s.setValue(p + key, conf[key])
        return

        
    def populateConfigurationDlg(self, dlg:QDialog, dict:dict) -> None:
        dlg.rubberBandColor.setColor(QColor(
                                            int(dict["rubberBandColorRed"]), 
                                            int(dict["rubberBandColorGreen"]), 
                                            int(dict["rubberBandColorBlue"]),
                                            int(dict["rubberBandOpacity"])
                                            )
                                    )
        dlg.rubberBandSize.setValue(dict["rubberBandSize"])
        dlg.markerColor.setColor(QColor(
                                        int(dict["markerColorRed"]), 
                                        int(dict["markerColorGreen"]), 
                                        int(dict["markerColorBlue"]),
                                        int(dict["markerOpacity"])
                                        )
                                )
        dlg.markerSize.setValue(dict["markerSize"])
        dlg.decimalDigits.setValue(dict["decimalDigits"])
        dlg.topologyTolerance.setValue(dict["topologyTolerance"])

        dlg.resultDialogType.clear()
        for index, optionTxt in enumerate(self.resultTypes):       
            dlg.resultDialogType.addItem(optionTxt)
            if dict["resultDialogTypeIndex"] == index:
                dlg.resultDialogType.setCurrentIndex(index)       
        dlg.connectorLoss.setValue(dict["connectorLoss"])
        dlg.numberOfConnectorsAtEntry.setValue(dict["numberOfConnectorsAtEntry"])
        dlg.numberOfConnectorsAtExit.setValue(dict["numberOfConnectorsAtExit"])
        dlg.spliceLoss.setValue(dict["spliceLoss"])
        dlg.spliceFrequency.setValue(dict["spliceFrequency"])
        dlg.cableLoss.setValue(dict["cableLoss"]) 
        dlg.fixedLoss.setValue(dict["fixedLoss"])
        return        

    
    def updateConfiguration(self, dlg:QDialog) -> None:
        conf = self.currentConfig
        
        conf["rubberBandColorRed"] = dlg.rubberBandColor.color().red()
        conf["rubberBandColorGreen"] = dlg.rubberBandColor.color().green()
        conf["rubberBandColorBlue"] = dlg.rubberBandColor.color().blue() 
        conf["rubberBandOpacity"] = dlg.rubberBandColor.color().alpha()
        conf["rubberBandSize"] = dlg.rubberBandSize.value()       
        conf["markerColorRed"] = dlg.markerColor.color().red()
        conf["markerColorGreen"] = dlg.markerColor.color().green()
        conf["markerColorBlue"] = dlg.markerColor.color().blue()
        conf["markerOpacity"] = dlg.markerColor.color().alpha()
        conf["markerSize"] = dlg.markerSize.value()
        conf["decimalDigits"] = dlg.decimalDigits.value()
        conf["topologyTolerance"] = dlg.topologyTolerance.value()
        for index, optionTxt in enumerate(self.resultTypes):          
            if dlg.resultDialogType.currentIndex() == index:       
                conf["resultDialogTypeIndex"] = index
        conf["connectorLoss"] = dlg.connectorLoss.value()
        conf["numberOfConnectorsAtEntry"] = dlg.numberOfConnectorsAtEntry.value()
        conf["numberOfConnectorsAtExit"] = dlg.numberOfConnectorsAtExit.value()
        conf["spliceLoss"] = dlg.spliceLoss.value()
        conf["spliceFrequency"] = dlg.spliceFrequency.value()
        conf["cableLoss"] = dlg.cableLoss.value() 
        conf["fixedLoss"] = dlg.fixedLoss.value() 
        # Store to QGIS settings repository
        self.storeQgsSettings()
        return        
        

    def display_point(self, point:QgsPointXY, button) -> None:   
        m = self.markers    
        try:
            x, y = point.x(), point.y()
            #print("Active button:", self.active_button, f" Clicked at X: {x}, Y: {y}")
            if self.start_button_pressed == True:
                self.dockDlg.start_coordinates_textbox.setText(str(x) + " " + str(y))
                # Explicit casting to QgsPointXY required to run on Linux
                self.startPoint = QgsPointXY(point)
                m[0].setCenter(self.startPoint)
                m[0].show()
            if self.middle_button_pressed == True:
                self.dockDlg.middle_coordinates_textbox.setText(str(x) + " " + str(y))
                self.middlePoint = QgsPointXY(point)
                m[2].setCenter(self.middlePoint)   
                m[2].show()                
            if self.end_button_pressed == True:
                self.dockDlg.end_coordinates_textbox.setText(str(x) + " " + str(y))                
                self.endPoint = QgsPointXY(point)
                m[1].setCenter(self.endPoint)
                m[1].show()
                
        except AttributeError:
            #print("No attribute")
            iface.messageBar().pushMessage("Error", "Exception: No attribute", level=Qgis.Critical)
        return


    def populateLayerSelector(self) -> None:
        self.dockDlg.layer_combobox.clear()
        # Get all map layers in the project
        layers = QgsProject.instance().mapLayers()
        # Iterate over layers and identify open line layers
        # Create a list containing (layer name, unique layer id, layer crs) from which 
        # I will populate the combo box and be able to work with the index and the unique id,
        # having the name only for presentation purposes 
        self.layerList.clear()
        index = 0        
        for layer_id, layer in layers.items():
            #Select only Vector line layers
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.LineGeometry:
                tuple = (layer.name(), layer_id)
                self.layerList.append(tuple)
                presentationName = layer.name() + ' [' + layer.crs().authid() + ']'
                # Index numbering in Qt combobox starts also at 0. Empty is -1
                self.dockDlg.layer_combobox.insertItem(index, presentationName)
                # Regardless of changes in the layers (add, remove, rename), if the unique layer id
                # still remains in the list, I want it to remain selected
                if layer_id == self.previousLayerId:
                    self.dockDlg.layer_combobox.setCurrentIndex(index)
                index += 1
                #print(f"Layer Name: {layer.name()} Layer geometryType: {layer.geometryType()}")
        return      


    def on_dockDlg_layer_selected(self):
        if self.dockDlg.layer_combobox.currentIndex != -1:
            self.previousLayerId = self.layerList[self.dockDlg.layer_combobox.currentIndex()][1]  
        #print ("index:", self.dockDlg.layer_combobox.currentIndex(), "text:",self.dockDlg.layer_combobox.currentText())
        return        
    
      
    def on_dockDlg_start_coordinates_button_clicked(self) -> None:
        #Show the last button pressed
        self.uncheckAllButtons()
        self.start_button_pressed = True
        self.dockDlg.start_coordinates_button.setChecked(True)
        self.active_button = "Start coords"
        # Activate the map tool
        self.canvas.setMapTool(self.pointTool)
        return
        
        
    def on_dockDlg_middle_coordinates_button_clicked(self) -> None:
        self.uncheckAllButtons()
        self.middle_button_pressed = True
        self.dockDlg.middle_coordinates_button.setChecked(True)   
        self.active_button = "Middle coords"
        self.canvas.setMapTool(self.pointTool)
        return

                
    def on_dockDlg_end_coordinates_button_clicked(self) -> None:                   
        self.uncheckAllButtons()
        self.end_button_pressed = True
        self.dockDlg.end_coordinates_button.setChecked(True)
        self.active_button = "End coords"
        self.canvas.setMapTool(self.pointTool)
        return

        
    def on_dockDlg_reset_button_clicked(self) -> None:
        # De-activate the map tool
        #print("Reset button")
        self.deleteRubberBands()
        self.canvas.unsetMapTool(self.pointTool) 
        self.active_button = ""           
        self.dockDlg.start_coordinates_textbox.setText("")
        self.dockDlg.middle_coordinates_textbox.setText("")
        self.dockDlg.end_coordinates_textbox.setText("")
        self.dockDlg.resultLength.setText("")
        self.dockDlg.lengthUnits.setText("")
        self.dockDlg.fiberLoss.setText("")
        self.dockDlg.fiberLossUnits.setText("")
        
        self.uncheckAllButtons()
        self.hideMarkers()
       
        self.populateLayerSelector()
        return
                

    def on_dockDlg_calculate_button_clicked(self) -> None:
       
        self.deleteRubberBands()
        #print("Starting calculation") 
        if self.dockDlg.layer_combobox.currentIndex() == -1:
            #print ("Invalid layer")
            self.iface.messageBar().pushMessage("Error", "Invalid layer", level=Qgis.Critical, duration=5)
            return
            
        if  self.dockDlg.start_coordinates_textbox.text() == "":
            #print ("Invalid start coordinates")
            self.iface.messageBar().pushMessage("Error", "Invalid start coordinates", level=Qgis.Warning, duration=5)
            return

        if  self.dockDlg.end_coordinates_textbox.text() == "":
            #print ("Invalid end coordinates")
            self.iface.messageBar().pushMessage("Error", "Invalid end coordinates", level=Qgis.Warning, duration=5)
            return
                          
        # Show busy                 
        self.dockDlg.resultLength.setText("Processing...")
        self.dockDlg.fiberLoss.setText("Processing...")
        # Necessary to update GUI before processing takes over
        self.dockDlg.repaint()
        
        #Start the algorithm. On any error, results will not be completed
        # On success, the dock widgets will be filled by the process
        if self.process() < 0:
            self.dockDlg.resultLength.setText("......")
            self.dockDlg.fiberLoss.setText("......")        
        
        return


    def on_dockDlg_configure_button_clicked(self) -> None:
        self.populateConfigurationDlg(self.configurationDlg, self.currentConfig)
        self.configurationDlg.show()
        return


    def on_configurationDlg_config_complete_ok(self) -> None:
        #print("New configuration accepted")
        # Re-set the dictionary with the dialog values
        self.updateConfiguration(self.configurationDlg)
        # and update the appearance of markers
        self.updateMarkerVisuals()
        return


    def on_configurationDlg_config_complete_cancel(self) -> None:
        #print("Configuration canceled")
        self.configurationDlg.hide()
        return


    def on_configurationDlg_config_reset_defaults(self) -> None:
        self.populateConfigurationDlg(self.configurationDlg, self.factoryDefaultSettings.copy())
        return
 
 
    def on_resultsDlg_results_ok(self) -> None:
        self.resultsDlg.hide()
        return

         
    def uncheckAllButtons(self) -> None:
        dlg = self.dockDlg
        dlg.start_coordinates_button.setChecked(False)
        dlg.middle_coordinates_button.setChecked(False)
        dlg.end_coordinates_button.setChecked(False) 
        
        self.start_button_pressed = False
        self.middle_button_pressed = False  
        self.end_button_pressed = False
        return
 

    def getPathLayer(self) -> QgsVectorLayer: 
        ''' Returns a memory clone of the line layer, over which the shortest path will be searched.
        This copy contains all features of the original layer, having only the geometry but not the attributes.
        This is to make the copy more light for the system. Yet, we cannot make use of any attributes for the analysis.
        If in the future we add some functionality requiring the analysis of attributes, we can add only the selected 
        attributes into the clone.
        '''       
        cmbBoxIndex = self.dockDlg.layer_combobox.currentIndex()
        if cmbBoxIndex < 0:
            return
        layerId = self.layerList[cmbBoxIndex][1]
        my_layer = QgsProject.instance().mapLayer(layerId)        
        #print ("Using path layer ", self.layerList[cmbBoxIndex][1])
        my_layer.selectAll()
        # all features
        #mem_layer = my_layer.materialize(QgsFeatureRequest().setFilterFids(my_layer.allFeatureIds()))
        # all features, no attributes. Documentation says "To disable fetching attributes, reset the FetchAttributes flag (which is set by default)"
        # which is misleading because there is no FetchAttributes flag. Yet, I tried the SubsetOfAttributes flag as below and it worked
        mem_layer = my_layer.materialize(QgsFeatureRequest().setFlags(QgsFeatureRequest.SubsetOfAttributes  ))
        my_layer.removeSelection()        
        # I do not want the layer on map, just in memory. I used it in order to make sure that the memory layer does 
        # not carry the attributes of the original layer
        # QgsProject.instance().addMapLayer(mem_layer)       
        
        return mem_layer
        
        
    def process(self) -> int:
    
        vectorLayer = self.getPathLayer() 
        
        #print ("CRS of path layer: ", vectorLayer.crs().authid())       
        if vectorLayer.crs().authid() == "":
            self.iface.messageBar().pushMessage("Error", "Path layer does not have a valid CRS", level=Qgis.Critical, duration=5)
            return -1

        # When middle coordinates is not set, I will use start and end points
        if  self.dockDlg.middle_coordinates_textbox.text() == "":        
            (self.rb1, costs1, middlePointOnGraph) = self.findRoute(vectorLayer, self.startPoint, self.endPoint)
            if self.rb1 is None:           
                return -1
            self.rb1.addPoint(self.endPoint)
            
            self.resultsDict["entryCost"] = costs1["entryCost"]
            self.resultsDict["costOnGraph"] = costs1["costOnGraph"]
            self.resultsDict["exitCost"] = costs1["exitCost"]
            self.resultsDict["totalCost"] =  self.resultsDict["entryCost"] +  self.resultsDict["costOnGraph"] +  self.resultsDict["exitCost"]
            self.resultsDict["ellipsoid"] = costs1["ellipsoid"]
            self.resultsDict["crs"] = costs1["crs"]
            self.resultsDict["lengthUnits"] = costs1["lengthUnits"]

        else:
            #print ("Going through middle point")
            (self.rb1, costs1, middlePointOnGraph) = self.findRoute(vectorLayer, self.startPoint, self.middlePoint)
            if self.rb1 is None:
                return -1          
            (self.rb2, costs2, finalPointOnGraph) = self.findRoute(vectorLayer, middlePointOnGraph, self.endPoint) 
            if self.rb2 is None:
                self.canvas.scene().removeItem(self.rb1)              
                return -1
            self.rb2.addPoint(self.endPoint)
 
            self.resultsDict["entryCost"] = costs1["entryCost"]
            self.resultsDict["costOnGraph"] = costs1["costOnGraph"] + costs2["costOnGraph"]
            self.resultsDict["exitCost"] = costs2["exitCost"]
            self.resultsDict["totalCost"] =  self.resultsDict["entryCost"] +  self.resultsDict["costOnGraph"] +  self.resultsDict["exitCost"]
            self.resultsDict["ellipsoid"] = costs1["ellipsoid"]
            self.resultsDict["crs"] = costs1["crs"]
            self.resultsDict["lengthUnits"] = costs1["lengthUnits"]

        # Show length result in dockWidget
        self.dockDlg.resultLength.setText(self.formatLengthValue(self.resultsDict["totalCost"])) 
        self.dockDlg.lengthUnits.setText(self.resultsDict["lengthUnits"])
        
        # Calculate fiber loss parameters and show result in dockWidget
        self.calculateFiberLoss()
        self.dockDlg.fiberLoss.setText(self.formatLossValue(self.resultsDict["fiberTotalLoss"]))
        self.dockDlg.fiberLossUnits.setText(self.resultsDict["fiberLossUnits"])
        
        # Show the results dialog, if configured to do so
        if self.currentConfig["resultDialogTypeIndex"] != 0:
            self.showResultDlg(self.resultsDlg, self.resultsDict)

        return 0

            
    def findRoute(self, vectorLayer:QgsVectorLayer, fromPoint:QgsPointXY, toPoint:QgsPointXY) -> None:
        director = QgsVectorLayerDirector(vectorLayer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)
        strategy = QgsNetworkDistanceStrategy()
        director.addStrategy(strategy)

        # I can use either the project crs or the line layer crs for the graph
        # and for the measurements between the points and the tied points, below
        #sourceCrs = QgsProject().instance().crs()
        sourceCrs = vectorLayer.sourceCrs()
        
        builder = QgsGraphBuilder(sourceCrs, True, self.currentConfig["topologyTolerance"], sourceCrs.ellipsoidAcronym())
        # These are the coordinates of the points on the line that are closest to the start and stop points
        tiedPoints = director.makeGraph(builder, [fromPoint, toPoint])
        tStart, tStop = tiedPoints
        #print("Tied points on the line:", tiedPoints)

        d = QgsDistanceArea()
        d.setSourceCrs(sourceCrs, QgsProject().instance().transformContext())
        d.setEllipsoid(sourceCrs.ellipsoidAcronym())
        entry_cost = d.measureLine(fromPoint, tStart)
        exit_cost = d.measureLine(tStop, toPoint)

        graph = builder.graph()
        idxStart = graph.findVertex(tStart)
        idxEnd = graph.findVertex(tStop)
        (tree, costs) = QgsGraphAnalyzer.dijkstra(graph, idxStart, 0)

        if tree[idxEnd] == -1:
            #print('No route!')
            #QMessageBox.information(None, "Costs", "No route")
            self.iface.messageBar().pushMessage("Warning", "No route found", level=Qgis.Warning, duration=3)
            return(None, None, None)

        # set all results to a dictionary to be used by calling function
        analysis_results = {
            "entryCost": entry_cost,
            "costOnGraph": costs[idxEnd],
            "exitCost": exit_cost,
            "ellipsoid": d.ellipsoid(),
            "crs" : d.sourceCrs().description(), 
            "lengthUnits" : QgsUnitTypes.toString(d.lengthUnits())      
        }            

        # Add last point
        route = [graph.vertex(idxEnd).point()]

        # Iterate the graph
        while idxEnd != idxStart:
            idxEnd = graph.edge(tree[idxEnd]).fromVertex()
            route.insert(0, graph.vertex(idxEnd).point())

        rb = self.createRubberBand()

        # This may require coordinate transformation if project's CRS
        # is different than layer's CRS
        rb.addPoint(fromPoint)
        for p in route:
            rb.addPoint(p)  
            
        return (rb, analysis_results, tStop)

    
    def createRubberBand(self) -> QgsRubberBand:
        rb = QgsRubberBand(self.canvas)
        rb.setColor(QColor(
                            self.currentConfig["rubberBandColorRed"], 
                            self.currentConfig["rubberBandColorGreen"], 
                            self.currentConfig["rubberBandColorBlue"],
                            self.currentConfig["rubberBandOpacity"],
                            
                           ))
        rb.setWidth(self.currentConfig["rubberBandSize"])
        return (rb)        


    def deleteRubberBands(self) -> None:
        '''Delete existing rubberbands if they exist'''
        try:
            self.canvas.scene().removeItem(self.rb1)
        except:
            pass
        try:    
            self.canvas.scene().removeItem(self.rb2) 
        except:
            pass 
        return            


    def createMarkers(self, numMarkers:list) -> None:
        '''  Ceates markers with the default settings. The iconType of start 
        and end markers will be changed manually '''    
    
        for i in range(numMarkers):
            self.markers.insert(i, QgsVertexMarker(self.canvas))        
            self.markers[i].setIconType(QgsVertexMarker.ICON_CROSS) # or ICON_CROSS, ICON_X
            markerColor = QColor(
                                int(self.currentConfig["markerColorRed"]), 
                                int(self.currentConfig["markerColorGreen"]), 
                                int(self.currentConfig["markerColorBlue"]),
                                int(self.currentConfig["markerOpacity"])
                                )
            self.markers[i].setColor(markerColor)
            self.markers[i].setFillColor(markerColor)
            self.markers[i].setIconSize(self.currentConfig["markerSize"])  
        return            

        
    def hideMarkers(self) -> None:
        for m in self.markers:
          m.hide()  
        return          

        
    def updateMarkerVisuals(self) -> None:
        ''' Update the attributes of existing objects, i.e. the markers'''
        markerColor = QColor(
                              int(self.currentConfig["markerColorRed"]), 
                              int(self.currentConfig["markerColorGreen"]), 
                              int(self.currentConfig["markerColorBlue"]),
                              int(self.currentConfig["markerOpacity"])
                            )      
        for m in self.markers:
            m.setColor(markerColor)
            m.setFillColor(markerColor)
            m.setIconSize(self.currentConfig["markerSize"])           
        return
 

    def spliceLoss(self, length:float) -> float:
        ''' Returns the splice loss of a length of fiber cable (in meters), given the configuration data '''      
        spliceLoss = length / 1000.0 / self.currentConfig["spliceFrequency"] * self.currentConfig["spliceLoss"] if self.currentConfig["spliceFrequency"] != 0 else 0
        return spliceLoss
        
    
    def formatLengthValue(self, length:float) -> str:
        ''' Rounds and formats a length value to the defined number of decimal digits ''' 
        decimalDigits = self.currentConfig["decimalDigits"]
        floatFormat = "%." + str(decimalDigits) + "f"
        return str(floatFormat%round(length, decimalDigits))
        
    
    def formatLossValue(self, loss:float) -> str:
        ''' Rounds and formats a fiber loss value to the defined number of decimal digits '''
        decimalDigits = self.fiber_loss_precision
        floatFormat = "%." + str(decimalDigits) + "f"
        return str(floatFormat%round(loss, decimalDigits))
        
    
    def calculateFiberLoss(self) -> None:
        ''' Runs after the results dictionary has been populated with the proper lengths.
            Adjustment is made with the division of length by 1000.0 because the cinfiguration parameters are in db/Km   '''
        d = self.resultsDict
        
        conectorLossAtEntry = (self.currentConfig["connectorLoss"] * self.currentConfig["numberOfConnectorsAtEntry"])
        conectorLossAtExit = (self.currentConfig["connectorLoss"] * self.currentConfig["numberOfConnectorsAtExit"])
             
        d["fiberLossEntry"] = conectorLossAtEntry \
                              + self.spliceLoss(d["entryCost"]) \
                              + d["entryCost"] /1000.0 * self.currentConfig["cableLoss"] 
        
        d["fiberLossExit"] = conectorLossAtExit \
                             + self.spliceLoss(d["exitCost"]) \
                             + d["exitCost"] /1000.0 * self.currentConfig["cableLoss"] 
                                                        
        d["fiberLossOnGraph"] =  d["totalCost"] / 1000.0 * self.currentConfig["cableLoss"] \
                                 + self.spliceLoss(d["totalCost"]) 
        
        if self.dockDlg.addFixedLoss.isChecked():
            d["fiberLossOnGraph"]  += self.currentConfig["fixedLoss"]
               
        d["fiberTotalLoss"] = d["fiberLossEntry"] + d["fiberLossOnGraph"] + d["fiberLossExit"]
        
        ''' Although the fiberLossUnits is set in the initial configuration and it is not foreseen to be changed,
            this is the place to set it properly, potentially depending on the calculations above '''        
        d["fiberLossUnits"] = "db"        
        return
    
    
    def showResultDlg(self, dlg:QDialog, d:dict) -> None:
        ''' Present the results dialog. This is a modal window. All operations are suspended until this window closes '''

        dlg.entryCostTxt.setText(self.formatLengthValue(d["entryCost"]))
        dlg.costOnGraphTxt.setText(self.formatLengthValue(d["costOnGraph"]))
        dlg.exitCostTxt.setText(self.formatLengthValue(d["exitCost"]))
        dlg.totalCostTxt.setText(self.formatLengthValue(d["totalCost"]))

        dlg.entryCostUnits.setText(d["costUnits"])
        dlg.onGraphCostUnits.setText(d["costUnits"])
        dlg.exitCostUnits.setText(d["costUnits"])
        dlg.totalCostUnits.setText(d["costUnits"])
        
        # Fiber loss precision is fixed and not associated to the length decimal digits.
        # I do not think that needs a configuration parameter

        dlg.lossEntryTxt.setText(self.formatLossValue(d["fiberLossEntry"]))
        dlg.lossOnGraphTxt.setText(self.formatLossValue(d["fiberLossOnGraph"]))
        dlg.lossExitTxt.setText(self.formatLossValue(d["fiberLossExit"]))
        dlg.lossTotalTxt.setText(self.formatLossValue(d["fiberTotalLoss"]))
             
        dlg.fiberLossUnitsEntry.setText(d["fiberLossUnits"])
        dlg.fiberLossUnitsOnGraph.setText(d["fiberLossUnits"])
        dlg.fiberLossUnitsExit.setText(d["fiberLossUnits"])
        dlg.fiberLossUnitsTotal.setText(d["fiberLossUnits"])
                        
        dlg.ellipsoidTxt.setText(d["ellipsoid"])
        dlg.crsTxt.setText(d["crs"])
               
        # Handle the peculiar case where the measurements of the start and end points return a distance unit other than meters  
        if d["lengthUnits"] != 'meters':
            dlg.errorTxt.setText("ERROR:Units")
            self.iface.messageBar().pushMessage("Error", 
                                                "Distance units are in " + d["lengthUnits"], 
                                                level=Qgis.Critical, 
                                                duration=5)
            dlg.entryCostUnits.setText("")
            dlg.onGraphCostUnits.setText("")
            dlg.exitCostUnits.setText("")
            dlg.totalCostUnits.setText("")
        else:
            dlg.errorTxt.setText("")
                
        # exec() is required instead of show() to make the result window modal. 
        # The setting in Qt Designer does not work
        dlg.exec()  
         
                        

