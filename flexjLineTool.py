# -*- coding: utf-8 -*-
"""
***************************************************************************
    flexjLineTool.py
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


    
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
from .vertexTool import MapToolSnapToLayers
from .flexjLine import FlexjLine
#import os


class MapToolFlexjLine(MapToolSnapToLayers):
     
    
    mapToolName = "MapToolFlexjLine"    
    defaultMaxNumMarkers = 100
    
    defaultToolColor = QColor(222, 155, 67, 128)
    defaultLineWidth = 3
    defaultLineStyle = Qt.NoPen # enum Qt::PenStyle. Start with 0 NoPen and the flexjLine class increases by 1 to SolidLine
    defaultMarkerIconSize = 10
    defaultAnnotationDecimalDigits = 0 
    defaultShowDistance = 0
    defaultShowTotalDistance = 0
    defaultAtAngle = 0
    defaultDistanceUnits = "m"
    defaultKeepBaseUnit = False # set to False to allow conversion of large distances to more suitable units, e.g., meters to kilometers 
    defaultAngleCorrection = 0

     
    def __init__(self, canvas, iface, maxNumMarkers:int = defaultMaxNumMarkers):
        super().__init__(canvas, iface)       
        self.canvas = canvas
        self.iface = iface
        self.maxNumMarkers = maxNumMarkers
        
        self.setToolName(self.mapToolName)
        self.setSnappingToolParameters( 
                    snappingBehaviour = self.BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS,
                    snappingMethod = self.MARKER_SNAPS_TO_VERTICES,                
                    snapToMatchedPoint = 1,  
                    tolerancePixels = 12,
                    showToolTip = 1                 
                )

        self.rb = FlexjLine(self.canvas, self.iface, maxNumMarkers = self.maxNumMarkers)
                                    
        self.setFlexjLineToolVisuals()                                    
        return        

        
    def reset(self) -> None: 
        super().reset()
        self.rb.reset()
        return        

    
    def canvasMoveEvent(self, event):       

        super().canvasMoveEvent(event)
        mousePoint = self.toMapCoordinates(event.pos())
              
        # Implement the snapping functionality for the dynamic movement of the mouse
        p = self.conditionalOffsetToSnappedPoint(mousePoint)                
        self.rb.moveEndVertex(p)                  
        return
        
        
    def addRubberBandPoint(self, p):
        self.rb.addRubberBandPoint(p)           
        return


    def endRubberBand(self) -> None:
        self.rb.endRubberBand()
        return            


    def getMarkerPoints(self):
        return  self.rb.getMarkerPoints()  

  
    def setFlexjLineToolVisuals(self, color:QColor = defaultToolColor, markerSize:int = defaultMarkerIconSize, lineWidth:int = defaultLineWidth, 
                                      lineStyle:int = defaultLineStyle, showDistance:int = defaultShowDistance, atAngle:int = defaultAtAngle, 
                                      showTotalDistance:int = defaultShowTotalDistance, decimalDigits:int = defaultAnnotationDecimalDigits, 
                                      distanceUnits:str = defaultDistanceUnits, keepBaseUnit:int = defaultKeepBaseUnit,
                                      angleCorrection = defaultAngleCorrection) -> None:

        self.toolColor = color
        self.markerIconSize = markerSize        
        self.lineWidth = lineWidth 
        self.lineStyle = lineStyle        
        self.showDistance = showDistance
        self.atAngle = atAngle
        self.showTotalDistance = showTotalDistance        
        self.annotationDecimalDigits = decimalDigits
        self.distanceUnits = distanceUnits
        self.keepBaseUnit = bool(keepBaseUnit)
        self.angleCorrection = bool(angleCorrection)        
               
        self.rb.setFlexjLineVisuals(color = self.toolColor, markerSize = self.markerIconSize, lineWidth = self.lineWidth, 
                                      lineStyle = self.lineStyle, showDistance = self.showDistance, atAngle = self.atAngle, showTotalDistance = self.showTotalDistance, decimalDigits = self.annotationDecimalDigits, 
                                      distanceUnits = self.distanceUnits, keepBaseUnit = self.keepBaseUnit, angleCorrection = self.angleCorrection)
        return                              
        


