# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QRadioButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_Cards_Interface(object):
    def setupUi(self, Cards_Interface):
        if not Cards_Interface.objectName():
            Cards_Interface.setObjectName(u"Cards_Interface")
        Cards_Interface.resize(800, 600)
        self.groupBox = QGroupBox(Cards_Interface)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setGeometry(QRect(30, 80, 451, 381))
        self.formLayout_2 = QFormLayout(self.groupBox)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.lineEdit_2 = QLineEdit(self.groupBox)
        self.lineEdit_2.setObjectName(u"lineEdit_2")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.lineEdit_2)

        self.label_2 = QLabel(self.groupBox)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.lineEdit_3 = QLineEdit(self.groupBox)
        self.lineEdit_3.setObjectName(u"lineEdit_3")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.lineEdit_3)

        self.label_3 = QLabel(self.groupBox)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.lineEdit_4 = QLineEdit(self.groupBox)
        self.lineEdit_4.setObjectName(u"lineEdit_4")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.lineEdit_4)

        self.radioButton_2 = QRadioButton(self.groupBox)
        self.radioButton_2.setObjectName(u"radioButton_2")

        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.FieldRole, self.radioButton_2)

        self.label_5 = QLabel(self.groupBox)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(10, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.lineEdit_5 = QLineEdit(self.groupBox)
        self.lineEdit_5.setObjectName(u"lineEdit_5")

        self.formLayout_2.setWidget(10, QFormLayout.ItemRole.FieldRole, self.lineEdit_5)

        self.label_6 = QLabel(self.groupBox)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(11, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.lineEdit_6 = QLineEdit(self.groupBox)
        self.lineEdit_6.setObjectName(u"lineEdit_6")

        self.formLayout_2.setWidget(11, QFormLayout.ItemRole.FieldRole, self.lineEdit_6)

        self.radioButton = QRadioButton(self.groupBox)
        self.radioButton.setObjectName(u"radioButton")

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.FieldRole, self.radioButton)

        self.label_4 = QLabel(self.groupBox)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.radioButton_3 = QRadioButton(self.groupBox)
        self.radioButton_3.setObjectName(u"radioButton_3")

        self.formLayout_2.setWidget(7, QFormLayout.ItemRole.FieldRole, self.radioButton_3)

        self.groupBox_2 = QGroupBox(Cards_Interface)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.groupBox_2.setGeometry(QRect(30, 460, 361, 81))
        self.horizontalLayout = QHBoxLayout(self.groupBox_2)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.pushButton_2 = QPushButton(self.groupBox_2)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.groupBox_2)
        self.pushButton_3.setObjectName(u"pushButton_3")

        self.horizontalLayout.addWidget(self.pushButton_3)

        self.groupBox_3 = QGroupBox(Cards_Interface)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.groupBox_3.setGeometry(QRect(480, 80, 284, 491))
        self.verticalLayout = QVBoxLayout(self.groupBox_3)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_7 = QLabel(self.groupBox_3)
        self.label_7.setObjectName(u"label_7")

        self.verticalLayout.addWidget(self.label_7)

        self.listWidget = QListWidget(self.groupBox_3)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout.addWidget(self.listWidget)

        self.groupBox_4 = QGroupBox(Cards_Interface)
        self.groupBox_4.setObjectName(u"groupBox_4")
        self.groupBox_4.setGeometry(QRect(30, 0, 731, 80))
        self.horizontalLayout_2 = QHBoxLayout(self.groupBox_4)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.lineEdit = QLineEdit(self.groupBox_4)
        self.lineEdit.setObjectName(u"lineEdit")

        self.horizontalLayout_2.addWidget(self.lineEdit)

        self.pushButton = QPushButton(self.groupBox_4)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_2.addWidget(self.pushButton)


        self.retranslateUi(Cards_Interface)

        QMetaObject.connectSlotsByName(Cards_Interface)
    # setupUi

    def retranslateUi(self, Cards_Interface):
        Cards_Interface.setWindowTitle(QCoreApplication.translate("Cards_Interface", u"Cards_Interface", None))
        self.groupBox.setTitle(QCoreApplication.translate("Cards_Interface", u"Description", None))
        self.label.setText(QCoreApplication.translate("Cards_Interface", u"Character(s)", None))
        self.label_2.setText(QCoreApplication.translate("Cards_Interface", u"Kana Writing", None))
        self.label_3.setText(QCoreApplication.translate("Cards_Interface", u"Romaji Writing", None))
        self.radioButton_2.setText(QCoreApplication.translate("Cards_Interface", u"Kanji", None))
        self.label_5.setText(QCoreApplication.translate("Cards_Interface", u"Meaning", None))
        self.label_6.setText(QCoreApplication.translate("Cards_Interface", u"Related", None))
        self.radioButton.setText(QCoreApplication.translate("Cards_Interface", u"Kana", None))
        self.label_4.setText(QCoreApplication.translate("Cards_Interface", u"Type", None))
        self.radioButton_3.setText(QCoreApplication.translate("Cards_Interface", u"Phrase", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("Cards_Interface", u"Modify", None))
        self.pushButton_2.setText(QCoreApplication.translate("Cards_Interface", u"Save", None))
        self.pushButton_3.setText(QCoreApplication.translate("Cards_Interface", u"Delete", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("Cards_Interface", u"Dictionary", None))
        self.label_7.setText(QCoreApplication.translate("Cards_Interface", u"Total Cards", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("Cards_Interface", u"Toolbar", None))
        self.pushButton.setText(QCoreApplication.translate("Cards_Interface", u"Search", None))
    # retranslateUi

