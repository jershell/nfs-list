__author__ = 'jershell'
from PyQt4.QtGui import QDialog
from PyQt4 import uic, QtGui
from PyQt4.QtCore import Qt

class InfoDialog(QDialog):
    def __init__(self, data):
        QDialog.__init__(self)

        # Set up the user interface from Designer.
        uic.loadUi("./InfoWindow/info_form.ui", self)
        self.setFixedSize(213, 283)
        pixmap = QtGui.QPixmap("./MainWindow/NAS-icon.png")
        w = self.label_icon.width()
        h = self.label_icon.height()
        self.label_icon.setPixmap(pixmap.scaled(w, h, Qt.KeepAspectRatio))
        self.textBrowser.setHtml('\
        <table style="margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px;">\
        <tr><td>ip:</td><td>'+str(data["host"])+'</td></tr>\
        <tr><td>hostname:</td><td>'+str(data["hostname"])+'</td></tr>\
        <tr><td>port:</td><td>'+str(data["port"])+'</td></tr>\
        <tr><td>Groups:</td><td>'+str(data["group"])+'</td></tr>\
        <tr><td>Paths:</td><td>'+str(data["path"])+'</td></tr>\
        </table>')

        # Make some local modifications.


        # Connect up the buttons.
        self.pushButtonClose.clicked.connect(self.close)