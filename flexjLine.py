# -*- coding: utf-8 -*-
"""
***************************************************************************
    flexjLine.py
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

Annotations supported since QGIS version 3.16

"""
__author__ = 'Ilias Iliopoulos'
__date__ = 'March 2024'
__copyright__ = '(C) 2024, Ilias Iliopoulos'

from qgis.gui import QgsVertexMarker, QgsRubberBand

try:
    from qgis.core import QgsPointXY, QgsDistanceArea, QgsGeometryUtils, QgsProject, QgsPoint, QgsUnitTypes, QgsAnnotationPointTextItem
except:
    from qgis.core import QgsPointXY, QgsDistanceArea, QgsGeometryUtils, QgsProject, QgsPoint, QgsUnitTypes
    
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import Qt
import math
import os


class FlexjLine:
     
    
    defaultToolColor = QColor(222, 155, 67, 128)
    defaultLineWidth = 3
    defaultLineStyle = Qt.DotLine # enum Qt::PenStyle
    defaultMarkerIconSize = 10
    defaultAnnotationDecimalDigits = 0 
    defaultShowDistance = 0
    defaultShowTotalDistance = 0
    defaultAtAngle = 0
    defaultDistanceUnits = "m"
    defaultKeepBaseUnit = False # set to False to allow conversion of large distances to more suitable units, e.g., meters to kilometers 
    defaultAngleCorrection = 0
    
    defaultMaxNumMarkers = 100

     
    def __init__(self, canvas, iface, maxNumMarkers:int = defaultMaxNumMarkers):
             
        self.canvas = canvas
        self.iface = iface
        self.maxNumMarkers = maxNumMarkers

        self.markers = []            
        self.markerIndex = 0
        
        
        # The dictionary that contains the returned markers in the order they have been set
        self.resultMarkers = {}  # same structure as pointsDict
                
        self.createRubberBand()  
        self.rubberBandActive = False
        # Assign the default parameters
        self.setFlexjLineVisuals()
        
        self.currentMarker = 0
        try:
            self.annotation_layer = QgsProject.instance().mainAnnotationLayer() 
        except:
            self.annotation_layer = None
            self.iface.messageBar().pushMessage("Error", "Annotations are supported only since QGIS version 3.16. Lengths in rubberbands are disabled.", level=Qgis.Warning, duration=5)            
        self.lastAnnotationId = None       
        self.totalLength = 0        
        return        

        
    def reset(self) -> None: 
        self.rubberBand.reset()
        self.destroyMarkers()
        self.markerIndex = 0
        self.currentMarker = 0
        self.markers.clear()
        self.resultMarkers.clear()
        
        if self.annotation_layer is not None:
            self.annotation_layer.reset()        
        self.totalLength = 0
        return        


    def createRubberBand(self):
        self.rubberBand = QgsRubberBand(self.canvas)           
        return       


    def newMarker(self) -> QgsVertexMarker:
        marker = QgsVertexMarker(self.canvas)            
        marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        marker.setColor(self.toolColor)
        marker.setFillColor(self.toolColor)
        marker.setIconSize(self.markerIconSize)
        return marker        
    
    
    def moveEndVertex(self, point):       
                      
        if self.markerIndex > 0 and self.markerIndex < self.maxNumMarkers and self.rubberBandActive == True:
            if self.rubberBand.numberOfVertices() > 1:
                # Move the end of the rubberband following the mouse
                self.rubberBand.removeLastPoint()
                self.rubberBand.addPoint(point)
                
                if self.annotation_layer is not None:               
                    if self.lastAnnotationId is not None :
                        self.annotation_layer.removeItem(self.lastAnnotationId)  
                    if self.markerIndex > 0 and self.showDistance == 1:
                        # Sets the temporary flag to annotations created by the canvasMoveEvent and not by the mouse click
                        self.addDistanceLabel(self.markers[self.markerIndex -1].center(), point, permanent = False)  
                
        return
        
        
    def addRubberBandPoint(self, p):

        if self.markerIndex >= self.maxNumMarkers:
            if self.lastAnnotationId is not None:
                self.annotation_layer.removeItem(self.lastAnnotationId) 
            # Start over after all markers are set
            self.reset()
            self.rubberBandActive = False

        if self.markerIndex == 0:
            ''' First point inserted '''
            self.rubberBandActive = True
            self.reset()
            
        if self.markerIndex < self.maxNumMarkers and self.rubberBandActive == True:       
            self.currentMarker = self.markerIndex
            self.markers.insert(self.currentMarker, self.newMarker())
            self.markers[self.currentMarker].setCenter(p)
            self.markers[self.currentMarker].show()
                           
            if self.rubberBand.numberOfVertices() > 1:
                self.rubberBand.removeLastPoint()  
            self.rubberBand.addPoint(p, doUpdate = True)
            # I must add twice, because the canvasMoveEvent will remove the last point at the next cursor move,
            # but I want to keep it as a rubberband point. I do not want to have resource consuming 
            # checks, so it is easier, although a bit ugly            
            self.rubberBand.addPoint(p, doUpdate = True)
            
            if self.markerIndex > 0 and self.showDistance == 1:  
                # Create a permanent annotation            
                self.addDistanceLabel(self.markers[self.markerIndex -1].center(), p, permanent = True)
                self.totalLength += self.candidateSegmentLength            
            
            self.markerIndex += 1   
            
        return


    def endRubberBand(self) -> None:
        # In case of multiple right clicks, we do not want to erase previous vertices
        if self.rubberBandActive == False:
            return
        # do not create more vertices
        self.rubberBandActive = False          
        if self.rubberBand.numberOfVertices() > 1:
            self.rubberBand.removeLastPoint()         
        # when only the first point has been set             
        if self.markerIndex == 1:
            self.reset()
        # in all cases    
        self.markerIndex = 0           
        if self.lastAnnotationId is not None:
            self.annotation_layer.removeItem(self.lastAnnotationId)  
        return            


    def getMarkerPoints(self):
        self.resultMarkers.clear()
        # If I do not have at least start and end, return an empty dictionary
        if len(self.markers) < 2:
            return {}
            
        for i, marker in enumerate(self.markers):
            if i == 0:
                self.resultMarkers[0] = marker.center()
            elif i == len(self.markers) - 1:
                self.resultMarkers[self.maxNumMarkers - 1] = marker.center()
            else:
                self.resultMarkers[i] = marker.center()        

        self.destroyMarkers()        
        return self.resultMarkers    


    def getMarkerPointList(self):
        result = []
        for marker in self.markers:
             result.append(marker.center())
        return result             

        
    def addDistanceLabel(self, p1:QgsPointXY, p2:QgsPointXY, permanent:bool = False) -> None:  

        pt1 = QgsPoint(p1)
        pt2 = QgsPoint(p2)
        
        # calculate length of line
        d = QgsDistanceArea()
        d.setSourceCrs(QgsProject.instance().crs(), QgsProject.instance().transformContext())
        d.setEllipsoid(QgsProject.instance().crs().ellipsoidAcronym())
        
        # Use length and units of the Project CRS/ellipsoid
        length_in_ellipsoid_units = d.measureLine([p1, p2])
        lengthUnits = d.lengthUnits()
               
        length_in_meters = d.convertLengthMeasurement(length_in_ellipsoid_units, QgsUnitTypes.DistanceMeters)      
        length_in_resultUnits = length_in_meters * QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, self.distanceUnitsQgs)
                
        self.candidateSegmentLength = length_in_ellipsoid_units
        candidatetotalLength = self.totalLength + length_in_ellipsoid_units
        candidatetotalLength_in_meters = d.convertLengthMeasurement(candidatetotalLength, QgsUnitTypes.DistanceMeters)
        candidatetotalLength_in_resultUnits = candidatetotalLength_in_meters * QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, self.distanceUnitsQgs)        
                  
        x, y = self.annotationCoordinates(pt1, pt2)
            
        # add annotation label   
        segmentLengthText = QgsUnitTypes.formatDistance(length_in_resultUnits, self.annotationDecimalDigits, self.distanceUnitsQgs, self.keepBaseUnit)
        totalLengthText = QgsUnitTypes.formatDistance(candidatetotalLength_in_resultUnits, self.annotationDecimalDigits, self.distanceUnitsQgs, self.keepBaseUnit)
        
        if candidatetotalLength != 0 and self.showTotalDistance == 1:
            segmentLengthText = segmentLengthText + " (" + totalLengthText + ")" 

        if self.annotation_layer is not None:          
            label = QgsAnnotationPointTextItem(segmentLengthText, QgsPointXY(x, y))        
            if self.atAngle == 1:
                label.setAngle(self.labelAngle(pt1, pt2))   
            else:
                label.setAngle(0)
           
            if permanent == True:
                self.lastAnnotationId = None
            else:    
                self.lastAnnotationId = self.annotation_layer.addItem(label)
        return
        
        
    def labelAngle(self, pt1:QgsPoint, pt2:QgsPoint) -> float:        
        
        # calculate gradient of line to place label at an angle
        gradient = QgsGeometryUtils.gradient(pt1, pt2)
        # convert gradient to an angle in degrees.
        # NOTICE THE MINUS SIGN in regards to the correction below
        angle = - math.degrees(math.atan(gradient))
        
        # Fit into the clockwise angle notation of the annotation  
        # It seems that QgsAnnotationPointTextItem.setAngle() works differently on Windows 33.32.2-Lima and Linux 3.22.4-Biatowieza
        # Perhaps it is os based. Needs testing        
        #if os.name == "nt":
        if self.angleCorrection:
            angle = -angle
 
        return angle        

        
    def annotationCoordinates(self, pt1:QgsPoint, pt2:QgsPoint):   
        middleX = pt1.x() + (pt2.x() - pt1.x()) * 0.5
        middleY = pt1.y() + (pt2.y() - pt1.y()) * 0.5
        return middleX, middleY        

        
    def destroyMarkers(self) -> None:
        for marker in self.markers:
            if marker in self.iface.mapCanvas().scene().items():
                self.iface.mapCanvas().scene().removeItem(marker)  
                
        self.markers.clear()   
        return            

        
    def setFlexjLineVisuals(self, color:QColor = defaultToolColor, markerSize:int = defaultMarkerIconSize, lineWidth:int = defaultLineWidth, 
                                      lineStyle:int = defaultLineStyle, showDistance:int = defaultShowDistance, atAngle:int = defaultAtAngle, showTotalDistance:int = defaultShowTotalDistance, decimalDigits:int = defaultAnnotationDecimalDigits, 
                                      distanceUnits:str = defaultDistanceUnits, keepBaseUnit:int = defaultKeepBaseUnit,
                                      angleCorrection:int = defaultAngleCorrection) -> None:
        self.toolColor = color
        self.rubberBand.setColor(self.toolColor)

        self.rubberBandWidth = lineWidth
        self.rubberBand.setWidth(self.rubberBandWidth)  
 
        self.rubberBandStyle = lineStyle + 1  # Qt:PenStyle  0:No pen, 1:Solid etc...
        self.rubberBand.setLineStyle(self.rubberBandStyle)  
       
        self.markerIconSize = markerSize
        for marker in self.markers:            
            marker.setColor(self.toolColor)
            marker.setFillColor(self.toolColor)
            marker.setIconSize(self.markerIconSize) 

        self.showDistance = showDistance
        self.atAngle = bool(atAngle)
        self.showTotalDistance = showTotalDistance
        self.annotationDecimalDigits = decimalDigits
        self.distanceUnitsQgs = QgsUnitTypes.decodeDistanceUnit(distanceUnits)[0] if QgsUnitTypes.decodeDistanceUnit(distanceUnits)[1] else QgsUnitTypes.DistanceMeters
        self.keepBaseUnit = bool(keepBaseUnit)
        self.angleCorrection = bool(angleCorrection)