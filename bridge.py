# -*- coding: utf-8 -*-
"""
***************************************************************************
    bridge.py
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


from qgis.core import QgsPointXY, QgsProject, QgsVectorLayer, QgsCoordinateTransform, QgsFeature, QgsFeatureRequest, QgsGeometry, QgsSpatialIndex , QgsCoordinateReferenceSystem, QgsUnitTypes
# import math for debugging to show distances instead of squared distances. Comment at production
#import math

# for debugging
from .geometry import OtFSP_Geometry
import math

''' 
Uses point layers as bridges between line layers, to provide ability for the path to cross the gap and pass from one layer to another
'''

class BridgeLayer:

    maximumNumberOfNeighbors = 5 # A bridge point searches a max of maximumNumberOfNeighbors line segments around it

    def __init__(self, iface):
        self.iface = iface
        self.bridgePointTolerance = 0 
        self.bridgeLineTolerance = 0        
        return


    def setLayers(self, pointLayers, mergedLayer:QgsVectorLayer, storeOriginalLayerInfo:bool = False) -> None:
        self.pointLayers = pointLayers
        self.mergedLayer = mergedLayer
         
        self.storeOriginalLayerInfo = storeOriginalLayerInfo 
        if storeOriginalLayerInfo == True:
            #print ("Will not allow same layer bridging")
            pass            
        else:
            #print ("Will ALLOW same layer bridging")
            pass
        return


    def setTolerance(self, bridgePointTolerance:float = 0, bridgeLineTolerance:float = 0):
        # input is directly in map units
        self.bridgePointTolerance = bridgePointTolerance 
        self.bridgeLineTolerance = bridgeLineTolerance
        #print ("Setting tolerances to ", bridgePointTolerance, bridgeLineTolerance) 
        return
    
        
    def createBridges(self):
        
        # A list to remember a layer for which a vertex has been created in the merged layer during the analysis of the nearest points of a bridge point
        connectedOriginalLayers = []
        
        # Create a spatial index object
        provider = self.mergedLayer.dataProvider()
        spIndex = QgsSpatialIndex()  
        
        # Insert features into the spatial index
        feature = QgsFeature()
        features = provider.getFeatures()
        while features.nextFeature(feature):
            spIndex.addFeature(feature)
                
        self.mergedLayer.startEditing()
        self.geom = OtFSP_Geometry()
        #For each point layer
        for index, pointLayer in enumerate(self.pointLayers): 
            #print ("Bridge index ", index)
            #print("layer ", pointLayer)
            if index == 0:
                # First layer is expected to be the layer of the markers of the bridging line tool,
                # for the purpose of bveing handled with a different tolerance.
                # If the bridging line tool has not been used, the layer will be None
                if pointLayer is None:
                    #print("Point layer is none. Continue")
                    continue
                tolerance = self.bridgeLineTolerance
                #print ("Setting tolerance to line layer ", tolerance)
            else:
                tolerance = self.bridgePointTolerance
                
            # Some local variables to avoid expensive system calls
            # Not really a significant optimization for on-the-fly created points but could help in big point layers
            sourceCrs = pointLayer.sourceCrs()
            targetCrs = self.mergedLayer.crs()
            reprojectCrs = False
            if sourceCrs != targetCrs:
                reprojectCrs = True
                try:
                    tr = QgsCoordinateTransform(sourceCrs, targetCrs, QgsProject.instance().transformContext())
                except:
                    self.iface.messageBar().pushMessage("Error", "Coordinate transformation of bridge point layer failed. Skipping layer.", level=Qgis.Critical, duration=10)
                    continue
    
            for feature in pointLayer.getFeatures(QgsFeatureRequest().setNoAttributes()):

                #print(f"Checking point: {feature.geometry().asPoint().x()}, {feature.geometry().asPoint().y()}") 
                # Transform to project CRS because below I will transform the tolerance in project units
                # I do point by point to avoid hogging up the memory with another memory layer or point list
                if reprojectCrs == True:                
                    trPoint = tr.transform(feature.geometry().asPoint()) 
                else:
                    trPoint = feature.geometry().asPoint()                
                #print (f"Reprojected point : {trPoint.x()} , {trPoint.y()}")                
                
                # Retrieve the nearest line feature IDs (you can adjust the number of neighbors as needed). According to the documentation,
                # nearestNeighbor() may return more features than requested, so I need to recheck the distance for each one
                nearestIds = spIndex.nearestNeighbor(trPoint, self.maximumNumberOfNeighbors, maxDistance = tolerance)  # Get the max n nearest neighbors
                #print ("Nearest line feature IDs ", nearestIds, " within tolerance ", tolerance, " (in meters) ", self.geom.lengthInMeters(tolerance, self.mergedLayer.crs()))
                
                  

                # A new list to store the filtered result lists [squaredDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment] because I need to process based on some of their parameters
                filteredNearestIds = []
                for lineId in nearestIds:
                    # Get the actual QgsFeature object corresponding to the feature ID
                    nearestFeature = QgsFeature()
                    self.mergedLayer.getFeatures(QgsFeatureRequest().setFilterFid(lineId)).nextFeature(nearestFeature)
                    #print (f"Id of nearest feature {nearestFeature.id()}")
                    nearestGeometry = nearestFeature.geometry()
                    # Need to set the epsilon to a very low value in order to cope with CRSs in degrees
                    # Without this setting, when the point is close to the line (e.g. 2-5 meters), the function below returns zero distance!
                    # Note: the squareDist below is based on Cartesian calculation. I should write a note on the configuration dialog!
                    [squaredDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment] = nearestGeometry.closestSegmentWithContext(trPoint, epsilon = 0.000000000001)
                    # uncomment import math to use the print() below
                    #print (f"lineId {lineId} squaredDist {squaredDist} dist in m {self.geom.lengthInMeters(math.sqrt(squaredDist), self.mergedLayer.crs())} point {minDistPoint}   nextVertexIndex {nextVertexIndex} leftOrRightOfSegment {leftOrRightOfSegment}")
                    
                    # avoid empty geometries
                    if minDistPoint.isEmpty():
                        #print ("Empty geometry. Skipping feature")
                        continue

                    #if math.sqrt(squaredDist) > tolerance: 
                    if squaredDist > (tolerance * tolerance): # to avoid import math just for the square root
                        #print ("Distance outside tolerance.")
                        continue                    
                        
                    # This situation occurs when the line involved is the bridge line itself, so the vertex is on the line, or when the vertex is snapped on a line.
                    # Keep the line.
                    if index == 0 and leftOrRightOfSegment == 0:
                        #print ("Right on top of line")
                        pass
                                         
                    if self.storeOriginalLayerInfo == True:                
                        filteredNearestIds.append([lineId, squaredDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment, nearestFeature["layerno"]])
                    else:    
                        filteredNearestIds.append([lineId, squaredDist, minDistPoint, nextVertexIndex, leftOrRightOfSegment, -1])

                # Sort the list to get the minimum distance element first
                filteredNearestIds.sort(key = lambda x: x[1]) # 1 element of the result list is squaredDist
                #print ("filteredNearestIds ", filteredNearestIds)

                connectedOriginalLayers.clear()
                for element in filteredNearestIds:
                    
                    lineId = element[0]
                    squaredDist = element[1]
                    minDistPoint = element[2]
                    nextVertexIndex = element[3]
                    leftOrRightOfSegment = element[4]
                    layerNo = element[5]
                    
                    vertexInserted = False
                    if self.storeOriginalLayerInfo == True:
                        # Avoid same layer bridging
                        
                        #print ("No same layer bridging: nearest connected layer number ", layerNo)
                        if layerNo not in connectedOriginalLayers:
                            #print(f"No same layer bridging: Inserting vertex at point {minDistPoint} of lineId {lineId} nextVertexIndex {nextVertexIndex}")
                            self.mergedLayer.insertVertex(minDistPoint.x(), minDistPoint.y(), lineId, nextVertexIndex)
                            vertexInserted = True
                            connectedOriginalLayers.append(layerNo)
                        else:
                            #print ("Will not insert another vertex to layer ",  layerNo)
                            vertexInserted = False
                            
                    else:  
                        # Implement same layer bridging 
                        #print (f"Same layer bridging: Inserting vertex at point {minDistPoint} of layer {layerNo} lineId {lineId} nextVertexIndex {nextVertexIndex}")
                        self.mergedLayer.insertVertex(minDistPoint.x(), minDistPoint.y(), lineId, nextVertexIndex)
                        vertexInserted = True 
                                                
                    if vertexInserted == True and minDistPoint != trPoint:                               
                        # Create a line connecting two points in the merged layer. Do not create lines of zero length
                        #print (f"Create a line connecting in the merged layer point {trPoint} to point {minDistPoint}")
                        if self.storeOriginalLayerInfo == True:
                            self.createLineFeature(self.mergedLayer, trPoint, minDistPoint, nearestFeature["layerno"])                        
                        else:    
                            self.createLineFeature(self.mergedLayer, trPoint, minDistPoint)
                        
        self.mergedLayer.endEditCommand()
        self.mergedLayer.commitChanges()    
        return
        
        
    def createLineFeature(self, layer:QgsVectorLayer, point1:QgsPointXY, point2:QgsPointXY, layerno:int = -1) -> None:
        ''' Creates a line between two points and adds the line to the layer ''' 

        feature = QgsFeature()
        feature.setFields(layer.fields())
        if self.storeOriginalLayerInfo == True:
            # Use layerno, so in case same layer bridging is not allowed, to avoid next bridge points to create a line to the newly created line 
            # Perhaps not necessary because the new lines were not existing in the spatial index, but just in case the index is somehow rebuilt
            feature.setAttribute("layerno", layerno)
            
        feature.setGeometry(QgsGeometry.fromPolylineXY([point1, point2]))    
        layer.addFeature(feature)   
            
        return
        
        
