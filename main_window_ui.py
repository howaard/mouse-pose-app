# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)
        MainWindow.setMinimumSize(QSize(1024, 768))
        MainWindow.setStyleSheet(u"/* --- Main Window Style --- */\n"
"QWidget#MainWindow, QWidget#scrollAreaWidgetContents {\n"
"	background-color: #191C2C;\n"
"	color: white;\n"
"}\n"
"QScrollArea#scrollArea {\n"
"    border: none;\n"
"}\n"
"\n"
"/* --- Section Titles --- */\n"
"QLabel#importRunLabel, QLabel#resultsLabel, QLabel#visualizeLabel {\n"
"	font-size: 18px;\n"
"	font-weight: bold;\n"
"	color: #E0E0E0;\n"
"	padding: 5px;\n"
"	border-bottom: 2px solid #2D3748;\n"
"}\n"
"\n"
"/* --- Info Labels --- */\n"
"QLabel#projectPathLabel {\n"
"	font-size: 14px;\n"
"	color: #718096;\n"
"}\n"
"QLabel#inputChosenLabel {\n"
"	font-size: 14px;\n"
"	color: #A0AEC0;\n"
"}\n"
"\n"
"/* --- List Widget for Imports --- */\n"
"QListWidget {\n"
"	background-color: #111527;\n"
"	border: 2px solid #2D3748;\n"
"	border-radius: 10px;\n"
"	font-size: 14px;\n"
"	color: #E0E0E0;\n"
"}\n"
"QListWidget::item {\n"
"	padding: 8px;\n"
"}\n"
"QListWidget::item:selected {\n"
"	background-color: #5A67D8;\n"
"	color: white;\n"
"}\n"
"\n"
"/* --- Buttons --- */\n"
"QPushBut"
                        "ton {\n"
"	background-color: #4A5580;\n"
"	color: white;\n"
"	border: none;\n"
"	border-radius: 8px;\n"
"	padding: 10px;\n"
"	font-size: 14px;\n"
"	font-weight: bold;\n"
"}\n"
"QPushButton:hover {\n"
"	background-color: #5A67D8;\n"
"}\n"
"QPushButton#poseButton {\n"
"	background-color: #5A67D8;\n"
"	font-size: 16px;\n"
"}\n"
"QPushButton#poseButton:hover {\n"
"	background-color: #4C58B8;\n"
"}\n"
"QPushButton#poseButton:disabled {\n"
"	background-color: #2D3748;\n"
"	color: #718096;\n"
"}\n"
"\n"
"/* --- Separator Line --- */\n"
"QFrame#line {\n"
"    border: 1px solid #2D3748;\n"
"}\n"
"\n"
"/* --- Log Output --- */\n"
"QPlainTextEdit#logOutput {\n"
"    background-color: #111527;\n"
"    border: 1px solid #2D3748;\n"
"    border-radius: 5px;\n"
"    color: #E0E0E0;\n"
"    font-family: Consolas, monospaced;\n"
"}\n"
"\n"
"/* --- Visualize Section --- */\n"
"QComboBox {\n"
"    background-color: #2D3748;\n"
"    border: 1px solid #4A5580;\n"
"    border-radius: 5px;\n"
"    padding: 5px;\n"
"    color: #E0E0E"
                        "0;\n"
"}\n"
"QComboBox::drop-down {\n"
"    subcontrol-origin: padding;\n"
"    subcontrol-position: top right;\n"
"    width: 15px;\n"
"    border-left-width: 1px;\n"
"    border-left-color: #4A5580;\n"
"    border-left-style: solid;\n"
"    border-top-right-radius: 3px;\n"
"    border-bottom-right-radius: 3px;\n"
"}\n"
"QComboBox QAbstractItemView {\n"
"    background-color: #2D3748;\n"
"    border: 1px solid #4A5580;\n"
"    selection-background-color: #5A67D8;\n"
"}\n"
"\n"
"/* --- Player Controls --- */\n"
"QLabel#timeLabel {\n"
"    color: #A0AEC0;\n"
"}")
        self.verticalLayout_4 = QVBoxLayout(MainWindow)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.scrollArea = QScrollArea(MainWindow)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 1178, 953))
        self.verticalLayout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.projectPathLabel = QLabel(self.scrollAreaWidgetContents)
        self.projectPathLabel.setObjectName(u"projectPathLabel")

        self.verticalLayout.addWidget(self.projectPathLabel)

        self.importRunBox = QGroupBox(self.scrollAreaWidgetContents)
        self.importRunBox.setObjectName(u"importRunBox")
        self.verticalLayout_2 = QVBoxLayout(self.importRunBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.importRunLabel = QLabel(self.importRunBox)
        self.importRunLabel.setObjectName(u"importRunLabel")

        self.verticalLayout_2.addWidget(self.importRunLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.importListWidget = QListWidget(self.importRunBox)
        self.importListWidget.setObjectName(u"importListWidget")

        self.horizontalLayout.addWidget(self.importListWidget)

        self.controlsLayout = QVBoxLayout()
        self.controlsLayout.setObjectName(u"controlsLayout")
        self.importButton = QPushButton(self.importRunBox)
        self.importButton.setObjectName(u"importButton")

        self.controlsLayout.addWidget(self.importButton)

        self.removeButton = QPushButton(self.importRunBox)
        self.removeButton.setObjectName(u"removeButton")

        self.controlsLayout.addWidget(self.removeButton)

        self.verticalSpacer_3 = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.controlsLayout.addItem(self.verticalSpacer_3)

        self.inputChosenLabel = QLabel(self.importRunBox)
        self.inputChosenLabel.setObjectName(u"inputChosenLabel")

        self.controlsLayout.addWidget(self.inputChosenLabel)

        self.poseButton = QPushButton(self.importRunBox)
        self.poseButton.setObjectName(u"poseButton")

        self.controlsLayout.addWidget(self.poseButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.controlsLayout.addItem(self.verticalSpacer)


        self.horizontalLayout.addLayout(self.controlsLayout)

        self.horizontalLayout.setStretch(0, 2)
        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.importRunBox)

        self.resultsBox = QGroupBox(self.scrollAreaWidgetContents)
        self.resultsBox.setObjectName(u"resultsBox")
        self.resultsBox.setMinimumSize(QSize(0, 200))
        self.verticalLayout_3 = QVBoxLayout(self.resultsBox)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.resultsLabel = QLabel(self.resultsBox)
        self.resultsLabel.setObjectName(u"resultsLabel")

        self.verticalLayout_3.addWidget(self.resultsLabel)

        self.logOutput = QPlainTextEdit(self.resultsBox)
        self.logOutput.setObjectName(u"logOutput")

        self.verticalLayout_3.addWidget(self.logOutput)


        self.verticalLayout.addWidget(self.resultsBox)

        self.line = QFrame(self.scrollAreaWidgetContents)
        self.line.setObjectName(u"line")
        self.line.setOrientation(Qt.Horizontal)

        self.verticalLayout.addWidget(self.line)

        self.visualizeBox = QGroupBox(self.scrollAreaWidgetContents)
        self.visualizeBox.setObjectName(u"visualizeBox")
        self.visualizeBox.setMinimumSize(QSize(0, 600))
        self.verticalLayout_5 = QVBoxLayout(self.visualizeBox)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.visualizeLabel = QLabel(self.visualizeBox)
        self.visualizeLabel.setObjectName(u"visualizeLabel")

        self.verticalLayout_5.addWidget(self.visualizeLabel)

        self.visualizeMainLayout = QHBoxLayout()
        self.visualizeMainLayout.setObjectName(u"visualizeMainLayout")
        self.visualizeControlsLayout = QVBoxLayout()
        self.visualizeControlsLayout.setObjectName(u"visualizeControlsLayout")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.csvComboBox = QComboBox(self.visualizeBox)
        self.csvComboBox.setObjectName(u"csvComboBox")

        self.horizontalLayout_2.addWidget(self.csvComboBox)

        self.horizontalSpacer_3 = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.visualizeControlsLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.runVisualizeButton = QPushButton(self.visualizeBox)
        self.runVisualizeButton.setObjectName(u"runVisualizeButton")

        self.horizontalLayout_3.addWidget(self.runVisualizeButton)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)


        self.visualizeControlsLayout.addLayout(self.horizontalLayout_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.visualizeControlsLayout.addItem(self.verticalSpacer_2)


        self.visualizeMainLayout.addLayout(self.visualizeControlsLayout)

        self.visualizeDisplayLayout = QVBoxLayout()
        self.visualizeDisplayLayout.setObjectName(u"visualizeDisplayLayout")
        self.toggleLayout = QHBoxLayout()
        self.toggleLayout.setObjectName(u"toggleLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.toggleLayout.addItem(self.horizontalSpacer)

        self.toggleSwitchLayout = QHBoxLayout()
        self.toggleSwitchLayout.setObjectName(u"toggleSwitchLayout")

        self.toggleLayout.addLayout(self.toggleSwitchLayout)


        self.visualizeDisplayLayout.addLayout(self.toggleLayout)

        self.videoPlayersLayout = QHBoxLayout()
        self.videoPlayersLayout.setObjectName(u"videoPlayersLayout")

        self.visualizeDisplayLayout.addLayout(self.videoPlayersLayout)

        self.sharedControlsLayout = QHBoxLayout()
        self.sharedControlsLayout.setObjectName(u"sharedControlsLayout")

        self.visualizeDisplayLayout.addLayout(self.sharedControlsLayout)

        self.exportLayout = QHBoxLayout()
        self.exportLayout.setObjectName(u"exportLayout")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.exportLayout.addItem(self.horizontalSpacer_2)

        self.exportFrameButton = QPushButton(self.visualizeBox)
        self.exportFrameButton.setObjectName(u"exportFrameButton")

        self.exportLayout.addWidget(self.exportFrameButton)


        self.visualizeDisplayLayout.addLayout(self.exportLayout)


        self.visualizeMainLayout.addLayout(self.visualizeDisplayLayout)

        self.visualizeMainLayout.setStretch(0, 1)
        self.visualizeMainLayout.setStretch(1, 4)

        self.verticalLayout_5.addLayout(self.visualizeMainLayout)


        self.verticalLayout.addWidget(self.visualizeBox)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout_4.addWidget(self.scrollArea)


        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Main Application", None))
        self.projectPathLabel.setText(QCoreApplication.translate("MainWindow", u"Current Project: Not Loaded", None))
        self.importRunBox.setTitle("")
        self.importRunLabel.setText(QCoreApplication.translate("MainWindow", u"Import & Run", None))
        self.importButton.setText(QCoreApplication.translate("MainWindow", u"Import Files...", None))
        self.removeButton.setText(QCoreApplication.translate("MainWindow", u"Remove Selected", None))
        self.inputChosenLabel.setText(QCoreApplication.translate("MainWindow", u"Input Chosen: None", None))
        self.poseButton.setText(QCoreApplication.translate("MainWindow", u"Pose !", None))
        self.resultsBox.setTitle("")
        self.resultsLabel.setText(QCoreApplication.translate("MainWindow", u"Results", None))
        self.visualizeBox.setTitle("")
        self.visualizeLabel.setText(QCoreApplication.translate("MainWindow", u"Visualize", None))
        self.runVisualizeButton.setText(QCoreApplication.translate("MainWindow", u"Run", None))
        self.exportFrameButton.setText(QCoreApplication.translate("MainWindow", u"Export Current Frame", None))
    # retranslateUi

