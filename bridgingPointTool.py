# -*- coding: utf-8 -*-
"""
***************************************************************************
    bridgingPointTool.py
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


from qgis.core import QgsPointXY, QgsCoordinateTransform, QgsProject , QgsCoordinateReferenceSystem
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsVertexMarker
from .vertexTool import MapToolSnapToLayers

'''
Creates a list of markers at selected points. The list will be used to create a layer of bridge points,
by accessing the self.markers[] list
'''

class BridgingPointTool(MapToolSnapToLayers):
     
    
    mapToolName = "BridgingPointTool"
    # map tool visual settings
    markerIconType = QgsVertexMarker.ICON_CIRCLE 
    markerColor = QColor(255, 0, 0, 128)
    markerIconSize = 10
    markerFillColor = QColor(255, 0, 0, 128)
    markerPenWidth = 2 # Not user modifiable

     
    def __init__(self, canvas, iface):
        super().__init__(canvas, iface)       
        self.canvas = canvas
        self.iface = iface        
        self.setToolName(self.mapToolName)
        self.setSnappingToolParameters( 
                    snappingBehaviour = self.BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS,
                    snappingMethod = self.MARKER_SNAPS_TO_VERTICES,                
                    snapToMatchedPoint = 1,  
                    tolerancePixels = 12,
                    showToolTip = 1                 
                )
                
        self.markers = []
        self.originalCrs = QgsProject.instance().crs()   
        return        


    def reset(self) -> None: 
        super().reset()
        self.removeVertexMarkers() 
        self.markers.clear()
        return        

    
    def createBridgeMarker(self) -> QgsVertexMarker: 
        marker = QgsVertexMarker(self.canvas)        
        marker.setIconType(self.markerIconType)
        marker.setColor(self.markerColor)
        marker.setFillColor(self.markerFillColor)
        marker.setIconSize(self.markerIconSize)
        marker.setPenWidth(self.markerPenWidth)         
        return  marker  
   
        
    def addBridgingPoint(self, point:QgsPointXY) -> None:
        # Remember the last project crs where a marker was created
        self.originalCrs = QgsProject.instance().crs()
        newMarker = self.createBridgeMarker()
        newMarker.setCenter(point)
        newMarker.show()
        self.markers.append(newMarker)  
        return
        

    def removeVertexMarkers(self) -> None:
        for marker in self.markers:
            if marker in self.iface.mapCanvas().scene().items():
                self.iface.mapCanvas().scene().removeItem(marker)  
                
        self.markers.clear()        
        return  


    def markersAsPointsXY(self): # -> List[QgsPointXY]:
        markerPoints = []
        for marker in self.markers:
            markerPoints.append(marker.center())
        return markerPoints    
        

    def changeCrs(self, newCrs:QgsCoordinateReferenceSystem) -> None:
    
        if self.originalCrs == newCrs:
            return
        try:    
            xform = QgsCoordinateTransform(self.originalCrs, newCrs, QgsProject.instance())
            for marker in self.markers: 
                marker.setCenter(xform.transform(marker.center()))
        except:
            self.iface.messageBar().pushMessage("Error", "Coordinate transformation of bridging markers failed", level=Qgis.Critical, duration=5)

        self.originalCrs = newCrs            
        return

        
    def setBridgingPointToolVisuals(self, markerColor:QColor, markerSize:int) -> None:      
        self.markerColor = markerColor        
        self.markerFillColor = markerColor 
        self.markerSize = markerSize        
        for marker in self.markers:
            marker.setColor(self.markerColor)
            marker.setFillColor(self.markerColor)
            marker.setIconSize(self.markerIconSize)
        return    
