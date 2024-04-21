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
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.core import ( Qgis,
                        QgsCoordinateReferenceSystem,
                        QgsCoordinateTransform,
                        QgsDistanceArea,
                        QgsFeature,
                        QgsFeatureRequest,
                        QgsField,
                        QgsFields,
                        QgsGeometry,
                        QgsMemoryProviderUtils,
                        QgsPointXY,
                        QgsProject,
                        QgsSettings,
                        QgsUnitTypes,
                        QgsVectorLayer, 
                        QgsWkbTypes
                       )
from qgis.gui import (  QgsDockWidget,
                        QgsHelp,
                        QgsLayoutDesignerInterface,
                        QgsMapToolEmitPoint, 
                        QgsRubberBand, 
                        QgsVertexMarker  
                      )
from qgis.analysis import *

from .vertexTool import *
from .geometry import OtFSP_Geometry
import webbrowser # For local and online help

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
        "numberOfConnectorsAtExit" : 3,
        "spliceLoss" : 0.15, # db per splice
        "spliceFrequency" : 1.0, # Km
        "cableLoss" : 0.25,       # db/Km    
        "fixedLoss" : 0,  # db e.g. Acccount for splitters 1:2->4db, 1:4->7db, 1:8->11db, 1:16->15db, 1:32->19db, 1:64->23db
        "coordinateFormatIndex" : 0, # ["x y", "y x", "x, y", "y, x"]
        "addResultLayer" : 0, # add the result rubberband path to map as a temporary layer
        "addMergedLayer": 0, # add the merged layer to map as a temporary layer
        "markerSnapMethod" : 0, # controls the snap behaviour of the marker (snap to vertices of point and line layers or snap to edges (the entire line) of line layers)
        "markerSnapPixels" : 10, # marker snapping tolerance in pixels
        "markerSnapToMap" : 0 # Yes,No to snap to the map feature or not
    }
    
    defaultStartMarkerIcon = QgsVertexMarker.ICON_CIRCLE
    defaultEndMarkerIcon = QgsVertexMarker.ICON_BOX
    defaultMiddleMarkerIcon = QgsVertexMarker.ICON_CROSS    

    # pluginName used as prefix in storing and reading configuration settings
    pluginName = "OtFShortestPath"    

    # Set the decimal digits for the presentation of fiber loss in the results window
    # Fiber loss precision is fixed and not associated to the length decimal digits.
    # I do not think that needs a configuration parameter
    fiber_loss_precision = 2
        
    # A list to hold the option items of the configuration dialog for distance units
    distanceUnits = ["meters", "Kilometers", "yards", "feet", "nautical miles", "miles"]
    # A list to hold the result units. Has the same order as the above list
    resultUnitsList = ["m", "Km", "y", "ft", "NM", "mi"]  

    # A list of options to control the snapping of markers
    markerSnapMethods = ["None", "Vertex", "Edge"]

    # A stylesheet string to show that a start, stop, middle button has been assigned to point coordinates
    #assignedButtonStyleSheet = "QPushButton {font-weight: bold}"
    #assignedButtonStyleSheet = "QPushButton {background-color: #6c6e6f}"
    assignedButtonStyleSheet = "QPushButton {border-style: outset; border-radius: 10px; border-width: 2px; border-color: #6c6c6c;}  QPushButton:checked{ background-color: #DCDCDC; }"
    pushedButtonStyleSheet = "QPushButton { background-color: #c6c6c6; }"
    
    # A list to hold a selecton of coordinate formats to show on textboxes
    coordinateFormats = ["x y", "y x", "x, y", "y, x"]
    
    # The y offset (in pixels) of the dockDlg dialog to move the buttons up, when fiber loss does not appear
    yOffset = 30
    
    # A default name for the created temp layer
    resultLayerName = "shortestPath"
    # A default name for the created merged temp layer
    mergedLayerName = "mergedLayer"
    
    mapToolIsSet = False
    
    # HARD CODED NUMBER OF MARKERS. THIS IS NOT A USER DEFINED VARIABLE 
    # IT IS ASSOCIATED WITH DIALOG VISUAL ELEMENTS
    numMarkers = 5
    
    # The path to the html help file. It is also the source of the online page of github.fryktoria.io
    # Github Pages has been configured to render the content from /docs.
    helpPath = "//docs//index.html"
    helpWindowTitle = "Help - On-the-Fly Shortest Path"
    
    def __init__(self, iface):

        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # Initialize the plugin path directory
        self.plugin_dir = os.path.dirname(__file__)

        # Set up the Panel using the docked widget
        self.dockDlg = uic.loadUi(os.path.join(self.plugin_dir, "./", "DlgDockWidget.ui"))   
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockDlg)

        # Load the configuration form
        self.configurationDlg = uic.loadUi(os.path.join(self.plugin_dir, "./", "DlgConfiguration.ui"))
      
        # Load the results form
        self.resultsDlg = uic.loadUi(os.path.join(self.plugin_dir, "./", "DlgResults.ui"))
        self.resultsDlg.modal = True

        # Load the results form without the fiber data
        self.resultsDlgNoFiber = uic.loadUi(os.path.join(self.plugin_dir, "./", "DlgResultsNoFiber.ui"))
        self.resultsDlgNoFiber.modal = True
        
        # Load the form displaying the coordinates of the markers
        self.markerCoordinatesDlg = uic.loadUi(os.path.join(self.plugin_dir, "./", "DlgMarkerCoordinates.ui"))
        self.markerCoordinatesDlg.modal = False
       
        # Variables to know which button was last pressed
        self.startButtonPressed = False
        self.middleButtonPressed = False
        self.middle2ButtonPressed = False
        self.middle3ButtonPressed = False        
        self.endButtonPressed = False

        # A list to hold the option items in the resultDialogType combobox of the 
        # configuration dialog
        self.resultTypes = ["Length and loss", "Length only", "Window, length and loss", "Window, length only"]

        # A dictionary to store configuration parameters
        self.currentConfig = {}
             
        # A list to store markers
        # We currently use 3 (start, stop and middle) but we may
        # add more middle markers in the future -- Added 2 more in 1.2.0
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
        {0:startpoint,  4:endpoint} and
        {0:startpoint, 1:middlepoint1,.... 4:endpoint}        
        I expect that this structure is fixed to be applied in future developments with several middle points.
        Perhaps I should modify the marker structure to operate in a similar manner -> Done in 1.2.1
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
            "fiberLossUnits" : "db",  
            "entryCostMeters" : 0,  # release 1.2.1
            "costOnGraphMeters" : 0,
            "exitCostMeters" : 0,
            "totalCostMeters" : 0,            
        }
        
        # A list to store the tuples (layer name and layer unique id) for all valid loaded line layers
        self.loadedLayerList = []
        
        # A list to store the ids (in string form) of currently selected layers  
        self.selectedLayersIdList = []
        
        # Instantiate a geometry object to use in all susequent actions
        self.geom = OtFSP_Geometry()
        
        # Read the stored settings from the QgsSettings mechanism 
        # In Windows could be C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\QGIS\QGIS3.ini      
        self.readQgsSettings()
        return


    def initGui(self):
    
        # Hide the unit labels on the dock widget. I do not want to set them to null 
        # in Qt designer because I want everything to be visible to the developer
        self.dockDlg.lengthUnits.setText("")
        self.dockDlg.fiberLossUnits.setText("")

        # set up the tool to click on screen and get the coordinates
        #self.pointTool = QgsMapToolEmitPoint(self.canvas)
        self.pointTool = CustomVertexTool(self.canvas, self.iface,
                                          snapToMap = self.currentConfig["markerSnapToMap"],
                                          snapMethod = self.currentConfig["markerSnapMethod"], 
                                          tolerancePixels = self.currentConfig["markerSnapPixels"])        
        self.pointTool.canvasClicked.connect(self.display_point)
        
        # Set the function to run on the press of each button of the form
        # self.dockDlg.BUTTON_NAME.clicked.connect(self.METHOD_NAME)
        self.dockDlg.startCoordinatesButton.clicked.connect(self.on_dockDlg_start_coordinates_button_clicked)
        self.dockDlg.middleCoordinatesButton.clicked.connect(self.on_dockDlg_middle_coordinates_button_clicked)
        self.dockDlg.middleCoordinatesButton.pressed.connect(self.on_dockDlg_any_middle_coordinates_button_pressed)
        self.dockDlg.middle2CoordinatesButton.clicked.connect(self.on_dockDlg_middle2_coordinates_button_clicked)
        self.dockDlg.middle2CoordinatesButton.pressed.connect(self.on_dockDlg_any_middle_coordinates_button_pressed)
        self.dockDlg.middle3CoordinatesButton.clicked.connect(self.on_dockDlg_middle3_coordinates_button_clicked)
        self.dockDlg.middle3CoordinatesButton.pressed.connect(self.on_dockDlg_any_middle_coordinates_button_pressed)       
        self.dockDlg.endCoordinatesButton.clicked.connect(self.on_dockDlg_end_coordinates_button_clicked)
        self.dockDlg.calculateButton.clicked.connect(self.on_dockDlg_calculate_button_clicked)  
        self.dockDlg.resetButton.clicked.connect(self.on_dockDlg_reset_button_clicked)
        self.dockDlg.configureButton.clicked.connect(self.on_dockDlg_configure_button_clicked)  
        # Signal activated does not work on QgsCheckableComboBox. Used checkedItemsChanged instead
        #self.dockDlg.layerCombobox.activated.connect(self.on_dockDlg_layer_selected)
        self.dockDlg.layerCombobox.checkedItemsChanged.connect(self.on_dockDlg_layer_selected)
        self.dockDlg.eyeButton.clicked.connect(self.on_dockDlg_eye_button_clicked)
        self.dockDlg.addLayerButton.clicked.connect(self.addRubberBandsToMap)
        self.dockDlg.addFixedLoss.stateChanged.connect(self.addFixedLossChanged)
                
        # For presenting the help text        
        self.dockDlg.helpButton.clicked.connect(self.on_dockDlg_help_button_clicked)
        
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
        
        self.markerCoordinatesDlg.closeButton.clicked.connect(self.on_markerCoordinatesDlg_closeButton)
        
        # Identify when a new layer is added, removed, re-named to the project in order to re-populate the layers
        QgsProject.instance().layersAdded.connect(self.on_layer_tree_changed)
        QgsProject.instance().layersRemoved.connect(self.on_layer_tree_changed)
        QgsProject.instance().layerTreeRoot().nameChanged.connect(self.on_layer_tree_changed)
        QgsProject.instance().readProject.connect(self.read_project)
        
        #Identify when the active layer changes to change the vertex identification on the current layer
        self.canvas.currentLayerChanged.connect(self.pointTool.updateLayersLocators)
        
        # Identify when the project CRS changes
        QgsProject.instance().crsChanged.connect(self.on_project_crsChanged)
        #QgsProject.instance().ellipsoidChanged.connect(self.on_project_crsChanged)
               
        # Identify the condition where another toolset is activated, so that we must unpress all buttons of the dock dialog
        self.canvas.mapToolSet.connect(self.on_toolset_change)
        
        # We create marker 0 and 4 for start and stop points,
        # as well as 1,2 and 3 for the middle point. Total of 5.
        # Additional middle points may be added in the future, with perhaps a list functionality, provided that the will be able to be visually managed on map.
        self.createMarkers(self.numMarkers)
        # Change the default icon only for the start and stop markers 
        # Issue #2. Use only icons allowed to be used as vertex markers in old QGIS versions. 
        self.markers[0].setIconType(self.defaultStartMarkerIcon)
        self.markers[self.numMarkers - 1].setIconType(self.defaultEndMarkerIcon)             
        # Hide all markers. We will show each one when needed
        self.hideMarkers()  
        
        # Remember the current QGIS Project CRS so that we can convert coordinates if the project CRS is changed
        self.projectCrs = QgsProject.instance().crs()
        
        # Issue #1. Populate combobox immediately upon installation, to cover the case where layers are already loaded 
        self.populateLayerSelector()
        
        # Remember the default settings of push buttons, so that we reset them when necessary. The
        # start button is taken as a sample, assuming that start, stop and middle buttons share the same stylesheets
        self.pushButtonOriginalStylesheet = self.dockDlg.calculateButton.styleSheet()  
        
        self.fiberWidgets = [self.dockDlg.label_3, self.dockDlg.addFixedLoss, self.dockDlg.fiberLoss, self.dockDlg.fiberLossUnits]
        self.controlWidgets = [self.dockDlg.calculateButton, self.dockDlg.resetButton, self.dockDlg.addLayerButton, self.dockDlg.configureButton, self.dockDlg.helpButton] 
        self.controlWidgetsMovedUp = False
        # Hide fiber loss widgets if configured
        if self.currentConfig["resultDialogTypeIndex"] == 1 or self.currentConfig["resultDialogTypeIndex"] == 3:
            self.hideFiberWidgets()
            self.moveUpControlWidgets()
        
        # A list of coordinate buttons. Not used at the moment. To be used for code optimization in next release
        self.coordinateButtons = [self.dockDlg.startCoordinatesButton,
                             self.dockDlg.middleCoordinatesButton, 
                             self.dockDlg.middle2CoordinatesButton,
                             self.dockDlg.middle3CoordinatesButton,
                             self.dockDlg.endCoordinatesButton]
                      
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

        if dict["addResultLayer"] == 1:
            dlg.addResultLayer.setChecked(True)
        else:
            dlg.addResultLayer.setChecked(False)

        if dict["addMergedLayer"] == 1:
            dlg.addMergedLayer.setChecked(True)
        else:
            dlg.addMergedLayer.setChecked(False)
           
        self.populateComboBox(dlg.distanceUnits, self.distanceUnits, dict["distanceUnitsIndex"])                   
        self.populateComboBox(dlg.resultDialogType, self.resultTypes, dict["resultDialogTypeIndex"])

        self.temporaryCrsMethod = dict["selectedCrsMethod"]
        self.setConfigurationSelectCrs(dict["selectedCrsMethod"])  
        dlg.mQgsProjectionSelectionWidget.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(dict["customCrs"]))  
        
        crs = self.activeCrs()
        crsData = self.geom.crsDetails(crs)
        dlg.measurementEllipsoid.setText(crsData[0]) 
        dlg.crsUnits.setText(self.geom.crsDistanceUnits(crs))
       
        self.populateComboBox(dlg.toleranceUnits, self.distanceUnits, dict["toleranceUnitsIndex"])        
                        
        dlg.connectorLoss.setValue(dict["connectorLoss"])
        dlg.numberOfConnectorsAtEntry.setValue(dict["numberOfConnectorsAtEntry"])
        dlg.numberOfConnectorsAtExit.setValue(dict["numberOfConnectorsAtExit"])
        dlg.spliceLoss.setValue(dict["spliceLoss"])
        dlg.spliceFrequency.setValue(dict["spliceFrequency"])
        dlg.cableLoss.setValue(dict["cableLoss"]) 
        dlg.fixedLoss.setValue(dict["fixedLoss"])
 
        self.populateComboBox(dlg.coordinateFormat, self.coordinateFormats, dict["coordinateFormatIndex"])
        self.populateComboBox(dlg.markerSnapMethod, self.markerSnapMethods, dict["markerSnapMethod"])
        dlg.markerSnapPixels.setValue(dict["markerSnapPixels"])
        if dict["markerSnapToMap"] == 1:
            dlg.snapToMap.setChecked(True)
        else:
            dlg.snapToMap.setChecked(False)        
        
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

        if dlg.addResultLayer.isChecked():
            conf["addResultLayer"] = 1
        else: 
            conf["addResultLayer"] = 0
            
        if dlg.addMergedLayer.isChecked():
            conf["addMergedLayer"] = 1
        else: 
            conf["addMergedLayer"] = 0

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
        
        for index, optionTxt in enumerate(self.coordinateFormats):          
            if dlg.coordinateFormat.currentIndex() == index:       
                conf["coordinateFormatIndex"] = index
        
        try:
            # I did not find a method to return the EPSG is as integer. I remove the first 5 characters "EPSG:" 
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
        
        for index, optionTxt in enumerate(self.markerSnapMethods):          
            if dlg.markerSnapMethod.currentIndex() == index:       
                conf["markerSnapMethod"] = index
        
        conf["markerSnapPixels"] = dlg.markerSnapPixels.value()
        if dlg.snapToMap.isChecked():
            conf["markerSnapToMap"] = 1
        else: 
            conf["markerSnapToMap"] = 0
            
        # Store to QGIS settings repository
        self.storeQgsSettings()
        return        
        

    def display_point(self, point:QgsPointXY, button) -> None:   
        m = self.markers  
                              
        try:
            
            if self.currentConfig["markerSnapToMap"]  == 0:
                # Explicit casting to QgsPointXY required to run on Linux
                p = QgsPointXY(point)
            else: 
                if self.pointTool.snappedPoint != None:            
                    p = QgsPointXY(self.pointTool.snappedPoint)
                else:
                    p = QgsPointXY(point)
            
            if self.startButtonPressed == True:
                self.dockDlg.startCoordinatesTextbox.setText(self.formatPointCoordinates(p))
                m[0].setCenter(p)
                m[0].show()
                self.pointsDict[0] = p
                self.dockDlg.startCoordinatesButton.setStyleSheet(self.assignedButtonStyleSheet)

            if self.endButtonPressed == True:
                self.dockDlg.endCoordinatesTextbox.setText(self.formatPointCoordinates(p))                
                m[4].setCenter(p)
                m[4].show()
                self.pointsDict[4] = p
                self.dockDlg.endCoordinatesButton.setStyleSheet(self.assignedButtonStyleSheet)

            if self.middleButtonPressed == True:
                m[1].setCenter(p)   
                m[1].show()
                self.pointsDict[1] = p
                self.dockDlg.middleCoordinatesButton.setStyleSheet(self.assignedButtonStyleSheet)
                
            if self.middle2ButtonPressed == True:
                m[2].setCenter(p)   
                m[2].show()
                self.pointsDict[2] = p
                self.dockDlg.middle2CoordinatesButton.setStyleSheet(self.assignedButtonStyleSheet)                
                
            if self.middle3ButtonPressed == True:
                m[3].setCenter(p)   
                m[3].show()
                self.pointsDict[3] = p
                self.dockDlg.middle3CoordinatesButton.setStyleSheet(self.assignedButtonStyleSheet)                
               
        except AttributeError:
            #print("No attribute")
            self.iface.messageBar().pushMessage("Error", "Exception: No attribute", level=Qgis.Critical)
            
        self.populateMarkerCoordinatesDialog()    
        return


    def on_layer_tree_changed(self) -> None:
        self.pointTool.reset()
        self.pointTool.updateLayersLocators()
        self.populateLayerSelector()
        return


    def populateLayerSelector(self) -> None:
        self.dockDlg.layerCombobox.clear()
        # Get all map layers in the project
        layers = QgsProject.instance().mapLayers()
        # Iterate over layers and identify open line layers
        # Create a list containing (layer name, unique layer id) from which 
        # I will populate the combo box and be able to work with the index and the unique id,
        # having the name only for presentation purposes 
        self.loadedLayerList.clear()
        index = 0        
        for layer_id, layer in layers.items():
            #Select only Vector line layers
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.LineGeometry and layer.crs().authid() != '':
                tuple = (layer.name(), layer_id)
                self.loadedLayerList.append(tuple)
                presentationName = layer.name() + ' [' + layer.crs().authid() + ']'
                # Index numbering in Qt combobox starts also at 0. Empty is -1
                self.dockDlg.layerCombobox.insertItem(index, presentationName)
                # Regardless of changes in the layers (add, remove, rename), if the unique layer id
                # still remains in the list, I want it to remain selected
                if layer_id in self.selectedLayersIdList:
                    self.dockDlg.layerCombobox.setItemCheckState(index, Qt.Checked)
                index += 1
                #print(f"Layer Name: {layer.name()} Layer geometryType: {layer.geometryType()}")
        return      


    def on_toolset_change(self):
        #print ("Toolset changed")
        self.uncheckAllButtons()
        return
        

    def on_dockDlg_layer_selected(self): 
        ''' Maintains a list of all the currently selected layer ids.
        It is called every time the user checks or unchecks an item in the QgsCheckableComboBox 
        '''        
        #print ("checkedItemsChanged")       
        self.selectedLayersIdList.clear()
        for i in range(0, self.dockDlg.layerCombobox.count()):
            if self.dockDlg.layerCombobox.itemCheckState(i) == Qt.Checked:
                layerId = self.loadedLayerList[i][1]
                self.selectedLayersIdList.append(layerId) 
        #print(self.selectedLayersIdList)                
        return        
    
    
    def coordButtonClicked(self, button:QPushButton) -> None:
        ''' Generic action routine when any of the start, stop, middle buttons is clicked '''
        # Activate the map tool. It must be run before the button is shown as pressed
        # so that the change tool event fires after.
        self.canvas.setMapTool(self.pointTool)
        # Need to remember in order to reset it in case the project crs is changed
        self.mapToolIsSet = True
        
        # Otherwise, when we click at any point without snapping has identified a new point, the last snapped point, no matter how far, will be set
        self.pointTool.forgetLastSnappedPoint()
        
        # Update with the current layers
        self.pointTool.updateLayersLocators()
        
        self.uncheckAllButtons()           
        button.setChecked(True)        
        return

      
    def on_dockDlg_start_coordinates_button_clicked(self) -> None:
        self.coordButtonClicked(self.dockDlg.startCoordinatesButton)
        self.startButtonPressed = True        
        return

        
    def on_dockDlg_middle_coordinates_button_clicked(self) -> None:
        self.coordButtonClicked(self.dockDlg.middleCoordinatesButton)
        self.middleButtonPressed = True    
        return


    def on_dockDlg_middle2_coordinates_button_clicked(self) -> None:
        self.coordButtonClicked(self.dockDlg.middle2CoordinatesButton)
        self.middle2ButtonPressed = True       
        return

        
    def on_dockDlg_middle3_coordinates_button_clicked(self) -> None:
        self.coordButtonClicked(self.dockDlg.middle3CoordinatesButton)
        self.middle3ButtonPressed = True       
        return        

                
    def on_dockDlg_end_coordinates_button_clicked(self) -> None: 
        self.coordButtonClicked(self.dockDlg.endCoordinatesButton)
        self.endButtonPressed = True        
        return

        
    def on_dockDlg_any_middle_coordinates_button_pressed(self) -> None:
        ''' Especially for any of the middle buttons, in contrast to the start and stop buttons,
        if pressed while it is already checked,
        it resets the value. This is useful when we want to reset the middle point
        while leaving the start and stop points as they are'''    
        # Get the button that sent the signal
        b = self.dockDlg.sender()
        if b == self.dockDlg.middleCoordinatesButton:
            index = 1
        elif b == self.dockDlg.middle2CoordinatesButton:
            index = 2
        elif b == self.dockDlg.middle3CoordinatesButton:
            index = 3  
            
        self.markers[index].hide()
        # Remove middle point
        if index in self.pointsDict:
            self.pointsDict.pop(index)
            
        b.setStyleSheet(self.pushButtonOriginalStylesheet)        
        self.populateMarkerCoordinatesDialog()
        return

          
    def on_dockDlg_reset_button_clicked(self) -> None:
        self.reset_project()
        return


    def read_project(self) -> None:
        self.reset_project()
        self.populateLayerSelector()
        return
        

    def reset_project(self) -> None:
        # De-activate the map tool
        #print("Reset button")
        self.deleteRubberBands()
        self.canvas.unsetMapTool(self.pointTool)
        self.pointTool.reset()        
        self.dockDlg.startCoordinatesTextbox.setText("")
        self.dockDlg.endCoordinatesTextbox.setText("")
        self.dockDlg.resultLength.setText("")
        self.dockDlg.lengthUnits.setText("")
        self.dockDlg.fiberLoss.setText("")
        self.dockDlg.fiberLossUnits.setText("")
        
        self.uncheckAllButtons()
        self.hideMarkers()
        
        self.dockDlg.startCoordinatesButton.setStyleSheet(self.pushButtonOriginalStylesheet)
        self.dockDlg.middleCoordinatesButton.setStyleSheet(self.pushButtonOriginalStylesheet)
        self.dockDlg.middle2CoordinatesButton.setStyleSheet(self.pushButtonOriginalStylesheet)
        self.dockDlg.middle3CoordinatesButton.setStyleSheet(self.pushButtonOriginalStylesheet)
        self.dockDlg.endCoordinatesButton.setStyleSheet(self.pushButtonOriginalStylesheet)
        
        self.pointsDict.clear()       
        self.populateLayerSelector()
        self.populateMarkerCoordinatesDialog()
        return

    
    def on_dockDlg_calculate_button_clicked(self) -> None:
       
        self.deleteRubberBands()
        #print("Starting calculation") 
        if self.dockDlg.layerCombobox.currentIndex() == -1:
            #print ("Invalid layer")
            self.iface.messageBar().pushMessage("Error", "Invalid layer", level=Qgis.Critical, duration=5)
            return
            
        if  0 not in self.pointsDict: # start point exists
            #print ("Invalid start coordinates")
            self.iface.messageBar().pushMessage("Error", "Invalid start coordinates", level=Qgis.Warning, duration=5)
            return

        if  4 not in self.pointsDict: # end point exists
            #print ("Invalid end coordinates")
            self.iface.messageBar().pushMessage("Error", "Invalid end coordinates", level=Qgis.Warning, duration=5)
            return
                          
        # Show busy                 
        self.dockDlg.resultLength.setText("Processing...")
        self.dockDlg.fiberLoss.setText("...")
        # Necessary to update GUI before processing takes over
        self.dockDlg.repaint()
        
        self.populateMarkerCoordinatesDialog()
               
        #Start the algorithm. On any error, results will not be completed
        # On success, the dock widgets will be filled by the process
        if self.calculate() < 0:
            self.dockDlg.resultLength.setText("......")
            self.dockDlg.fiberLoss.setText("......")                
        return


    def on_dockDlg_configure_button_clicked(self) -> None:
        self.populateConfigurationDlg(self.configurationDlg, self.currentConfig)
        self.dockDlg.configureButton.setStyleSheet(self.pushedButtonStyleSheet)
        self.configurationDlg.show()
        self.configurationDlg.activateWindow()
        return


    def on_dockDlg_eye_button_clicked(self) -> None:
        self.populateMarkerCoordinatesDialog()
        self.markerCoordinatesDlg.show()
        self.markerCoordinatesDlg.activateWindow()
        self.dockDlg.eyeButton.setStyleSheet(self.pushedButtonStyleSheet)
        return

    
    def on_markerCoordinatesDlg_closeButton(self) -> None:
        self.markerCoordinatesDlg.hide()
        self.dockDlg.eyeButton.setStyleSheet(self.pushButtonOriginalStylesheet)
        return
        
        
    def on_configurationDlg_config_complete_ok(self) -> None:
        #print("New configuration accepted")
        # Re-set the dictionary with the dialog values
        self.updateConfiguration(self.configurationDlg)
        # and update the appearance of markers
        self.updateMarkerVisuals()
        self.pointTool.setSnapMethod(self.currentConfig["markerSnapToMap"], self.currentConfig["markerSnapMethod"], self.currentConfig["markerSnapPixels"])
        self.updateRubberBandVisuals()
        self.populateMarkerCoordinatesDialog()
        if self.currentConfig["resultDialogTypeIndex"] == 1 or self.currentConfig["resultDialogTypeIndex"] == 3:
            self.hideFiberWidgets()
            if self.controlWidgetsMovedUp == False:
                self.moveUpControlWidgets()
        else:
            if self.controlWidgetsMovedUp == True:
                self.moveDownControlWidgets()            
            self.showFiberWidgets()    
        self.dockDlg.configureButton.setStyleSheet(self.pushButtonOriginalStylesheet)
            
        return


    def on_configurationDlg_config_complete_cancel(self) -> None:
        #print("Configuration canceled")
        self.dockDlg.configureButton.setStyleSheet(self.pushButtonOriginalStylesheet)
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
        crsData = self.geom.crsDetails(crs)
        self.configurationDlg.measurementEllipsoid.setText(crsData[0]) 
        self.configurationDlg.crsUnits.setText(self.geom.crsDistanceUnits(crs))
    
              
    def setConfigurationSelectCrs(self, crsMethod:int) -> None:
        
        if crsMethod == 0: # Project CRS
            self.configurationDlg.selectProjectCrs.setChecked(True)    
            self.configurationDlg.mQgsProjectionSelectionWidget.setEnabled(False)
            crs = QgsProject().instance().crs()
            
        elif crsMethod == 1: # Layer CRS
                self.configurationDlg.selectLayerCrs.setChecked(True)    
                self.configurationDlg.mQgsProjectionSelectionWidget.setEnabled(False)                 
                crs = self.optionLayerCrs()
                
        elif crsMethod == 2: # Custom CRS   
            self.configurationDlg.selectCustomCrs.setChecked(True)    
            self.configurationDlg.mQgsProjectionSelectionWidget.setEnabled(True)
            crs = self.configurationDlg.mQgsProjectionSelectionWidget.crs() 
            
        crsData = self.geom.crsDetails(crs)
        self.configurationDlg.measurementEllipsoid.setText(crsData[0]) 
        self.configurationDlg.crsUnits.setText(self.geom.crsDistanceUnits(crs))
            
        return    
    
    
    def on_project_crsChanged(self) -> None:
        ''' Function to run when the project CRS is changed '''
        #print ("Event CRS changed")
        #print ("Transforming from ", self.projectCrs.description(), " to ", QgsProject().instance().crs().description())  
        newCrs = QgsProject.instance().crs()        
        self.transformInputData(self.projectCrs, newCrs)
        self.projectCrs = newCrs

        # Update also the configuration dialog which is non modal and could be open
        crsData = self.geom.crsDetails(newCrs)
        self.configurationDlg.measurementEllipsoid.setText(crsData[0]) 
        self.configurationDlg.crsUnits.setText(self.geom.crsDistanceUnits(newCrs))   

        # Need to unset the mapTool to cope with the new coordinate system
        if self.mapToolIsSet == True:
            self.canvas.unsetMapTool(self.pointTool)

        return
 
 
    def on_resultsDlg_results_ok(self) -> None:
        self.resultsDlg.hide()
        return


    def on_resultsDlgNoFiber_results_ok(self) -> None:
        self.resultsDlgNoFiber.hide()
        return
        
         
    def uncheckAllButtons(self) -> None:
        dlg = self.dockDlg
        dlg.startCoordinatesButton.setChecked(False)
        dlg.middleCoordinatesButton.setChecked(False)
        dlg.middle2CoordinatesButton.setChecked(False)
        dlg.middle3CoordinatesButton.setChecked(False)
        dlg.endCoordinatesButton.setChecked(False) 
        
        self.startButtonPressed = False
        self.middleButtonPressed = False
        self.middle2ButtonPressed = False
        self.middle3ButtonPressed = False       
        self.endButtonPressed = False
        return
 

    def activeCrs(self) -> QgsCoordinateReferenceSystem:
        ''' Returns the QgsCoordinateReferenceSystem to be used for measurements 
            This can be either the Project CRS, the CRS of the line layer or a Custom CRS ''' 
        try:       
            if self.currentConfig["selectedCrsMethod"] == 0: # Project CRS
                crs = QgsProject.instance().crs()
            elif self.currentConfig["selectedCrsMethod"] == 1: # Layer CRS
                crs = self.optionLayerCrs()
            else: # Custom CRS
                crs = QgsCoordinateReferenceSystem.fromEpsgId(self.currentConfig["customCrs"]) 
            return crs 
        except:
            return None        
       
          
    def calculate(self) -> int:

        measureCrs = self.activeCrs() 
        if measureCrs is None:
            self.iface.messageBar().pushMessage("Error", "Invalid measure CRS", level=Qgis.Critical, duration=5)
            return -1  
                
        layersList = self.selectedLayersList() 
        num_layers = len(layersList)

        if num_layers < 1:
            self.iface.messageBar().pushMessage("Error", "One or more line layers must be selected...", level=Qgis.Critical, duration=5)
            return -1            
        elif num_layers == 1:
            pathLayer = layersList[0]
        else:
            pathLayer = self.mergedMemoryLayer(measureCrs)
              
        if pathLayer.crs().authid() == "":
            self.iface.messageBar().pushMessage("Error", "Path layer does not have a valid CRS", level=Qgis.Critical, duration=5)
            return -1
        #print ("CRS of path layer: ", pathLayer.crs().authid())


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
        crsData = self.geom.crsDetails(measureCrs)          
        self.resultsDict["ellipsoid"] = crsData[0] 
        self.resultsDict["crs"] = crsData[1] + "/" + crsData[2] 
        self.resultsDict["lengthUnits"] = crsData[3]

        ''' We expect that the distance units returned by crsData[3] will be meters in order to make 
            our conversions. Most CRS and associated ellipsoids' units are in meters or can be converted by QGIS from 
            feet or other unit to meters. If not, or in case a CRS is not defined for the project,
            we present a warning and return the values and units returnded by QgsDistanceArea class without conversion 
            From 1.2.1, we convert to meters and use meters for fiber loss calculations    
            
        '''
        if self.resultsDict["lengthUnits"] == "meters":
            conversionIndex = self.currentConfig["distanceUnitsIndex"]
            # From 1.0.4, we use the converted units
            self.resultsDict["lengthUnits"] = self.resultUnitsList[self.currentConfig["distanceUnitsIndex"]]
            
            #1.2.1
            # We store the results in meters to use in fiber loss calculations where attenuation is given as db/Km
            self.resultsDict["entryCostMeters"] = entryCost
            self.resultsDict["costOnGraphMeters"] = costOnGraph
            self.resultsDict["exitCostMeters"] = exitCost
            self.resultsDict["totalCostMeters"] = entryCost + costOnGraph + exitCost          
            
        else: 
            # Not really sure if necessary. Probably setting the ellipsoid in QgsGraphBuilder(currentCrs, True, topologyTolerance, currentCrs.ellipsoidAcronym())
            # defines an ellipsoidal measurement, which uses the metric system. QGIS documentation does not cover the issue.            
            conversionIndex = -1
            self.iface.messageBar().pushMessage("Warning", "Base distance unit is not meters but " + crsData[3] +". Unit conversion is taking place", level=Qgis.Warning, duration=5)
            self.resultsDict["entryCostMeters"] = self.geom.lengthInMeters(entryCost, measureCrs)
            self.resultsDict["costOnGraphMeters"] = self.geom.lengthInMeters(costOnGraph, measureCrs)
            self.resultsDict["exitCostMeters"] = self.geom.lengthInMeters(exitCost, measureCrs)
            self.resultsDict["totalCostMeters"] = self.resultsDict["entryCostMeters"] + self.resultsDict["costOnGraphMeters"] + self.resultsDict["exitCostMeters"]          
                        
            
        # Convert distances in the configuration selected units if the original unit is in meters, otherwise leave as is   
        self.resultsDict["entryCost"] = self.geom.convertDistanceUnits(entryCost, conversionIndex)
        self.resultsDict["costOnGraph"] = self.geom.convertDistanceUnits(costOnGraph, conversionIndex)
        self.resultsDict["exitCost"] = self.geom.convertDistanceUnits(exitCost, conversionIndex)
        self.resultsDict["totalCost"] = self.resultsDict["entryCost"] + self.resultsDict["costOnGraph"] + self.resultsDict["exitCost"]  
     
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
        if self.currentConfig["resultDialogTypeIndex"] == 3:
            self.showResultDlg(self.resultsDlgNoFiber, self.resultsDict) 
        elif self.currentConfig["resultDialogTypeIndex"] == 2:            
            self.showResultDlg(self.resultsDlg, self.resultsDict)
        
        if self.currentConfig["addResultLayer"] == 1:
            self.addRubberBandsToMap()
        
        return 0

               
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
        entry_cost = self.geom.distanceP2P(currentCrs, fromPoint, tStart)      
        exit_cost = self.geom.distanceP2P(currentCrs, tStop, toPoint)

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

        ''' I need to transform to the map coordinates in order to draw
         To avoid checking CRSs for every point, a programming ugly method is below.
         Yet, I prefer to save system resources and be faster, if possible '''
        if currentCrs == self.projectCrs:
            if addStartPoint:
                rb.addPoint(fromPoint)             
            for p in route:
                rb.addPoint(p)                 
        else: 
            ''' Create a transformation instance to be used for subsequent point transformations
            The creation of this instance is heavy on system resources and causes unnecessary delays, 
            so I better do it once and use many, especially when route has many points. '''     
            tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(currentCrs), QgsCoordinateReferenceSystem(self.projectCrs), QgsProject.instance().transformContext())          
            if addStartPoint:
                rb.addPoint(tr.transform(fromPoint))             
            for p in route:
                rb.addPoint(tr.transform(p))  
              
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
       

    def createMarkers(self, numMarkers:int) -> None:
        '''  Ceates markers with the default settings. The iconType of start 
        and end markers will be changed manually '''    
    
        for i in range(numMarkers):
            self.markers.insert(i, QgsVertexMarker(self.canvas))        
            self.markers[i].setIconType(self.defaultMiddleMarkerIcon) # e.g. ICON_CROSS, ICON_X
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
        return str(floatFormat%length)
        
    
    def formatLossValue(self, loss:float) -> str:
        ''' Rounds and formats a fiber loss value to the defined number of decimal digits '''
        decimalDigits = self.fiber_loss_precision
        floatFormat = "%." + str(decimalDigits) + "f"
        return str(floatFormat%loss)
        
    
    def calculateFiberLoss(self) -> None:
        ''' Runs after the results dictionary has been populated with the proper lengths.
            Adjustment is made with the division of length by 1000.0 because the cinfiguration parameters are in db/Km   '''
        d = self.resultsDict
        
        conectorLossAtEntry = (self.currentConfig["connectorLoss"] * self.currentConfig["numberOfConnectorsAtEntry"])
        conectorLossAtExit = (self.currentConfig["connectorLoss"] * self.currentConfig["numberOfConnectorsAtExit"])
             
        d["fiberLossEntry"] = conectorLossAtEntry \
                              + self.spliceLoss(d["entryCostMeters"]) \
                              + d["entryCostMeters"] /1000.0 * self.currentConfig["cableLoss"] 
        
        d["fiberLossExit"] = conectorLossAtExit \
                             + self.spliceLoss(d["exitCostMeters"]) \
                             + d["exitCostMeters"] /1000.0 * self.currentConfig["cableLoss"] 
                                                        
        d["fiberLossOnGraph"] =  d["costOnGraphMeters"] / 1000.0 * self.currentConfig["cableLoss"] \
                                 + self.spliceLoss(d["costOnGraphMeters"]) 
        
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
    
        tr = QgsCoordinateTransform(QgsCoordinateReferenceSystem(sourceCRS), QgsCoordinateReferenceSystem(targetCrs), QgsProject.instance())
        transformedPoint = tr.transform(point)                               
        return transformedPoint

  
    def transformedPointsList(self, points, fromCrs:QgsCoordinateReferenceSystem, toCrs:QgsCoordinateReferenceSystem) -> None:
        trPoint = []
        for i, point in enumerate(points):
            trPoint.append(self.transformPointCoordinates(points[i], fromCrs.authid(), toCrs.authid())) 
        return trPoint


    def transformInputData(self, fromCrs:QgsCoordinateReferenceSystem, toCrs:QgsCoordinateReferenceSystem) -> None:
        ''' Transforms the coordinates of the points dictionary and updates the textboxes with the string
        representation of the coordinates for start and stop points (coordinates of middle points do not appear) ''' 

        for key, point in self.pointsDict.items():  
            trPoint = self.transformPointCoordinates(point, fromCrs.authid(), toCrs.authid())            
            self.pointsDict[key] = trPoint
            #self.markers[self.pointIndexToMarkerIndex(key)].setCenter(trPoint) obsolete in 1.2.1
            self.markers[key].setCenter(trPoint)
            
            if key == 0:
                self.dockDlg.startCoordinatesTextbox.setText(self.formatPointCoordinates(trPoint)) 
            elif key == 4:
                self.dockDlg.endCoordinatesTextbox.setText(self.formatPointCoordinates(trPoint))
        
        # Also update the marker coordinates dialog
        self.populateMarkerCoordinatesDialog()

        return

    ''' OBSOLETE in release 1.2.1 To be deleted entirely in nex trelease'''
    '''        
    def pointIndexToMarkerIndex(self, pointIndex:int) -> int:
        # Maintains a map between the index of the points dictionary, which are in 
        # order {start, middles...., end} and the marker index which is in order {start, end, middles...}    
        map = { 0:0, 4:1, 1:2, 2:3, 3:4}
        return map[pointIndex]    
    '''    

      
    def toleranceToMapUnits(self, crs:QgsCoordinateReferenceSystem, toleranceUnitsIndex:int, topologyTolerance:float) -> float:
        ''' Converts the tolerance value from the units set in the configuration dialog to the map units of the CRS'''
        configuredUnitIndex = toleranceUnitsIndex
        toleranceUnits = self.distanceUnits[configuredUnitIndex]
        unit = QgsUnitTypes.stringToDistanceUnit(toleranceUnits)[0]
        toleranceMapUnits = QgsUnitTypes.fromUnitToUnitFactor(unit, crs.mapUnits()) * topologyTolerance
        return toleranceMapUnits 
      
        
    def selectedLayersList(self) -> list[QgsVectorLayer]:
        ''' Returns a list of layers selected via the multi-selection combobox   '''
        layersList = [] 
        self.selectedLayersIdList.clear()
        for i in range(0, self.dockDlg.layerCombobox.count()):
            if self.dockDlg.layerCombobox.itemCheckState(i) == Qt.Checked:
                layerId = self.loadedLayerList[i][1]
                self.selectedLayersIdList.append(layerId)     
                layerObj = QgsProject.instance().mapLayer(layerId)
                layersList.append(layerObj)              
        return  layersList      

        
    def optionLayerCrs(self) -> QgsCoordinateReferenceSystem:
        ''' Returns a CRS when the configuration option Layer CRS is selected.
        Since the system supports the selection of multiple CRS, probably having different CRSs,
        the algorithm behaves like this:
           If one single layer is selected, returns the crs of the layer
           If no layer is in the list or if multiple layers are selected, returns the project CRS
        '''
        layersList = self.selectedLayersList()
        if len(layersList) == 1 :
            crs = layersList[0].sourceCrs()
        else:    
            crs = QgsProject.instance().crs()
        return crs    


    def createMemLayer(self, layerName: str, crs:QgsCoordinateReferenceSystem) -> QgsVectorLayer:
        ''' Creates and returns a memory line layer, 
        '''       
        #mem_layer = QgsVectorLayer("LineString?crs=" + crs.authid(), "temp_layer", "memory")
        # Better use the proper core function rather than the string concatenation method
        fields = QgsFields() # just need to construct the object to pass below. No fields are added
        mem_layer = QgsMemoryProviderUtils.createMemoryLayer(layerName, fields, QgsWkbTypes.LineString, crs)

        # To avoid QGIS issuing warning message to save project and potential data loss if there are any non-empty memory layers present
        mem_layer.setCustomProperty("skipMemoryLayersCheck", 1)
        if not mem_layer.isValid():
            self.iface.messageBar().pushMessage("Error", "Failed to create memory layer", level=Qgis.Critical, duration=5)
            return None
            
        return mem_layer 
        
        
    def mergedMemoryLayer(self, crs:QgsCoordinateReferenceSystem) -> QgsVectorLayer:
        ''' Merge layers into a memory layer '''
        pathLayer = self.createMemLayer(self.mergedLayerName, crs)
        layersList = self.selectedLayersList()
        pr = pathLayer.dataProvider()

        for layer in layersList:
            if layer.crs().authid() == "":
                self.iface.messageBar().pushMessage("Warning", "Layer " + layer.name() + " does not have a valid CRS", level=Qgis.Warning, duration=5)
            else:
                #print(layer.name(), layer.crs().authid())
                features = layer.getFeatures()
                if layer.crs().authid() == crs.authid():
                    #print ("Same authid. No need to transform")
                    pr.addFeatures(features)
                else:
                    #print ("Different authids. Must transform")
                    # NOTE: Does transformation maintains topological snapping between layers of different CRS or when two layers of a CRS are transformed to the memory layer CRS?
                    xform = QgsCoordinateTransform(layer.crs(), crs, QgsProject.instance().transformContext())
                    for feature in layer.getFeatures():
                        geometry = feature.geometry()
                        geometry.transform(xform)
                        feature.setGeometry(geometry)
                        pr.addFeatures([feature])  
                        
        pathLayer.updateExtents()
        # Add merged layer to the layer browser
        if self.currentConfig["addMergedLayer"] == 1:
            QgsProject.instance().addMapLayer(pathLayer)
        return pathLayer        

   
    def formatPointCoordinates(self, point:QgsPointXY) -> str:
        ''' Returns a string with the coordinates of a point, formatted according to the configuration setting ["x y", "y x", "x, y", "y, x"]'''       
        x, y = point.x(), point.y()
        s = ""
        if self.currentConfig["coordinateFormatIndex"] == 0: # x y
            s = str(x) + " " + str(y)
        elif self.currentConfig["coordinateFormatIndex"] == 1: # y x
            s = str(y) + " " + str(x)
        elif self.currentConfig["coordinateFormatIndex"] == 2: # x, y
            s = str(x) + ", " + str(y)
        elif self.currentConfig["coordinateFormatIndex"] == 3: # y, x
            s = str(y) + ", " + str(x)
        else:
            s = str(x) + " " + str(y)
        return s  


    def populateComboBox(self, comboBoxWidget, contentList:list, selectedIndex:int) -> None:
        ''' Populates a comboBox widget with the contents of a list, having selected the index value at selectedIndex '''
        comboBoxWidget.clear()
        for index, optionTxt in enumerate(contentList):       
            comboBoxWidget.addItem(optionTxt)
            if selectedIndex == index:
                comboBoxWidget.setCurrentIndex(index)
        return        


    def populateMarkerCoordinatesDialog(self) -> None:
        ''' Sets the values of the coordinates of the marker points to the textboxes of the dialog '''
        dlg = self.markerCoordinatesDlg
        textBoxObjects = [  dlg.startCoords,
                            dlg.middle1Coords,
                            dlg.middle2Coords,
                            dlg.middle3Coords,
                            dlg.endCoords
                         ]   
        
        # Clear all because not all markers are present in the dictionary to be set        
        for txtBox in textBoxObjects:
            txtBox.clear()
    
        for key, point in self.pointsDict.items():              
            textBoxObjects[key].setText(self.formatPointCoordinates(point))       

        # Also update the textboxes of the dockDlg
        if 0 in self.pointsDict:
           self.dockDlg.startCoordinatesTextbox.setText(self.formatPointCoordinates(self.pointsDict[0]))
        if 4 in self.pointsDict:
           self.dockDlg.endCoordinatesTextbox.setText(self.formatPointCoordinates(self.pointsDict[4]))           
        
        return

        
    def hideFiberWidgets(self) -> None:
        for w in self.fiberWidgets:
            w.hide()
        return            


    def showFiberWidgets(self) -> None:
        for w in self.fiberWidgets:
            w.show()  
        return            
    
    
    def moveUpControlWidgets(self) -> None:
        self.controlWidgetsMovedUp = True
        for w in self.controlWidgets:
            g = w.geometry()
            w.setGeometry(g.adjusted(0, -self.yOffset, 0, 0))
        return

        
    def moveDownControlWidgets(self) -> None:
        self.controlWidgetsMovedUp = False
        for w in self.controlWidgets:
            g = w.geometry()
            w.setGeometry(g.adjusted(0, +self.yOffset, 0, 0))
        return        

    '''
    OBSOLETE: This function added each rubberband as a feature.
    I want to have one single feature in order to set the results of the analysis'''
    '''
    def addRubberBandsToMap(self) -> None:
        if len(self.rubberBands) <= 0:
            return
        layer = self.createMemLayer(self.resultLayerName, QgsProject.instance().crs())
        pr = layer.dataProvider()
        for rb in self.rubberBands:
            geometry = rb.asGeometry()
            feature = QgsFeature()
            feature.setGeometry(geometry)
            pr.addFeatures([feature])             
        QgsProject.instance().addMapLayer(layer)            
        return
    '''
    
    def addRubberBandsToMap(self) -> None:
        if len(self.rubberBands) <= 0:
            return
        layer = self.createMemLayer(self.resultLayerName, QgsProject.instance().crs())
        pr = layer.dataProvider()

        # types:  QVariant.String, QVariant.Int, QVariant.Double  
                
        tempLayerfields = [
            QgsField("start", QVariant.String),
            QgsField("end", QVariant.String),
            QgsField("length", QVariant.Double),
            QgsField("lengthunits", QVariant.String),
            QgsField("fiberloss", QVariant.Double),
            QgsField("lossunits", QVariant.String),
            QgsField("entrylength", QVariant.Double),
            QgsField("pathlength", QVariant.Double),
            QgsField("exitlength", QVariant.Double),            
            QgsField("entryloss", QVariant.Double),
            QgsField("pathloss", QVariant.Double),            
            QgsField("exitloss", QVariant.Double),                        
            QgsField("middle1", QVariant.String),
            QgsField("middle2", QVariant.String),
            QgsField("middle3", QVariant.String),
            QgsField("crs", QVariant.String),
            QgsField("ellipsoid", QVariant.String)
        ]
        
        # Add fields to the provider        
        pr.addAttributes(tempLayerfields)
        layer.updateFields()  # Update the layer's schema
        
        geometry = QgsGeometry()
        # We shall collect the points of all rubberbands in a list and then we will create one multilinestring
        pointsList = []
        for rb in self.rubberBands:
            # Each rubberband may have many parts. We deal with part 0
            numVertices = rb.partSize(0)
            for i in range(0, numVertices):
                pointsList.append(rb.getPoint(0, i))                
        geometry.addPointsXY(pointsList, QgsWkbTypes.LineGeometry)                   

        # Add as one feature to the layer  
        feature = QgsFeature()
        feature.setGeometry(geometry)
        
        # To use feature.setAttribute() by name, I need to do this
        fields = QgsFields()
        for newField in tempLayerfields:
            fields.append(newField)       
        feature.setFields(fields, True)
        
        feature.setAttribute("start", self.formatPointCoordinates(self.pointsDict[0]))
        feature.setAttribute("end", self.formatPointCoordinates(self.pointsDict[4]))
        feature.setAttribute("length", self.formatLengthValue(self.resultsDict["totalCost"]))
        feature.setAttribute("lengthunits", self.resultsDict["lengthUnits"])              
        feature.setAttribute("entrylength", self.formatLengthValue(self.resultsDict["entryCost"]))
        feature.setAttribute("pathlength", self.formatLengthValue(self.resultsDict["costOnGraph"]))
        feature.setAttribute("exitlength", (self.resultsDict["exitCost"]))
        
        # Do not add values to fiber fields if fiber measurements are not required. 
        if not (self.currentConfig["resultDialogTypeIndex"] == 1 or self.currentConfig["resultDialogTypeIndex"] == 3):        
            feature.setAttribute("fiberloss", self.formatLossValue(self.resultsDict["fiberTotalLoss"]))
            feature.setAttribute("lossunits", self.resultsDict["fiberLossUnits"])                 
            feature.setAttribute("entryloss", self.formatLossValue(self.resultsDict["fiberLossEntry"]))
            feature.setAttribute("pathloss", self.formatLossValue(self.resultsDict["fiberLossOnGraph"]))
            feature.setAttribute("exitloss", self.formatLossValue(self.resultsDict["fiberLossExit"]))
            
        if 1 in self.pointsDict:
            feature.setAttribute("middle1", self.formatPointCoordinates(self.pointsDict[1]))
        if 2 in self.pointsDict:    
            feature.setAttribute("middle2", self.formatPointCoordinates(self.pointsDict[2]))
        if 3 in self.pointsDict:    
            feature.setAttribute("middle3", self.formatPointCoordinates(self.pointsDict[3]))
            
        feature.setAttribute("crs", self.resultsDict["crs"])
        feature.setAttribute("ellipsoid", self.resultsDict["ellipsoid"])
             
        pr.addFeatures([feature])        
        layer.updateExtents()
        layer.commitChanges()
        QgsProject.instance().addMapLayer(layer)            
        return
        
        
    def addFixedLossChanged(self) -> None:
        ''' Modifies the displayed loss when the addFixedLoss checkbox changes state '''
        ''' If there is no previous measurement, or the reset button was pressed and canceled the previous measurement, do nothing '''
        if self.dockDlg.fiberLoss.text() == "":
            return
        self.calculateFiberLoss()
        if self.currentConfig["includeStartStop"]:
            self.dockDlg.fiberLoss.setText(self.formatLossValue(self.resultsDict["fiberTotalLoss"]))
        else:
            self.dockDlg.fiberLoss.setText(self.formatLossValue(self.resultsDict["fiberLossOnGraph"]))
        return


    def on_dockDlg_help_button_clicked(self) -> None:
        path = "".join([self.plugin_dir, self.helpPath])
        webbrowser.open(path)
        return    