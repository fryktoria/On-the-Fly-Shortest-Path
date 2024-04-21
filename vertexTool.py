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

from qgis.gui import QgsMapTool, QgsMapToolEmitPoint, QgsVertexMarker
from qgis.core import QgsPointXY, QgsPointLocator, QgsProject, QgsTolerance, QgsMapSettings, QgsVectorLayer
from qgis.PyQt.QtGui import QColor

class CustomVertexTool(QgsMapToolEmitPoint):

    BEHAVIOUR_SHOW_VERTICES_OF_ACTIVE_LAYER = 0
    BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS = 1
    
    # snapMethod
    MARKER_DOES_NOT_SNAP = 0
    MARKER_SNAPS_TO_VERTICES = 1
    MARKER_SNAPS_TO_LINES = 2
    
    # Select default behaviour
    behaviour = BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS

    # A list containing tuples (layer, locator)
    layersLocators = [] 
    activeLayer = None
    
    # Distance in pixels to identify a near vertex (point, line start point, line end_point)
    proximityTolerancePixels = 15  # in pixels
    
    # map tool Icon settings
    markerIconType = QgsVertexMarker.ICON_BOX
    markerColor = QColor(0, 0, 255, 255)
    markerFillColor = QColor(255, 255, 255, 0) 
    markerPenWidth = 2
    markerIconSize = 12
    
     
    def __init__(self, canvas, iface, snapToMap = 0, snapMethod = MARKER_SNAPS_TO_VERTICES, tolerancePixels = proximityTolerancePixels ):
        super().__init__(canvas)
        self.canvas = canvas
        self.iface = iface
        #self.start_point = None
        self.marker = self.createMarker()        
        if snapMethod == self.MARKER_SNAPS_TO_LINES:
            self.marker.setIconType(QgsVertexMarker.ICON_CIRCLE)    
        self.snapToMap = snapToMap
        self.snapMethod = snapMethod
        self.proximityTolerancePixels = tolerancePixels
        self.markerIsVisible = False
        self.snappedPoint = None
        
    def reset(self) -> None:
        self.layersLocators.clear() 
        self.activeLayer = None            
        
    '''
    def canvasPressEvent(self, event):
        # Capture the press event from the mouse click 
        self.start_point = self.toMapCoordinates(event.pos())
        print(self.start_point)

    def canvasReleaseEvent(self, event):
        # Handle the release event, let the mouse button off (e.g. move vertex, add vertex etc.)
        if self.start_point:
            end_point = self.toMapCoordinates(event.pos())
            print(end_point)
    '''
 
    def updateLayersLocators(self) -> None:
        ''' Updates the list of  layers of the project at the current moment and 
        assigns a locator to each layer
        '''

        # No need to create locators if snapping is not wanted
        if self.snapMethod == 0:
            return

        if self.behaviour == self.BEHAVIOUR_SHOW_VERTICES_OF_ACTIVE_LAYER:        
            # if we want the marker to show vertices of only the active layer
            layers = []
            if self.canvas.currentLayer() != None:
                layers.append(self.canvas.currentLayer())        
        else:
            # if we want the marker to show vertices of all layers (refers to layers that have been rendered once by setting them as visible on the map, before the tool is activated)
            layers = self.canvas.layers()        
                                
        self.layersLocators.clear()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                locator = QgsPointLocator(layer, QgsProject.instance().crs(), QgsProject.instance().transformContext())
                self.layersLocators.append((layer, locator))
        return            

 
    def canvasMoveEvent(self, event):
    
        # No need to do anything if snapping is not wanted
        if self.snapMethod == 0:
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
            if self.snapMethod == self.MARKER_SNAPS_TO_VERTICES:
                match = layer_locator[1].nearestVertex(mouse_point, tolerance)
            else: 
                match = layer_locator[1].nearestEdge(mouse_point, tolerance)
                
            if match.isValid():             
                if matchFound == False:
                    # for the first valid match
                    matchFound = True
                    edgePoint = match.point()
                    self.marker.setCenter(edgePoint)
                    #print (self.activeLayer.name())
                    #print(f"Nearest edge point in tolerance {tolerance}: {edgePoint.x()}, {edgePoint.y()}")
                    
                # for all layer matches                    
                layerNamesList.append(self.activeLayer.name())

        if matchFound == True:
            self.snappedPoint = edgePoint
            self.marker.setToolTip(",".join(layerNamesList))
            self.marker.show()
            self.markerIsVisible = True 
        else:
            if self.markerIsVisible == True:
                self.marker.hide() 
                self.markerIsVisible = False
                self.snappedPoint = None                
        
        return        
                
                
    def createMarker(self) -> None: 
        marker = QgsVertexMarker(self.canvas)        
        marker.setIconType(QgsVertexMarker.ICON_BOX)
        marker.setColor(self.markerColor)
        marker.setFillColor(self.markerFillColor)
        marker.setIconSize(self.markerIconSize)
        marker.setPenWidth(self.markerPenWidth)        
        marker.hide()
        return  marker  


    def setSnapMethod(self, snapToMap:int, method:int, tolerancePixels = proximityTolerancePixels) -> None:
        self.snapToMap = snapToMap
        self.snapMethod = method
        if self.snapMethod == self.MARKER_SNAPS_TO_LINES:
            self.marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        else:
            self.marker.setIconType(QgsVertexMarker.ICON_BOX)
        self.proximityTolerancePixels = tolerancePixels
        return

        
    def forgetLastSnappedPoint(self) -> None:
        self.snappedPoint = None
        return
    