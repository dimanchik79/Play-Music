import sys
from PyQt5.QtWidgets import QApplication

from os import path
from models import PlayList
from classes import MainClass


def main():
    app = QApplication(sys.argv)
    mainwindow = MainClass()
    mainwindow.show()
    sys.exit(app.exec())
    

if __name__ == "__main__":
    if not path.exists('database/bot_base.db'):
        PlayList.create_table()
    main()
