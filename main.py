#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from MainWindow import *
import sys
def main():

        app = QtGui.QApplication(sys.argv)
        window = MainForm()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
        main()