# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'DlgResultsNoFiber.ui'
#
# Created by: PyQt5 UI code generator 5.15.6
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


#from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt import QtCore, QtGui, QtWidgets


class Ui_resultDialogNoFiber(object):
    def setupUi(self, resultDialog):
        resultDialog.setObjectName("resultDialog")
        resultDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        resultDialog.resize(230, 170)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(resultDialog.sizePolicy().hasHeightForWidth())
        resultDialog.setSizePolicy(sizePolicy)
        resultDialog.setMinimumSize(QtCore.QSize(230, 170))
        resultDialog.setMaximumSize(QtCore.QSize(230, 170))
        resultDialog.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        resultDialog.setModal(True)
        self.OkButton = QtWidgets.QPushButton(resultDialog)
        self.OkButton.setGeometry(QtCore.QRect(80, 96, 75, 23))
        self.OkButton.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.OkButton.setObjectName("OkButton")
        self.entryCostUnits = QtWidgets.QLabel(resultDialog)
        self.entryCostUnits.setGeometry(QtCore.QRect(185, 7, 26, 16))
        self.entryCostUnits.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.entryCostUnits.setObjectName("entryCostUnits")
        self.onGraphCostUnits = QtWidgets.QLabel(resultDialog)
        self.onGraphCostUnits.setGeometry(QtCore.QRect(185, 27, 26, 16))
        self.onGraphCostUnits.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.onGraphCostUnits.setObjectName("onGraphCostUnits")
        self.exitCostUnits = QtWidgets.QLabel(resultDialog)
        self.exitCostUnits.setGeometry(QtCore.QRect(185, 47, 26, 16))
        self.exitCostUnits.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.exitCostUnits.setObjectName("exitCostUnits")
        self.totalCostUnits = QtWidgets.QLabel(resultDialog)
        self.totalCostUnits.setGeometry(QtCore.QRect(185, 72, 26, 16))
        self.totalCostUnits.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.totalCostUnits.setObjectName("totalCostUnits")
        self.totalCostTxt = QtWidgets.QLineEdit(resultDialog)
        self.totalCostTxt.setGeometry(QtCore.QRect(80, 70, 100, 20))
        self.totalCostTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.totalCostTxt.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.totalCostTxt.setReadOnly(True)
        self.totalCostTxt.setObjectName("totalCostTxt")
        self.label_4 = QtWidgets.QLabel(resultDialog)
        self.label_4.setGeometry(QtCore.QRect(10, 72, 51, 16))
        self.label_4.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.label_4.setObjectName("label_4")
        self.line = QtWidgets.QFrame(resultDialog)
        self.line.setGeometry(QtCore.QRect(10, 60, 197, 16))
        self.line.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.label_2 = QtWidgets.QLabel(resultDialog)
        self.label_2.setGeometry(QtCore.QRect(10, 47, 51, 16))
        self.label_2.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(resultDialog)
        self.label_3.setGeometry(QtCore.QRect(10, 7, 61, 16))
        self.label_3.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.label_3.setObjectName("label_3")
        self.label = QtWidgets.QLabel(resultDialog)
        self.label.setGeometry(QtCore.QRect(10, 27, 71, 16))
        self.label.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.label.setObjectName("label")
        self.exitCostTxt = QtWidgets.QLineEdit(resultDialog)
        self.exitCostTxt.setGeometry(QtCore.QRect(80, 45, 100, 20))
        self.exitCostTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.exitCostTxt.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.exitCostTxt.setReadOnly(True)
        self.exitCostTxt.setObjectName("exitCostTxt")
        self.entryCostTxt = QtWidgets.QLineEdit(resultDialog)
        self.entryCostTxt.setGeometry(QtCore.QRect(80, 5, 100, 20))
        self.entryCostTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.entryCostTxt.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.entryCostTxt.setReadOnly(True)
        self.entryCostTxt.setObjectName("entryCostTxt")
        self.costOnGraphTxt = QtWidgets.QLineEdit(resultDialog)
        self.costOnGraphTxt.setGeometry(QtCore.QRect(80, 25, 100, 20))
        self.costOnGraphTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.costOnGraphTxt.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.costOnGraphTxt.setReadOnly(True)
        self.costOnGraphTxt.setObjectName("costOnGraphTxt")
        self.label_5 = QtWidgets.QLabel(resultDialog)
        self.label_5.setGeometry(QtCore.QRect(4, 142, 53, 16))
        self.label_5.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.label_5.setObjectName("label_5")
        self.ellipsoidTxt = QtWidgets.QLabel(resultDialog)
        self.ellipsoidTxt.setGeometry(QtCore.QRect(56, 142, 235, 16))
        self.ellipsoidTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.ellipsoidTxt.setObjectName("ellipsoidTxt")
        self.label_6 = QtWidgets.QLabel(resultDialog)
        self.label_6.setGeometry(QtCore.QRect(4, 126, 55, 16))
        self.label_6.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.label_6.setObjectName("label_6")
        self.crsTxt = QtWidgets.QLabel(resultDialog)
        self.crsTxt.setGeometry(QtCore.QRect(56, 126, 235, 16))
        self.crsTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.crsTxt.setObjectName("crsTxt")
        self.errorTxt = QtWidgets.QLabel(resultDialog)
        self.errorTxt.setGeometry(QtCore.QRect(114, 120, 109, 39))
        self.errorTxt.setLocale(QtCore.QLocale(QtCore.QLocale.C, QtCore.QLocale.AnyCountry))
        self.errorTxt.setObjectName("errorTxt")

        self.retranslateUi(resultDialog)
        QtCore.QMetaObject.connectSlotsByName(resultDialog)
        resultDialog.setTabOrder(self.OkButton, self.entryCostTxt)
        resultDialog.setTabOrder(self.entryCostTxt, self.costOnGraphTxt)
        resultDialog.setTabOrder(self.costOnGraphTxt, self.exitCostTxt)
        resultDialog.setTabOrder(self.exitCostTxt, self.totalCostTxt)

    def retranslateUi(self, resultDialog):
        _translate = QtCore.QCoreApplication.translate
        resultDialog.setWindowTitle(_translate("resultDialog", "Results"))
        self.OkButton.setText(_translate("resultDialog", "Ok"))
        self.entryCostUnits.setText(_translate("resultDialog", "TextLabel"))
        self.onGraphCostUnits.setText(_translate("resultDialog", "TextLabel"))
        self.exitCostUnits.setText(_translate("resultDialog", "TextLabel"))
        self.totalCostUnits.setText(_translate("resultDialog", "TextLabel"))
        self.label_4.setText(_translate("resultDialog", "Total"))
        self.label_2.setText(_translate("resultDialog", "Exit"))
        self.label_3.setText(_translate("resultDialog", "Entry"))
        self.label.setText(_translate("resultDialog", "Οn path"))
        self.label_5.setText(_translate("resultDialog", "Ellipsoid:"))
        self.ellipsoidTxt.setText(_translate("resultDialog", "TextLabel"))
        self.label_6.setText(_translate("resultDialog", "CRS:"))
        self.crsTxt.setText(_translate("resultDialog", "TextLabel"))
        self.errorTxt.setText(_translate("resultDialog", "Message"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    resultDialog = QtWidgets.QDialog()
    ui = Ui_resultDialogNoFiber()
    ui.setupUi(resultDialog)
    resultDialog.show()
    sys.exit(app.exec_())
