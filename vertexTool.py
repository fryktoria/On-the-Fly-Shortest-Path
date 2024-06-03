# -*- coding: utf-8 -*-
"""
***************************************************************************
    vertexTool.py
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
"""
__author__ = 'Ilias Iliopoulos'
__date__ = 'March 2024'
__copyright__ = '(C) 2024, Ilias Iliopoulos'

from qgis.gui import QgsMapToolEmitPoint, QgsVertexMarker, QgsSnapIndicator
from qgis.core import QgsPointXY, QgsPointLocator, QgsProject, QgsTolerance, QgsVectorLayer
from qgis.PyQt.QtGui import QColor

''' 
Provides snapping functionality to QgsMapToolEmitPoint.

'''

class MapToolSnapToLayers(QgsMapToolEmitPoint):

    mapToolName = "MapToolSnapToLayers"

    # For snapping, option to use the QGIS snapping tool or own snapping tool or both
    SNAPPING_PROVIDER_OWN = 0
    SNAPPING_PROVIDER_QGIS = 1
    SNAPPING_PROVIDER_BOTH = 2 # In both case, show only the tooltip of the QGIS snapper
    defaultSnappingProvider = SNAPPING_PROVIDER_BOTH    

    # snapping behaviour
    BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS = 0
    BEHAVIOUR_SHOW_VERTICES_OF_SELECTED_LAYERS = 1   
    BEHAVIOUR_SHOW_VERTICES_OF_ACTIVE_LAYER = 2

    # Select default snapping behaviour
    defaultSnappingBehaviour = BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS
    
    # snappingMethod
    MARKER_DOES_NOT_SNAP = 0
    MARKER_SNAPS_TO_VERTICES = 1
    MARKER_SNAPS_TO_SEGMENT_EDGES = 2

    defaultSnappingMethod = MARKER_SNAPS_TO_VERTICES = 1
    
    defaultShowToolTip = 0 # do not show
    defaultSnapToMatchedPoint = 0 # do not snap 
       
    # Distance in pixels to identify a near vertex (point, line start point, line end_point)
    defaultProximityTolerancePixels = 15  # in pixels
    
    # map tool visual settings
    markerIconType = QgsVertexMarker.ICON_BOX # Not user modifiable
    markerColor = QColor(0, 0, 255, 255)
    markerIconSize = 12
    markerFillColor = QColor(255, 255, 255, 0) # Not user modifiable
    markerPenWidth = 2 # Not user modifiable
    
    # A list containing tuples (layer, locator)
    layersLocators = []
         
    activeLayer = None    
     
    def __init__(self, canvas, iface, 
                 snappingBehaviour = defaultSnappingBehaviour,
                 snappingMethod:int = defaultSnappingMethod,                
                 snapToMatchedPoint:int = defaultSnapToMatchedPoint,  
                 tolerancePixels:int = defaultProximityTolerancePixels,
                 showToolTip:int = defaultShowToolTip,                 
                 markerColor:QColor = markerColor, 
                 markerSize:int =  markerIconSize,
                 snappingProvider = defaultSnappingProvider                 
                 ):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface
        self.marker = self.createMarker()        
        if snappingMethod == self.MARKER_SNAPS_TO_SEGMENT_EDGES:
            self.marker.setIconType(QgsVertexMarker.ICON_CIRCLE)    
        self.snapToMatchedPoint = snapToMatchedPoint
        self.snappingMethod = snappingMethod
        self.proximityTolerancePixels = tolerancePixels
        self.marker.setColor(markerColor)
        self.marker.setIconSize(markerSize)
        self.showToolTip = showToolTip
        self.snappingBehaviour = snappingBehaviour
        self.snappingProvider = snappingProvider
        
        self.markerIsVisible = False
        self.snappedPoint = None
        self.snappedLayers = []
        # To handle snap to all map layers upon initiation
        
        self.updateLayersLocators()
        self.setToolName(self.mapToolName)
        
        self.snapIndicator = QgsSnapIndicator(canvas)
        # Reads the current settings of the snapping parameters
        # I can modify using QgsSnappingConfig()
        self.snapper = self.canvas.snappingUtils()        
        
        return


    def setSnappingToolParameters(self, 
                    snappingBehaviour = defaultSnappingBehaviour,
                    snappingMethod:int = defaultSnappingMethod,                
                    snapToMatchedPoint:int = defaultSnapToMatchedPoint,  
                    tolerancePixels:int = defaultProximityTolerancePixels,
                    showToolTip:int = defaultShowToolTip,
                    snappingProvider:int = defaultSnappingProvider                     
                ) -> None:

        self.snapToMatchedPoint = snapToMatchedPoint
        self.snappingMethod = snappingMethod
        if self.snappingMethod == self.MARKER_SNAPS_TO_SEGMENT_EDGES:
            self.marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        else:
            self.marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.proximityTolerancePixels = tolerancePixels
        self.showToolTip = showToolTip
        self.snappingBehaviour = snappingBehaviour
        self.snappingProvider = snappingProvider
        
        self.updateLayersLocators()       
        return


    def setMarkerVisuals(self, color:QColor = markerColor, size:int = markerIconSize) -> None:
        self.marker.setColor(color)
        self.marker.setIconSize(size)         
        return

        
    def reset(self) -> None:        
        # Required in case of snapping to all map layers, upon reading a new project  
        self.setLayersToSnap(None)        
        self.activeLayer = None 
        return        
        
 
    def updateLayersLocators(self) -> None:
        ''' 
        Updates the list of  layers at the current moment and 
        assigns a locator to each layer
        ''' 
        # No need to create locators if snapping is not wanted
        if self.snappingMethod == self.MARKER_DOES_NOT_SNAP:
            return

        if self.snappingBehaviour == self.BEHAVIOUR_SHOW_VERTICES_OF_ACTIVE_LAYER:        
            # if we want the marker to show vertices of only the active layer
            layers = []
            if self.canvas.currentLayer() != None:
                layers.append(self.canvas.currentLayer())  
                
        elif self.snappingBehaviour == self.BEHAVIOUR_SHOW_VERTICES_OF_SELECTED_LAYERS: 
            layers = self.snappedLayers
        
        else: # all layers, even invisible
            layers = QgsProject.instance().mapLayers().values()            

        #print ("updateLayersLocators", layers)
        self.layersLocators.clear()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                # CRS MUST be the projects CRS to work with all behaviours
                locator = QgsPointLocator(layer, QgsProject.instance().crs(), QgsProject.instance().transformContext())
                self.layersLocators.append((layer, locator))

        return            

    
    def canvasMoveEvent(self, event):
    
        QGIS_snappedPoint = None
        OWN_snappedPoint = None
    
        if self.snappingProvider == self.SNAPPING_PROVIDER_BOTH or self.snappingProvider == self.SNAPPING_PROVIDER_QGIS:   
        # Using the QGIS snapping tool. 
            snapMatch = self.snapper.snapToMap(event.pos())
            self.snapIndicator.setMatch(snapMatch) 
            if self.snapIndicator.match().type():
                QGIS_snappedPoint = self.snapIndicator.match().point()
            else:
                QGIS_snappedPoint = None
                       
        if self.snappingProvider == self.SNAPPING_PROVIDER_BOTH or self.snappingProvider == self.SNAPPING_PROVIDER_OWN:        
        
            # No need to do anything if snapping is not wanted
            if self.snappingMethod == 0:
                return  
          
            mouse_point = self.toMapCoordinates(event.pos())       
            layerNamesList = []  
            matchFound = False        
            # Search layer by layer using the layer locator
            # Get the coordinates of the first match and continue for the rest of the layers, only to get the layers name to show in the tooltip
            for layer_locator in self.layersLocators: 
                
                self.activeLayer = layer_locator[0]
                # set tolerance in pixels
                tolerance =  QgsTolerance.toleranceInProjectUnits(self.proximityTolerancePixels, self.activeLayer, self.iface.mapCanvas().mapSettings(), QgsTolerance.Pixels)
        
                # Takes a lot of time (2-3 seconds) to check for a match when it runs for the first time in heavy projects and layers.
                # It is quicker at next iteration but to make things feel better the first time, I used the relaxed=True
                if self.snappingMethod == self.MARKER_SNAPS_TO_VERTICES:
                    match = layer_locator[1].nearestVertex(mouse_point, tolerance, relaxed = True)
                elif self.snappingMethod == self.MARKER_SNAPS_TO_SEGMENT_EDGES: 
                    match = layer_locator[1].nearestEdge(mouse_point, tolerance, relaxed = True)
                else: 
                    match = layer_locator[1].nearestVertex(mouse_point, tolerance, relaxed = True)
        
                if match.isValid():             
                    if matchFound == False:
                        # for the first valid match
                        matchFound = True
                        edgePoint = match.point()
                        self.marker.setCenter(edgePoint)
                        #print(f"Nearest matched point in layer {self.activeLayer.name()} within tolerance {tolerance}: {edgePoint.x()}, {edgePoint.y()}")
                        
                    # for all layer matches                    
                    layerNamesList.append(self.activeLayer.name())        
                
        
            if matchFound == True:
                OWN_snappedPoint = edgePoint
                if self.showToolTip == True and self.snappingProvider == self.SNAPPING_PROVIDER_OWN: # Is there a way to disable the tooltip of the QGIS snapping tool in BOTH case? QgsSnappingConfig does not provide such option!
                    self.marker.setToolTip(",".join(layerNamesList))
                self.marker.show()
                self.markerIsVisible = True 
            else:
                if self.markerIsVisible == True:
                    self.marker.hide() 
                    self.markerIsVisible = False
                    OWN_snappedPoint = None                

        # External code can make use of self.whatevertool.snappedPoint
        # If it is None, snapping has not taken place, else it contains the coordinates of the snapped point
        # The method conditionalOffsetToSnappedPoint() keeps this internally.
        
        # In the case of BOTH option, select which point to return to the rest of the code
        if self.snappingProvider == self.SNAPPING_PROVIDER_BOTH:
            # Prefer own point. But, to cover the case where e.g. snaps on intersection, which the own tool cannot snap...
            if OWN_snappedPoint is None and QGIS_snappedPoint is not None:
                self.snappedPoint = QGIS_snappedPoint
            else:
                self.snappedPoint = OWN_snappedPoint
            '''    
            if OWN_snappedPoint is not None or QGIS_snappedPoint is not None: 
                print ("BOTH: valid snap at ", self.snappedPoint)           
            '''    
        elif self.snappingProvider == self.SNAPPING_PROVIDER_QGIS:
            if QGIS_snappedPoint is None and OWN_snappedPoint is not None:
                self.snappedPoint = OWN_snappedPoint
            else:
                self.snappedPoint = QGIS_snappedPoint
            '''    
            if OWN_snappedPoint is not None or QGIS_snappedPoint is not None: 
                print ("QGIS: valid snap at ", self.snappedPoint)                
            '''    
        else:
            self.snappedPoint = OWN_snappedPoint
            '''
            if OWN_snappedPoint is not None: 
                print ("OWN: valid snap at ", self.snappedPoint) 
            '''                
        return        


    def conditionalOffsetToSnappedPoint(self, mousePoint:QgsPointXY) -> QgsPointXY:
        if self.snapToMatchedPoint == 0:
            # Explicit casting to QgsPointXY required to run on Linux
            p = QgsPointXY(mousePoint)
        else: 
            if self.snappedPoint != None:            
                p = QgsPointXY(self.snappedPoint)
            else:
                p = QgsPointXY(mousePoint)
        return p      
                
                
    def createMarker(self) -> None: 
        marker = QgsVertexMarker(self.canvas)        
        marker.setIconType(self.markerIconType)
        marker.setColor(self.markerColor)
        marker.setFillColor(self.markerFillColor)
        marker.setIconSize(self.markerIconSize)
        marker.setPenWidth(self.markerPenWidth)        
        marker.hide()
        return  marker  

        
    def forgetLastSnappedPoint(self) -> None:
        self.snappedPoint = None
        return
    
    
    def setLayersToSnap(self, layers) -> None: 
        if layers is None:
            # e.g. when reading a new project
            self.snappedLayers.clear()
        else:    
            self.snappedLayers = layers 
            
        self.updateLayersLocators()  
        return 


          