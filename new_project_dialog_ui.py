# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_project_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialogButtonBox, QFormLayout,
    QLabel, QLineEdit, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_NewProjectWidget(object):
    def setupUi(self, NewProjectWidget):
        if not NewProjectWidget.objectName():
            NewProjectWidget.setObjectName(u"NewProjectWidget")
        NewProjectWidget.setMinimumSize(QSize(500, 80))
        NewProjectWidget.setStyleSheet(u"/* --- Main Dialog Style --- */\n"
"QWidget#NewProjectWidget {\n"
"	background-color: #191e36;\n"
"	border-radius: 10px;\n"
"}\n"
"\n"
"/* --- Label Styles --- */\n"
"QLabel {\n"
"	color: #E0E0E0;\n"
"	font-family: \"Segoe UI\", Arial, sans-serif;\n"
"	font-size: 14px;\n"
"}\n"
"\n"
"/* --- Status Label Styles (No longer needed, but harmless to keep) --- */\n"
"QLabel#statusLabel {\n"
"	font-size: 12px;\n"
"}\n"
"\n"
"/* --- LineEdit Styles --- */\n"
"QLineEdit {\n"
"	background-color: #191C2C;\n"
"	border: 1px solid #4A5580;\n"
"	border-radius: 5px;\n"
"	padding: 8px;\n"
"	font-size: 14px;\n"
"	color: #E0E0E0;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"	border-color: #5A67D8;\n"
"}\n"
"\n"
"/* Make read-only fields look different */\n"
"QLineEdit:read-only {\n"
"    background-color: #2D3748;\n"
"    color: #A0AEC0;\n"
"}\n"
"\n"
"/* --- QDialogButtonBox Styles --- */\n"
"QDialogButtonBox QPushButton {\n"
"	background-color: #4A5580;\n"
"	color: white;\n"
"  min-width: 60px;\n"
"\u00a0 padding: 4px;\n"
"	border: 1p"
                        "x solid #5A67D8;\n"
"}\n"
"\n"
"QDialogButtonBox QPushButton:hover {\n"
"	background-color: #5A67D8;\n"
"}\n"
"\n"
"QDialogButtonBox QPushButton:disabled {\n"
"	background-color: #2D3748;\n"
"	color: #718096;\n"
"    border: 1px solid #4A5580;\n"
"}\n"
"\n"
"QDialogButtonBox QPushButton[text=\"OK\"] {\n"
"	background-color: #5A67D8;\n"
"}\n"
"\n"
"QDialogButtonBox QPushButton[text=\"OK\"]:hover {\n"
"	background-color: #4C58B8;\n"
"}\n"
"")
        self.verticalLayout = QVBoxLayout(NewProjectWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(20, 20, 20, 20)
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setLabelAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)
        self.nameLabel = QLabel(NewProjectWidget)
        self.nameLabel.setObjectName(u"nameLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.nameLabel)

        self.projectNameEdit = QLineEdit(NewProjectWidget)
        self.projectNameEdit.setObjectName(u"projectNameEdit")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.projectNameEdit)

        self.pathLabel = QLabel(NewProjectWidget)
        self.pathLabel.setObjectName(u"pathLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.pathLabel)

        self.projectPathEdit = QLineEdit(NewProjectWidget)
        self.projectPathEdit.setObjectName(u"projectPathEdit")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.projectPathEdit)


        self.verticalLayout.addLayout(self.formLayout)

        self.statusLabel = QLabel(NewProjectWidget)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.statusLabel)

        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.buttonBox = QDialogButtonBox(NewProjectWidget)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(NewProjectWidget)

        QMetaObject.connectSlotsByName(NewProjectWidget)
    # setupUi

    def retranslateUi(self, NewProjectWidget):
        NewProjectWidget.setWindowTitle(QCoreApplication.translate("NewProjectWidget", u"Form", None))
        self.nameLabel.setText(QCoreApplication.translate("NewProjectWidget", u"Project Name:", None))
        self.pathLabel.setText(QCoreApplication.translate("NewProjectWidget", u"Project Path:", None))
        self.statusLabel.setText("")
    # retranslateUi

