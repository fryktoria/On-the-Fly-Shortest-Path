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

__author__ = 'Ilias Iliopoulos'
__date__ = 'March 2024'
__copyright__ = '(C) 2024, Ilias Iliopoulos'


import os
from qgis.PyQt import uic
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QPushButton
from qgis.PyQt.QtCore import Qt
from qgis.core import (QgsProject,
                       QgsVectorLayer,
                       QgsPointXY,
                       QgsSettings,
                       QgsWkbTypes,
                       Qgis,
                       QgsDistanceArea,
                       QgsUnitTypes,
                       QgsCoordinateReferenceSystem,                       
                       QgsFeatureRequest,
                       QgsCoordinateTransform                       
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
        "rubberBandColorRed" : 55,
        "rubberBandColorGreen" : 165,
        "rubberBandColorBlue" : 200,
        "rubberBandOpacity" : 128,        
        "rubberBandSize" : 8,
        "markerColorRed" : 255,
        "markerColorGreen" : 30,
        "markerColorBlue" : 50,
        "markerOpacity" : 255,       
        "markerSize" : 10,
        "decimalDigits" : 2,
        "topologyTolerance" : 0.0,
        "toleranceUnitsIndex" : 0,
        "includeStartStop" : 1,
        "resultDialogTypeIndex" : 0, 
        "distanceUnitsIndex" : 0, # ["meters", "Kilometers", "yards", "feet", "nutical miles", "imperial miles"]
        "selectedCrsMethod" : 0, # 0 Project, 1 Layer, 2 Custom
        "customCrs" : 0, # EPSG id
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

        # Load the configuration form
        self.configurationDlg = uic.loadUi(os.path.join(os.path.dirname(__file__), "./", "DlgConfiguration.ui"))
      
        # Load the results form
        self.resultsDlg = uic.loadUi(os.path.join(os.path.dirname(__file__), "./", "DlgResults.ui"))
        self.resultsDlg.modal = True

        # Load the results form without the fiber data
        self.resultsDlgNoFiber = uic.loadUi(os.path.join(os.path.dirname(__file__), "./", "DlgResultsNoFiber.ui"))
        self.resultsDlgNoFiber.modal = True

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
        self.resultTypes = ["Panel", "Length", "Length and Loss"]

        # A dictionary to store configuration parameters
        self.currentConfig = {}
             
        # A list to store markers
        # We currently use 3 (start, stop and middle) but we may
        # add more middle markers in the future
        self.markers = []
        
        # A list to store rubberbands
        self.rubberBands=[]
        
        # A dictionary to store the analysis points.
        '''
        I use a dictionary and use the keys as ordinal values to recognize
        the start, stop and mid points. Contrary to the markers list,
        the structure is as follows {0:startpoint, 1:middlepoint1, 3:middlepoint3, ... , n:endpoint}
        The point with the highest key number is the end point. There may be gaps between middle points, 
        e.g. when a middle point does not exist or it is deleted. Currently, I will use the forms
        {0:startpoint,  2:endpoint} and
        {0:startpoint, 1:middlepoint1, 2:endpoint}        
        I expect that this structure is fixed to be applied in future developments with several middle points.
        Perhaps I should modify the marker structure to operate in a similar manner
        '''
        self.pointsDict={}
       
        # A dictionary to pass data to the results dialog
        self.resultsDict = {
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
        
        # A list to hold the option items of the configuration dialog for distance units
        self.distanceUnits = ["meters", "Kilometers", "yards", "feet", "nautical miles", "miles"]
        # A list to hold the result units. Has the same order as the above list
        self.resultUnitsList = ["m", "Km", "y", "ft", "NM", "mi"]
        self.conversionFactor = [1, 0.001, 1.0936132983377078, 3.280839895013123, 0.0005399568034557236, 0.0006213711922373339] 

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
        self.dockDlg.middle_coordinates_button.pressed.connect(self.on_dockDlg_middle_coordinates_button_pressed)
        
        self.dockDlg.end_coordinates_button.clicked.connect(self.on_dockDlg_end_coordinates_button_clicked)
        self.dockDlg.calculate_button.clicked.connect(self.on_dockDlg_calculate_button_clicked)  
        self.dockDlg.reset_button.clicked.connect(self.on_dockDlg_reset_button_clicked)
        self.dockDlg.configure_button.clicked.connect(self.on_dockDlg_configure_button_clicked)  
        self.dockDlg.layer_combobox.activated.connect(self.on_dockDlg_layer_selected)
        
        self.resultsDlg.OkButton.clicked.connect(self.on_resultsDlg_results_ok)
        self.resultsDlgNoFiber.OkButton.clicked.connect(self.on_resultsDlgNoFiber_results_ok)
        
        # The configuration dialog does not have two independent buttons but a "buttonBox" with two visual buttons
        # where the entire buttonBox widget activates the accepted (click OK) and rejejeted (click cancel) events
        self.configurationDlg.buttonBox.accepted.connect(self.on_configurationDlg_config_complete_ok)
        self.configurationDlg.buttonBox.rejected.connect(self.on_configurationDlg_config_complete_cancel)
        self.configurationDlg.defaultsButton.clicked.connect(self.on_configurationDlg_config_reset_defaults)
        
        self.configurationDlg.selectProjectCrs.toggled.connect(self.on_configurationDlg_selectCrsChange)
        self.configurationDlg.selectLayerCrs.toggled.connect(self.on_configurationDlg_selectCrsChange)
        self.configurationDlg.selectCustomCrs.toggled.connect(self.on_configurationDlg_selectCrsChange)
        self.configurationDlg.mQgsProjectionSelectionWidget.crsChanged.connect(self.on_configurationDlg_customCrsChange)
        
        # Identify when a new layer is added, removed, re-named to the project in order to re-populate the layers
        QgsProject.instance().layersAdded.connect(self.populateLayerSelector)
        QgsProject.instance().layersRemoved.connect(self.populateLayerSelector)
        QgsProject.instance().layerTreeRoot().nameChanged.connect(self.populateLayerSelector)
        
        # Identify when the project CRS changes
        QgsProject.instance().crsChanged.connect(self.on_project_crsChanged)
        #QgsProject.instance().ellipsoidChanged.connect(self.on_project_crsChanged)
               
        # Identify the condition where another toolset is activated, so that we must unpress all buttons of the dock dialog
        self.canvas.mapToolSet.connect(self.on_toolset_change)
        
        # We create marker 0 and 1 for start and stop points,
        # as well as 2 for the middle point. Total of 3.
        # Additional middle points may be added in the future
        self.createMarkers(3)
        # Change the default icon only for the start and stop markers 
        self.markers[0].setIconType(QgsVertexMarker.ICON_TRIANGLE)
        self.markers[1].setIconType(QgsVertexMarker.ICON_INVERTED_TRIANGLE)             
        # Hide all markers. We will show each one when needed
        self.hideMarkers()  
        
        # Remember the current project CRS so that we can convert coordinates if the project CRS is changed
        self.projectCrs = QgsProject().instance().crs()
        
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
        currentRubberBandColor = QColor(
                                        int(dict["rubberBandColorRed"]), 
                                        int(dict["rubberBandColorGreen"]), 
                                        int(dict["rubberBandColorBlue"]),
                                        int(dict["rubberBandOpacity"])
                                        )    
        dlg.rubberBandColor.setColor(currentRubberBandColor)
        dlg.rubberBandSize.setValue(dict["rubberBandSize"])
        
        currentMarkerColor = QColor(
                                    int(dict["markerColorRed"]), 
                                    int(dict["markerColorGreen"]), 
                                    int(dict["markerColorBlue"]),
                                    int(dict["markerOpacity"])
                                    )
        dlg.markerColor.setColor(currentMarkerColor)
        dlg.markerSize.setValue(dict["markerSize"])
        dlg.decimalDigits.setValue(dict["decimalDigits"])
        dlg.topologyTolerance.setValue(dict["topologyTolerance"])
        if dict["includeStartStop"] == 1:
            dlg.includeStartStop.setChecked(True)
        else:
            dlg.includeStartStop.setChecked(False)       

        dlg.distanceUnits.clear()
        for index, optionTxt in enumerate(self.distanceUnits):       
            dlg.distanceUnits.addItem(optionTxt)
            if dict["distanceUnitsIndex"] == index:
                dlg.distanceUnits.setCurrentIndex(index)

        dlg.resultDialogType.clear()
        for index, optionTxt in enumerate(self.resultTypes):       
            dlg.resultDialogType.addItem(optionTxt)
            if dict["resultDialogTypeIndex"] == index:
                dlg.resultDialogType.setCurrentIndex(index)  

        self.temporaryCrsMethod = dict["selectedCrsMethod"]
        self.setConfigurationSelectCrs(dict["selectedCrsMethod"])  
        dlg.mQgsProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(dict["customCrs"]))  
        
        crs = self.activeCrs()
        crsData = self.crsDetails(crs)
        dlg.measurementEllipsoid.setText(crsData[0]) 
        dlg.crsUnits.setText(self.crsDistanceUnits(crs))
        
        dlg.toleranceUnits.clear()
        for index, optionTxt in enumerate(self.distanceUnits):       
            dlg.toleranceUnits.addItem(optionTxt)
            if dict["toleranceUnitsIndex"] == index:
                dlg.toleranceUnits.setCurrentIndex(index)
        
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
        if dlg.includeStartStop.isChecked():
            conf["includeStartStop"] = 1
        else: 
            conf["includeStartStop"] = 0

        for index, optionTxt in enumerate(self.distanceUnits):          
            if dlg.distanceUnits.currentIndex() == index:       
                conf["distanceUnitsIndex"] = index

        for index, optionTxt in enumerate(self.distanceUnits):          
            if dlg.toleranceUnits.currentIndex() == index:       
                conf["toleranceUnitsIndex"] = index
        
        for index, optionTxt in enumerate(self.resultTypes):          
            if dlg.resultDialogType.currentIndex() == index:       
                conf["resultDialogTypeIndex"] = index
        
        # "selectedCrsMethod" is set by the event handler
        conf["selectedCrsMethod"] = self.temporaryCrsMethod
        
        try:
            # I did not find a method to return the EPSG is as ineteger. I remove the first 5 characters "EPSG:" 
            epsgId = int(dlg.mQgsProjectionSelectionWidget.crs().authid()[5:])
        except:
            #epsgId = -1
            #If Invalid layer, set to EPSG:4326 WGS 84
            epsgId=4326              
        conf["customCrs"] = epsgId
                       
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
                self.pointsDict[0] = self.startPoint

            if self.middle_button_pressed == True:
                self.dockDlg.middle_coordinates_textbox.setText(str(x) + " " + str(y))
                self.middlePoint = QgsPointXY(point)
                m[2].setCenter(self.middlePoint)   
                m[2].show()
                self.pointsDict[1] = self.middlePoint

            if self.end_button_pressed == True:
                self.dockDlg.end_coordinates_textbox.setText(str(x) + " " + str(y))                
                self.endPoint = QgsPointXY(point)
                m[1].setCenter(self.endPoint)
                m[1].show()
                self.pointsDict[2] = self.endPoint
                
        except AttributeError:
            #print("No attribute")
            self.iface.messageBar().pushMessage("Error", "Exception: No attribute", level=Qgis.Critical)
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


    def on_toolset_change(self):
        #print ("Toolset changed")
        self.uncheckAllButtons()
        return
        

    def on_dockDlg_layer_selected(self):
        if self.dockDlg.layer_combobox.currentIndex != -1:
            self.previousLayerId = self.layerList[self.dockDlg.layer_combobox.currentIndex()][1]  
        #print ("index:", self.dockDlg.layer_combobox.currentIndex(), "text:",self.dockDlg.layer_combobox.currentText())
        return        
    
    
    def coordButtonClicked(self, button:QPushButton) -> None:
        ''' Generic action routine when any of the start, stop, middle buttons is clicked '''
        # Activate the map tool. It must be run before the button is shown as pressed
        # so that the change tool event fires after.
        self.canvas.setMapTool(self.pointTool)        
        self.uncheckAllButtons()           
        button.setChecked(True)
        return
      
    def on_dockDlg_start_coordinates_button_clicked(self) -> None:
        self.coordButtonClicked(self.dockDlg.start_coordinates_button)
        self.start_button_pressed = True
        self.active_button = "Start coords"
        return
        

    def on_dockDlg_middle_coordinates_button_pressed(self) -> None:
        ''' Especially for middle button, if pressed while it is already checked,
        it resets the value. This is useful when we want to reset the middle point
        while leaving the start and stop points as they are'''
        if self.dockDlg.middle_coordinates_button.isChecked():       
            self.dockDlg.middle_coordinates_textbox.setText("")
            self.markers[2].hide()
            # Remove middle point
            if 1 in self.pointsDict:
                self.pointsDict.pop(1)
        return
    
           
    def on_dockDlg_middle_coordinates_button_clicked(self) -> None:
        self.coordButtonClicked(self.dockDlg.middle_coordinates_button)
        self.middle_button_pressed = True
        self.active_button = "Middle coords"       
        return

                
    def on_dockDlg_end_coordinates_button_clicked(self) -> None: 
        self.coordButtonClicked(self.dockDlg.end_coordinates_button)
        self.end_button_pressed = True
        self.active_button = "End coords"         
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
        
        self.pointsDict.clear()
       
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
        self.dockDlg.fiberLoss.setText("...")
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
        self.updateRubberBandVisuals()
        return


    def on_configurationDlg_config_complete_cancel(self) -> None:
        #print("Configuration canceled")
        self.configurationDlg.hide()
        return


    def on_configurationDlg_config_reset_defaults(self) -> None:
        self.populateConfigurationDlg(self.configurationDlg, self.factoryDefaultSettings.copy())
        return
 

    def on_configurationDlg_selectCrsChange(self) -> None:
        
        # Get the radio button that sent the signal
        rb = self.configurationDlg.sender()
        # Check if the radio button is checked
        if rb.isChecked():            
            if rb.text() == "Project CRS":
                self.temporaryCrsMethod = 0                 
            elif rb.text() == "Layer CRS":
                self.temporaryCrsMethod = 1                
            else:
                self.temporaryCrsMethod = 2
                
            self.setConfigurationSelectCrs(self.temporaryCrsMethod) 
        return            


    def on_configurationDlg_customCrsChange(self) -> None:  
        crs = self.configurationDlg.mQgsProjectionSelectionWidget.crs()
        crsData = self.crsDetails(crs)
        self.configurationDlg.measurementEllipsoid.setText(crsData[0]) 
        self.configurationDlg.crsUnits.setText(self.crsDistanceUnits(crs))
    
              
    def setConfigurationSelectCrs(self, crsMethod:int) -> None:
        
        if crsMethod == 0:
            self.configurationDlg.selectProjectCrs.setChecked(True)    
            self.configurationDlg.mQgsProjectionSelectionWidget.setEnabled(False)
            crs = QgsProject().instance().crs()
            
        elif crsMethod == 1:
                self.configurationDlg.selectLayerCrs.setChecked(True)    
                self.configurationDlg.mQgsProjectionSelectionWidget.setEnabled(False)  
                if self.getPathLayer() is None:
                    crs = None
                else:    
                    crs = self.getPathLayer().sourceCrs()
                
        elif crsMethod == 2:    
            self.configurationDlg.selectCustomCrs.setChecked(True)    
            self.configurationDlg.mQgsProjectionSelectionWidget.setEnabled(True)
            crs = self.configurationDlg.mQgsProjectionSelectionWidget.crs() 
            
        crsData = self.crsDetails(crs)
        self.configurationDlg.measurementEllipsoid.setText(crsData[0]) 
        self.configurationDlg.crsUnits.setText(self.crsDistanceUnits(crs))
            
        return    
    
    
    def on_project_crsChanged(self) -> None:
        ''' Function to run when the project CRS is changed '''
        #print ("Event CRS changed")
        #print ("Transforming from ", self.projectCrs.description(), " to ", QgsProject().instance().crs().description())  
        newCrs = QgsProject().instance().crs()        
        self.transformInputData(self.projectCrs, newCrs)
        self.projectCrs = newCrs

        # Update also the configuration dialog which is non modal and could be open
        crsData = self.crsDetails(newCrs)
        self.configurationDlg.measurementEllipsoid.setText(crsData[0]) 
        self.configurationDlg.crsUnits.setText(self.crsDistanceUnits(newCrs))
               
        return
 
 
    def on_resultsDlg_results_ok(self) -> None:
        self.resultsDlg.hide()
        return


    def on_resultsDlgNoFiber_results_ok(self) -> None:
        self.resultsDlgNoFiber.hide()
        return
        
         
    def uncheckAllButtons(self) -> None:
        dlg = self.dockDlg
        dlg.start_coordinates_button.setChecked(False)
        dlg.middle_coordinates_button.setChecked(False)
        dlg.end_coordinates_button.setChecked(False) 
        
        self.start_button_pressed = False
        self.middle_button_pressed = False  
        self.end_button_pressed = False
        
        self.active_button = ""
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
            return None
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
        

    def activeCrs(self) -> QgsCoordinateReferenceSystem:
        ''' Returns the QgsCoordinateReferenceSystem to be used for measurements 
            This can be either the Project CRS, the CRS of the line layer or a Custom CRS '''         
        
        if self.currentConfig["selectedCrsMethod"] == 0:
            crs = QgsProject().instance().crs()
        elif self.currentConfig["selectedCrsMethod"] == 1:
            if self.getPathLayer() is None:
                crs = None
            else:    
                crs = self.getPathLayer().sourceCrs()
        else:
            crs = QgsCoordinateReferenceSystem.fromEpsgId(self.currentConfig["customCrs"]) 
        return crs            
    


        
    def process(self) -> int:

        pathLayer = self.getPathLayer() 
        if pathLayer is None:
             return -1
        
        #print ("CRS of path layer: ", pathLayer.crs().authid())          
        if pathLayer.crs().authid() == "":
            self.iface.messageBar().pushMessage("Error", "Path layer does not have a valid CRS", level=Qgis.Critical, duration=5)
            return -1

        # Local variable to avoid length calculations
        measureCrs = self.activeCrs() 
        if measureCrs is None:
            self.iface.messageBar().pushMessage("Error", "Path layer is not set", level=Qgis.Critical, duration=5)
            return -1

        entryCost = 0
        costOnGraph = 0
        exitCost = 0

        # Convert dict to a list, having only the values. I make sure the order is retained,
        # so that I reference freely the i and the i+1 item
        sortedPointsDict = dict(sorted(self.pointsDict.items()))
        pointsList = list(sortedPointsDict.values())


        ''' The coordinates stored when clicking the buttons are those of the Project CRS. We like this because we want to associated
            these values with what is shown on the current map. We need to transform coordinates if necessary '''  
        trPointsList = self.transformedPointsList(pointsList, self.projectCrs, measureCrs)
           
        numPointPairs = len(trPointsList) - 1
        for i in range(0,numPointPairs): 

            if i == 0:
                ''' First rubberband, from start point to next point which can either be a middle point or the end point
                 If the second point is a middle point, calculate the point on graph nearest to the middle point (middlePointOnGraph)
                 to be used in next iteration. '''
                (rb, costs, middlePointOnGraph) = self.findRoute(measureCrs, pathLayer, trPointsList[i], trPointsList[i+1], self.currentConfig["includeStartStop"])
            else:
                # For the second rubberband, use the point on graph middlePointOnGraph calculated in the previous iteration
                (rb, costs, middlePointOnGraph) = self.findRoute(measureCrs, pathLayer, middlePointOnGraph, trPointsList[i+1], False)
            if rb is None:
                self.deleteRubberBands()
                return -1 
            self.rubberBands.insert(i, rb)    
            # First pair
            if i == 0:    
                entryCost = costs["entryCost"]
                
            # Last pair. Note: can also be the first pair if middle point is not present   
            if i == (numPointPairs - 1):    
                costOnGraph += costs["costOnGraph"]
                exitCost = costs["exitCost"]
                # Final rubberband from the graph to the end point
                if self.currentConfig["includeStartStop"]:
                    self.rubberBands[i].addPoint(self.transformPointCoordinates(trPointsList[numPointPairs], measureCrs, self.projectCrs))
              
            # Between two middle points    
            else:
                costOnGraph += costs["costOnGraph"]
       
        # Get the details of the measurements, i.e. the distance units of the CRS
        crsData = self.crsDetails(measureCrs)          
        self.resultsDict["ellipsoid"] = crsData[0] 
        self.resultsDict["crs"] = crsData[1] + "/" + crsData[2] 
        self.resultsDict["lengthUnits"] = crsData[3]

        ''' We expect that the distance units returned by crsData[3] will be meters in order to make 
            our conversions. Most CRS and associated ellipsoids' units are in meters or can be converted by QGIS from 
            feet or other unit to meters. If not, or in case a CRS is not defined for the project,
            we present a warning and return the values and units returnded by QgsDistanceArea class without conversion '''
        if self.resultsDict["lengthUnits"] == "meters":
            conversionIndex = self.currentConfig["distanceUnitsIndex"]
            # From 1.0.4, we use the converted units
            self.resultsDict["lengthUnits"] = self.resultUnitsList[self.currentConfig["distanceUnitsIndex"]]
        else:    
            conversionIndex = -1
            self.iface.messageBar().pushMessage("Warning", "Base distance unit is not meters but " + crsData[3] +". Unit conversion is disabled", level=Qgis.Warning, duration=5)
            
        self.resultsDict["entryCost"] = self.convertDistanceUnits(entryCost, conversionIndex)
        self.resultsDict["costOnGraph"] = self.convertDistanceUnits(costOnGraph, conversionIndex)
        self.resultsDict["exitCost"] = self.convertDistanceUnits(exitCost, conversionIndex)
        self.resultsDict["totalCost"] = self.convertDistanceUnits(entryCost + costOnGraph + exitCost, conversionIndex)  
     
        # Show length result in dockWidget
        if self.currentConfig["includeStartStop"]:
            self.dockDlg.resultLength.setText(self.formatLengthValue(self.resultsDict["totalCost"])) 
        else:
            self.dockDlg.resultLength.setText(self.formatLengthValue(self.resultsDict["costOnGraph"]))
        self.dockDlg.lengthUnits.setText(self.resultsDict["lengthUnits"])
        
        # Calculate fiber loss parameters and show result in dockWidget
        self.calculateFiberLoss()
        if self.currentConfig["includeStartStop"]:
            self.dockDlg.fiberLoss.setText(self.formatLossValue(self.resultsDict["fiberTotalLoss"]))
        else:
            self.dockDlg.fiberLoss.setText(self.formatLossValue(self.resultsDict["fiberLossOnGraph"]))
        self.dockDlg.fiberLossUnits.setText(self.resultsDict["fiberLossUnits"])
        
        # Show the results dialog, if configured to do so
        if self.currentConfig["resultDialogTypeIndex"] == 1:
            self.showResultDlg(self.resultsDlgNoFiber, self.resultsDict) 
        elif self.currentConfig["resultDialogTypeIndex"] == 2:            
            self.showResultDlg(self.resultsDlg, self.resultsDict)
            
        return 0


    def distanceP2P(self, crs:QgsCoordinateReferenceSystem, p1:QgsPointXY, p2:QgsPointXY) -> float:
        ''' Returns the distance between two points, in the units of the CRS '''
        d = QgsDistanceArea()
        d.setSourceCrs(crs, QgsProject().instance().transformContext())
        d.setEllipsoid(crs.ellipsoidAcronym())
        return d.measureLine([p1, p2])

    def convertDistanceUnits(self, value:float, index:int) -> float:
        ''' Converts a distance from meters to any of the allowed units, or the same value if the index is not recognized
            The index is expected to be the index in lists self.resultUnitsList[] and self.conversionFactor[]        '''
        if index < 0:
            return value
        else:
            return value * self.conversionFactor[index]
                       
                       
    def crsDetails(self, crs:QgsCoordinateReferenceSystem) -> list: # list of strings  [ellipsoid, EPSG, CRS_description, Units] 
        ''' Returns a list of valuable data regarding the measurements of the CRS '''
        '''Be protective in case a transformation is not possible '''
        try:
            d = QgsDistanceArea()
            d.setSourceCrs(crs, QgsProject().instance().transformContext())
            d.setEllipsoid(crs.ellipsoidAcronym())     
            return [d.ellipsoid(), d.sourceCrs().authid(), d.sourceCrs().description(), QgsUnitTypes.toString(d.lengthUnits())]    
        except:
            return ["?", "?", "?", "?"]
    
               
    def findRoute(self, currentCrs:QgsCoordinateReferenceSystem, pathLayer:QgsVectorLayer, fromPoint:QgsPointXY, toPoint:QgsPointXY, addStartPoint = False) -> None:
        ''' Runs dijkstra and create the rubberbands ''' 
        
        ''' An exception may occur if QGIS does not know how to make a transformation, e.g.
               No transform is available between IAU_2015:200021660 - Kleopatra (2015) - Sphere / Ocentric / Tranverse Mercator and ESRI:102082 - Korea_2000_Korea_Central_Belt_2010.
               Unknown error (code 4096)
        '''
        try:
            director = QgsVectorLayerDirector(pathLayer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)
            strategy = QgsNetworkDistanceStrategy()
            director.addStrategy(strategy)
       
            topologyTolerance = self.toleranceToMapUnits(currentCrs, self.currentConfig["toleranceUnitsIndex"], self.currentConfig["topologyTolerance"])
            builder = QgsGraphBuilder(currentCrs, True, topologyTolerance, currentCrs.ellipsoidAcronym())
            
        except:
            return(None, None, None)
        
        
        # These are the coordinates of the points on the line that are closest to the start and stop points
        tiedPoints = director.makeGraph(builder, [fromPoint, toPoint])
        tStart, tStop = tiedPoints
        #print("Tied points on the line:", tiedPoints)

        graph = builder.graph()
        idxStart = graph.findVertex(tStart)
        idxEnd = graph.findVertex(tStop)
        (tree, costs) = QgsGraphAnalyzer.dijkstra(graph, idxStart, 0)

        if tree[idxEnd] == -1:
            #print('No route!')
            self.iface.messageBar().pushMessage("Warning", "No route found", level=Qgis.Warning, duration=3)
            return(None, None, None)

        # Measure the distance from the start and stop point to the entry and exit point of the graph
        entry_cost = self.distanceP2P(currentCrs, fromPoint, tStart)      
        exit_cost = self.distanceP2P(currentCrs, tStop, toPoint)

        # set all results to a dictionary to be used by calling function
        analysis_results = {
            "entryCost": entry_cost,
            "costOnGraph": costs[idxEnd],
            "exitCost": exit_cost,
        }            

        # Add last point
        route = [graph.vertex(idxEnd).point()]

        # Iterate the graph
        while idxEnd != idxStart:
            idxEnd = graph.edge(tree[idxEnd]).fromVertex()
            route.insert(0, graph.vertex(idxEnd).point())

        rb = self.createRubberBand()


        # I need to transform to the map coordinates in order to draw
        if addStartPoint:
            rb.addPoint(self.transformPointCoordinates(fromPoint, currentCrs, self.projectCrs))     
        for p in route:
            rb.addPoint(self.transformPointCoordinates(p, currentCrs, self.projectCrs))   
            
        return (rb, analysis_results, tStop)

    
    def createRubberBand(self) -> QgsRubberBand:
        rb = QgsRubberBand(self.canvas)
        rb.setColor(QColor(
                            self.currentConfig["rubberBandColorRed"], 
                            self.currentConfig["rubberBandColorGreen"], 
                            self.currentConfig["rubberBandColorBlue"],
                            self.currentConfig["rubberBandOpacity"],
                            
                           )
                    )
        rb.setWidth(self.currentConfig["rubberBandSize"])
        return (rb)        


    def deleteRubberBands(self) -> None:
        for rb in self.rubberBands:
            self.canvas.scene().removeItem(rb)       
        self.rubberBands.clear()               
        return            


    def updateRubberBandVisuals(self) -> None:
        ''' Update the attributes of the rubberbands'''
        rubberBandColor = QColor(
                                self.currentConfig["rubberBandColorRed"], 
                                self.currentConfig["rubberBandColorGreen"], 
                                self.currentConfig["rubberBandColorBlue"],
                                self.currentConfig["rubberBandOpacity"]
                                )
        for rb in self.rubberBands:
            rb.setColor(rubberBandColor)
            rb.setWidth(self.currentConfig["rubberBandSize"]) 
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
        ''' Update the attributes of the markers'''
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

        ''' Length section '''
        dlg.entryCostTxt.setText(self.formatLengthValue(d["entryCost"]))
        dlg.costOnGraphTxt.setText(self.formatLengthValue(d["costOnGraph"]))
        dlg.exitCostTxt.setText(self.formatLengthValue(d["exitCost"]))
        dlg.totalCostTxt.setText(self.formatLengthValue(d["totalCost"]))

        dlg.entryCostUnits.setText(d["lengthUnits"])
        dlg.onGraphCostUnits.setText(d["lengthUnits"])
        dlg.exitCostUnits.setText(d["lengthUnits"])
        dlg.totalCostUnits.setText(d["lengthUnits"])
        
        ''' Fiber section '''
        if dlg != self.resultsDlgNoFiber:        
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
        
        ''' CRS and Ellipsoid section '''        
        dlg.ellipsoidTxt.setText(d["ellipsoid"])
        dlg.crsTxt.setText(d["crs"])
        
        # Keep for future use
        dlg.errorTxt.setText("")
        
        # exec() is required instead of show() to make the result window modal. 
        # The setting in Qt Designer does not work
        dlg.exec()  

        
    def transformPointCoordinates(self, point:QgsPointXY, sourceCRS:str, targetCrs:str) -> QgsPointXY:
        ''' Transforms the coordinates of a point object from a source CRS to a target CRS. CRS to be input as "EPSG:xxxx" '''   

        if sourceCRS == targetCrs:
            return  point
        
        '''
        try:        
            tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(sourceCRS), QgsCoordinateReferenceSystem(targetCrs), QgsProject.instance())
        except:
            self.iface.messageBar().pushMessage("Error", "Exception: Not valid transformation. Returns same point coordinates", level=Qgis.Critical)
        
        if tr.isValid():
            try:
                transformedPoint = tr.transform(point)
                print ("Point ", point, " To ", transformedPoint)                                
                return transformedPoint
            except:
                self.iface.messageBar().pushMessage("Error", "Exception: transform() failed", level=Qgis.Critical)
                return point                
        else:
            print ("Not valid transformation. Returns same point coordinates")
            self.iface.messageBar().pushMessage("Error", "Not valid transformation. Returns same point coordinates", level=Qgis.Critical)
            return point            
        '''
        tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(sourceCRS), QgsCoordinateReferenceSystem(targetCrs), QgsProject.instance())
        transformedPoint = tr.transform(point)                               
        return transformedPoint
        
        
    def transformedPointsList(self, points, fromCrs:QgsCoordinateReferenceSystem, toCrs:QgsCoordinateReferenceSystem) -> None:
        trPoint = []
        for i, point in enumerate(points):
            trPoint.append(self.transformPointCoordinates(points[i], fromCrs.authid(), toCrs.authid())) 
        return trPoint


    def transformInputData(self, fromCrs:QgsCoordinateReferenceSystem, toCrs:QgsCoordinateReferenceSystem) -> None:

        for key, point in self.pointsDict.items():  
            #originalPoint = self.pointsDict[key]
            trPoint = self.transformPointCoordinates(point, fromCrs.authid(), toCrs.authid())            
            self.pointsDict[key] = trPoint
            self.markers[self.pointIndexToMarkerIndex(key)].setCenter(trPoint) 
            if key == 0:
                self.dockDlg.start_coordinates_textbox.setText(str(trPoint.x()) + " " + str(trPoint.y()))
                self.startPoint = QgsPointXY(trPoint) 
            elif key == 1:
                self.dockDlg.middle_coordinates_textbox.setText(str(trPoint.x()) + " " + str(trPoint.y()))
                self.middlePoint = QgsPointXY(trPoint) 
            elif key == 2:
                self.dockDlg.end_coordinates_textbox.setText(str(trPoint.x()) + " " + str(trPoint.y()))
                self.endPoint = QgsPointXY(trPoint)    
        
        return


    ''' Need to be modified if multiple markers '''
    def pointIndexToMarkerIndex(self, pointIndex:int) -> int:
        if pointIndex == 0:
           return 0
        elif pointIndex == 2:
            return 1
        else:
            return 2

    def crsDistanceUnits(self, crs:QgsCoordinateReferenceSystem) -> str:
        ''' Returns the distance units of a CRS, in human readable format '''
        if crs is None:
            return "Undefined"
        else:
            return QgsUnitTypes.toString(crs.mapUnits())         


    def toleranceToMapUnits(self, crs:QgsCoordinateReferenceSystem, toleranceUnitsIndex:int, topologyTolerance:float) -> float:
        ''' Converts the tolerance value from the units set in the configuration dialog to the map units of the CRS'''
        configuredUnitIndex = toleranceUnitsIndex
        toleranceUnits = self.distanceUnits[configuredUnitIndex]
        unit = QgsUnitTypes.stringToDistanceUnit(toleranceUnits)[0]
        toleranceMapUnits = QgsUnitTypes.fromUnitToUnitFactor(unit, crs.mapUnits()) * topologyTolerance
        return toleranceMapUnits
