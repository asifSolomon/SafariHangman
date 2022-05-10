import os
import re
import sqlite3
import sys

import pandas
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QLabel

path = os.path.dirname(os.path.abspath(__file__))


class DBWidget(object):
    def __init__(self, Dialog):
        self.conn = sqlite3.connect(os.path.abspath
                                    (f"{path}/files/db/database.db"))

        Dialog.resize(600, 500)
        Dialog.setMinimumSize(QtCore.QSize(600, 500))
        Dialog.setMaximumSize(QtCore.QSize(600, 500))
        Dialog.setWindowTitle("Customize Words")
        Dialog.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
                              QtCore.Qt.Dialog)
        Dialog.setStyleSheet("background-color:rgb(255, 236, 184);")

        font = QtGui.QFont()
        font.setFamily("Comic Sans MS")
        font.setPointSize(23)
        Dialog.setFont(font)

        self.labelTitle = QtWidgets.QLabel(Dialog)
        self.labelTitle.setText('list of words')
        self.labelTitle.move(200, 10)
        self.labelTitle.setFont(font)

        font.setPointSize(14)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(145, 450, 340, 30))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Save |
                                          QtWidgets.QDialogButtonBox.Discard)
        self.buttonBox.buttons()[0].clicked.connect(self.save)
        self.buttonBox.buttons()[0].setStyleSheet("background-color:rgb"
                                                  "(247, 194, 151);")
        self.buttonBox.buttons()[1].clicked.connect(Dialog.close)
        self.buttonBox.buttons()[1].setStyleSheet("background-color:rgb"
                                                  "(247, 194, 151);")
        self.buttonBox.buttons()[1].setFont(font)
        self.buttonBox.buttons()[0].setFont(font)

        self.buttonBox.buttons()[0].setDefault(True)

        self.labelText = QtWidgets.QLabel(Dialog)
        self.labelText.setText('Enter word here: ')
        self.labelText.move(300, 90)
        self.labelText.setFont(font)

        self.listOfWords = QtWidgets.QListWidget(Dialog)
        self.listOfWords.setGeometry(QtCore.QRect(10, 100, 250, 350))
        self.listOfWords.itemClicked.connect(self.clicked)
        self.listOfWords.setFont(font)

        self.inputLine = QtWidgets.QLineEdit(Dialog)
        self.inputLine.setGeometry(QtCore.QRect(300, 130, 200, 25))
        self.inputLine.setText("")
        self.inputLine.setStyleSheet("background-color:rgb(255, 255, 255);")
        self.inputLine.setFont(font)
        self.inputLine.    setMaxLength(15)

        self.addButton = QtWidgets.QPushButton(Dialog)
        self.addButton.setGeometry(QtCore.QRect(300, 200, 200, 25))
        self.addButton.setStyleSheet("background-color:rgb(247, 194, 151);")
        self.addButton.setText("Add")
        self.addButton.clicked.connect(self.addItem)
        self.addButton.setAutoDefault(False)
        self.addButton.setFont(font)

        self.removeButton = QtWidgets.QPushButton(Dialog)
        self.removeButton.setGeometry(QtCore.QRect(300, 250, 200, 25))
        self.removeButton.setStyleSheet("background-color:rgb(247, 194, 151);")
        self.removeButton.setText("Remove")
        self.removeButton.clicked.connect(self.removeItem)
        self.removeButton.setDisabled(True)
        self.removeButton.setFont(font)

        self.resetButton = QtWidgets.QPushButton(Dialog)
        self.resetButton.setGeometry(QtCore.QRect(300, 300, 200, 25))
        self.resetButton.setStyleSheet("background-color:rgb(247, 194, 151);")
        self.resetButton.setText("Reset")
        self.resetButton.setAutoDefault(False)
        self.resetButton.setFont(font)
        self.resetButton.clicked.connect(self.reset)

        self.clearAllButton = QtWidgets.QPushButton(Dialog)
        self.clearAllButton.setGeometry(QtCore.QRect(300, 350, 200, 25))
        self.clearAllButton.setStyleSheet("background-color:"
                                          "rgb(247, 194, 151);")
        self.clearAllButton.setText("Clear all")
        self.clearAllButton.setAutoDefault(False)
        self.clearAllButton.clicked.connect(self.listOfWords.clear)
        self.clearAllButton.setFont(font)

        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        self.reset()

    def addItem(self):
        item = self.inputLine.text().strip().title()
        lst = [self.listOfWords.item(i).text()
               for i in range(self.listOfWords.count())]
        if item and item not in lst and not re.findall(r"[^a-zA-Z ]", item):
            self.listOfWords.addItem(item)
            self.listOfWords.scrollToItem(self.listOfWords.item
                                          (self.listOfWords.count() - 1))
        self.inputLine.setText("")

    def removeItem(self):
        self.listOfWords.takeItem(self.listOfWords.currentRow())
        self.listOfWords.clearSelection()
        self.removeButton.setDisabled(True)

    def clicked(self):
        self.removeButton.setEnabled(True)

    def reset(self):
        words = pandas.read_sql_query("SELECT Word from tblWords "
                                      "WHERE Level=4", self.conn)
        words = list(words['Word'])
        self.listOfWords.clear()
        for word in words:
            self.listOfWords.addItem(word)

    def save(self):
        self.conn.execute("DELETE FROM tblWords WHERE Level=4")
        for i in range(self.listOfWords.count()):
            x = self.listOfWords.item(i).text()
            self.conn.execute(f"INSERT INTO tblWords (Word, Level, "
                              f"Discover, FileName, Priority)"
                              f" VALUES ('{x}', 4, 0, null, 3)")
        self.conn.commit()


def customize():
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = DBWidget(Dialog)
    Dialog.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    customize()