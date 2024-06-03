from qgis.PyQt.QtWidgets import QDialog

#from .ui_DlgDockWidget import Ui_mDockWidget
from .ui_DlgConfiguration import Ui_configuration_form
from .ui_DlgResults import Ui_resultDialog
from .ui_DlgResultsNoFiber import Ui_resultDialogNoFiber
from .ui_DlgLayerSelection import Ui_layersDialog
from .ui_DlgMarkerCoordinates import Ui_coordinatesDialog


'''
class DockWidgetDialog(QDialog, Ui_mDockWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
'''        
        
class ConfigurationDialog(QDialog, Ui_configuration_form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)        

class ResultsDialog(QDialog, Ui_resultDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
class ResultsNoFiberDialog(QDialog, Ui_resultDialogNoFiber):
    def __init__(self):
        super().__init__()
        self.setupUi(self)        
        
class LayerSelectionDialog(QDialog, Ui_layersDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)   


class MarkerCoordinatesDialog(QDialog, Ui_coordinatesDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)           