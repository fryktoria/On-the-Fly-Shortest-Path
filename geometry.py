# -*- coding: utf-8 -*-
"""
***************************************************************************
    geometry.py
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

from qgis.core import ( QgsDistanceArea,
                        QgsCoordinateReferenceSystem,
                        QgsPointXY,                        
                        QgsProject,
                        QgsUnitTypes
                      )
class OtFSP_Geometry:    
                   
    #Conversion factor from meters to units in the following order  ["m", "Km", "y", "ft", "NM", "mi"]
    conversionFactor = [1, 0.001, 1.0936132983377078, 3.280839895013123, 0.0005399568034557236, 0.0006213711922373339]                       

    def distanceP2P(self, crs:QgsCoordinateReferenceSystem, p1:QgsPointXY, p2:QgsPointXY) -> float:
        ''' Returns the distance between two points. Distance is returned in meters, since ellipsoidal calculation is set by setting the ellipsoid '''
        d = QgsDistanceArea()
        d.setSourceCrs(crs, QgsProject.instance().transformContext())
        d.setEllipsoid(crs.ellipsoidAcronym())
        distance = d.measureLine([p1, p2]) 
        return distance


    def convertDistanceUnits(self, value:float, index:int) -> float:
        ''' Converts a distance from meters to any of the allowed units, or the same value if the index is not recognized
            The index is expected to be the index in lists self.resultUnitsList[] and self.conversionFactor[]        '''
        if index < 0:
            return value
        else:
            return value * self.conversionFactor[index]

    def lengthInMeters(self, length:float, crs:QgsCoordinateReferenceSystem) -> float:
        ''' Converts a distance from a crs unit to meters'''
        try:
            d = QgsDistanceArea()
            d.setSourceCrs(crs, QgsProject.instance().transformContext())
            # I do not use d.setEllipsoid(crs.ellipsoidAcronym()) because setting the ellipsoid defines an ellipsoidal rather than 
            # a cartesian distance measurement and sets the length unit to meters.           
            # After QGIS 3.30 
            # length = d.convertLengthMeasurement(length, QgsUnitTypes.DistanceUnit.DistanceMeters)  
            # Before QGIS 3.30 works also after 3.30. 
            length_meters = d.convertLengthMeasurement(length, QgsUnitTypes.DistanceMeters)
            return  length_meters   
        except:
            return -1        
                       
                       
    def crsDetails(self, crs:QgsCoordinateReferenceSystem) -> list: # list of strings  [ellipsoid, EPSG, CRS_description, Units] 
        ''' Returns a list of valuable data regarding the measurements of the CRS '''
        '''Be protective in case a transformation is not possible '''
        try:
            d = QgsDistanceArea()
            d.setSourceCrs(crs, QgsProject.instance().transformContext())
            d.setEllipsoid(crs.ellipsoidAcronym())              
            return [d.ellipsoid(), d.sourceCrs().authid(), d.sourceCrs().description(), QgsUnitTypes.toString(d.lengthUnits())]    
        except:
            return ["?", "?", "?", "?"]

            
    def crsDistanceUnits(self, crs:QgsCoordinateReferenceSystem) -> str:
        ''' Returns the distance units of a CRS, in human readable format '''
        if crs is None:
            return "Undefined"
        else:
            return QgsUnitTypes.toString(crs.mapUnits())               

            
           