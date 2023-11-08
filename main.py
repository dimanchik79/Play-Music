import sys
from PyQt5.QtWidgets import QApplication

from os import path
from models import PlayList, Albums
from classes import MainClass


def main():
    dir_dir, *files = sys.argv
    dir_dir = dir_dir.replace(chr(92), chr(47))
    dir_dir = dir_dir[0:dir_dir.rfind("/")]

    app = QApplication(sys.argv)
    main_window = MainClass(dir_dir, files)
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    if not path.exists('DB/playlist.db'):
        PlayList.create_table()
        Albums.create_table()
    main()
