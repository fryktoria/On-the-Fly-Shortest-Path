# -*- coding: utf-8 -*-
"""
***************************************************************************
    bridgingLineTool.py
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
from qgis.core import QgsPointXY
from .vertexTool import MapToolSnapToLayers
from .flexjLine import FlexjLine


class BridgingLineTool(MapToolSnapToLayers):
     
    
    mapToolName = "MapToolBridgingLine"
    defaultMaxNumMarkers = 100
    
    defaultToolColor = QColor(12, 0, 255, 128)
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
        self.numMarkers = maxNumMarkers        
        self.rubberBands = []
        self.activeRubberBand = None     
        self.setToolName(self.mapToolName)
        self.setSnappingToolParameters( 
                    snappingBehaviour = self.BEHAVIOUR_SHOW_VERTICES_OF_ALL_LAYERS,
                    snappingMethod = self.MARKER_SNAPS_TO_VERTICES,                
                    snapToMatchedPoint = 1,  
                    tolerancePixels = 12,
                    showToolTip = 1                 
                )
        # Although there are no rubberbands, I run this to set the self.parameters        
        self.setBridgingLineToolVisuals()       
        return        


    def reset(self) -> None: 
        super().reset()
        for rb in self.rubberBands:
            rb.reset()
        return        


    def newRubberBand(self):
        rb = FlexjLine(self.canvas, self.iface, maxNumMarkers = self.numMarkers)
                                                                        
        rb.setFlexjLineVisuals(color = self.toolColor, markerSize = self.markerIconSize, lineWidth = self.lineWidth, 
                                      lineStyle = self.lineStyle, showDistance = self.showDistance, atAngle = self.atAngle, showTotalDistance = self.showTotalDistance, decimalDigits = self.annotationDecimalDigits, 
                                      distanceUnits = self.distanceUnits, keepBaseUnit = self.keepBaseUnit, angleCorrection = self.angleCorrection)
        self.rubberBands.append(rb)
        return rb       

    
    def addVertex(self, point:QgsPointXY):
        if self.activeRubberBand is None:
            self.activeRubberBand = self.newRubberBand()    
        self.activeRubberBand.addRubberBandPoint(point)
        return

    # Returns -1 to show to calling function that we are not ending a current rubberband, so a delete all bridging lines can take place
    def finishRubberBand(self) -> None:
        if self.activeRubberBand is not None:
            self.activeRubberBand.endRubberBand()
            self.activeRubberBand = None
            return 0
        else:
            #self.reset()        
            return  -1  

        
    def canvasMoveEvent(self, event):       

        super().canvasMoveEvent(event)
        mousePoint = self.toMapCoordinates(event.pos())
        
        #snapping functionality for the dynamic movement of the mouse
        p = self.conditionalOffsetToSnappedPoint(mousePoint) 

        if self.activeRubberBand is not None:        
            self.activeRubberBand.moveEndVertex(p)                  
        return


    def markerPointsList(self):
        ''' 
        Returns a list of all points that compose the flexjLines. The points are in random order 
        and duplicates may be found
        '''
        result = []
        for rb in self.rubberBands:
            rbPoints = list(rb.getMarkerPointList())
            for p in rbPoints:
                result.append(p)  
        return result 

                        
    def lineVerticesList(self):
        ''' 
        Returns a list of lists, where each internal list contains the markers of each flexjLine.
        The result can be used to reconstruct a layer of lines, using the vertex points 
        '''
        result = []
        for rb in self.rubberBands:
            result.append(list(rb.getMarkerPointList()))
        return result
  

    def setBridgingLineToolVisuals(self, color:QColor = defaultToolColor, markerSize:int = defaultMarkerIconSize, lineWidth:int = defaultLineWidth, 
                                      lineStyle:int = defaultLineStyle, showDistance:int = defaultShowDistance, atAngle:int = defaultAtAngle, showTotalDistance:int = defaultShowTotalDistance, decimalDigits:int = defaultAnnotationDecimalDigits, 
                                      distanceUnits:str = defaultDistanceUnits, keepBaseUnit:int = defaultKeepBaseUnit, angleCorrection:int = defaultAngleCorrection):
       
        self.toolColor = color
        self.markerIconSize = markerSize
        self.lineWidth = lineWidth
        self.lineStyle = lineStyle       
        self.showDistance = showDistance
        self.atAngle = atAngle
        self.showTotalDistance = showTotalDistance
        self.annotationDecimalDigits = decimalDigits
        self.distanceUnits = distanceUnits
        self.keepBaseUnit = keepBaseUnit
        self.angleCorrection = angleCorrection 
        for rb in self.rubberBands:
            rb.setFlexjLineVisuals(color = self.toolColor, markerSize = self.markerIconSize, lineWidth = self.lineWidth, 
                                      lineStyle = self.lineStyle, showDistance = self.showDistance, atAngle = self.atAngle, showTotalDistance = self.showTotalDistance, decimalDigits = self.annotationDecimalDigits, 
                                      distanceUnits = self.distanceUnits, keepBaseUnit = self.keepBaseUnit, angleCorrection = self.angleCorrection)    
