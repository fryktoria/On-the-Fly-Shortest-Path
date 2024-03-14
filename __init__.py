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
"""


def classFactory(iface):
    from .onthefly_shortest_path import OnTheFlyShortestPath
    return OnTheFlyShortestPath(iface)
    
