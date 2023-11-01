import os
import time

import threading
import pygame

from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QDialog
from tinytag import TinyTag
from models import PlayList

pygame.mixer.init()


def get_time(duration):
    duration /= 1000
    if duration < 0:
        return
    second = f"{0}{int(duration % 60)}"
    minute = '00' if (duration % 60) == 0 else f"{0}{int(duration / 60)}"
    hour = '00' if (duration % 3600) == 0 else f"{0}{int(duration / 3600)}"
    return f"{hour:}:{minute}:{second[0:] if len(second) < 3 else second[1:]}"


class MainClass(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        (self.play_list, self.pause, self.start, self.duration,
         self.duration_sec, self.duration_old, self.song_id,
         self.song_id_old, self.total_songs, self.wait, self.vol,
         self.p_text, self.save_window, self.count, self.id, self.album) = [{}, False, False, None, None, None, None, 0,
                                                                            0, 0, 0, "", None, 0, [], ""]

        uic.loadUi("DIALOG/player.ui", self)

        self.setFixedSize(501, 648)

        self.add.clicked.connect(self.file_add)
        self.play.clicked.connect(self.press_play_button)
        self.stop.clicked.connect(self.press_stop_button)
        self.forward.clicked.connect(self.next_song)
        self.back.clicked.connect(self.back_song)

        self.exit_btn.clicked.connect(self.exit_program)

        self.playlist.doubleClicked.connect(self.bind_tree_change_song)
        self.soft.clicked.connect(self.thread_soft_volume_off)
        self.save.clicked.connect(self.save_playlist)

        self.update_playlist()
        self.playlist.setCurrentRow(self.count)
        self.playlist.setFocus()

    def closeEvent(self, event):
        self.exit_program()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.bind_tree_change_song()

    def bind_tree_change_song(self):
        self.press_stop_button()
        self.press_play_button()

    def thread_soft_volume_off(self):
        for process in threading.enumerate():
            if process.name.count("soft_volume_off"):
                process.is_alive()
        threading.Thread(target=self.soft_volume_off, args=(), daemon=True).start()

    def soft_volume_off(self):
        if self.soft.checkState() == 2:
            self.soft.setEnabled(False)
            self.volume.setEnabled(False)
            self.vol = self.volume.value()
            vol = self.vol
            while vol != -1:
                self.volume.setValue(vol)
                pygame.mixer.music.set_volume(vol / 100)
                time.sleep(0.05)
                vol -= 1
            self.soft.setEnabled(True)
            self.volume.setEnabled(True)
        else:
            vol = 0
            self.soft.setEnabled(False)
            self.volume.setEnabled(False)
            while vol != self.vol:
                self.volume.setValue(vol)
                pygame.mixer.music.set_volume(self.volume.value() / 100)
                time.sleep(0.05)
                vol += 1
            self.soft.setEnabled(True)
            self.volume.setEnabled(True)

    def file_add(self):
        songs = QtWidgets.QFileDialog.getOpenFileNames(filter="*.mp3 *.wav")[0]
        if not songs:
            return
        for song_file in songs:
            song = TinyTag.get(song_file)
            text_name = song_file[song_file.rindex("/") + 1:]
            text_time = f"{get_time(song.duration * 1000)}"
            PlayList.create(song_name=text_name,
                            song_path=song_file,
                            duration=text_time,
                            duration_sec=song.duration,
                            list_name=self.p_text if self.p_text != "" else "*")
        self.update_playlist()
        self.playlist.setCurrentRow(self.count)
        self.playlist.setFocus()

    def press_stop_button(self) -> None:
        self.start = False
        self.pause = False
        self.clock.setText("00:00:00")
        self.play.setIcon(QtGui.QIcon("IMG/play.ico"))
        self.play.setIconSize(QtCore.QSize(28, 28))
        self.playlist.item(self.song_id_old).setForeground(QtGui.QColor('black'))
        pygame.mixer.music.unload()

    def press_play_button(self) -> None:
        if not self.start:
            self.start = True
            self.play.setIcon(QtGui.QIcon("IMG/pause.ico"))
            self.play.setIconSize(QtCore.QSize(28, 28))
            self.count = self.playlist.currentIndex().row()
            key = self.id[self.count]
            path_file = self.play_list[key][1]
            self.duration = self.play_list[key][2]
            self.duration_sec = self.play_list[key][3]
            if self.song_id_old is not None:
                self.playlist.item(self.song_id_old).setForeground(QtGui.QColor('black'))
            self.song_id = self.count
            self.song_id_old = self.song_id
            self.playlist.item(self.count).setForeground(QtGui.QColor('blue'))
            pygame.mixer.music.load(path_file)
            pygame.mixer.music.play(loops=0)
            for process in threading.enumerate():
                if process.name.count("play_music"):
                    process.is_alive()
            threading.Thread(target=self.play_music, args=(), daemon=True).start()
            return

        if not self.pause:
            self.play.setIcon(QtGui.QIcon("IMG/play.ico"))
            self.play.setIconSize(QtCore.QSize(28, 28))
            self.pause = True
            pygame.mixer.music.pause()
        else:
            self.play.setIcon(QtGui.QIcon("IMG/pause.ico"))
            self.play.setIconSize(QtCore.QSize(28, 28))
            self.pause = False
            pygame.mixer.music.unpause()
            for process in threading.enumerate():
                if process.name.count("play_music"):
                    process.is_alive()
            threading.Thread(target=self.play_music, args=(), daemon=True).start()

    def update_playlist(self):
        album = []
        self.id = []
        self.playlist.clear()
        for row in PlayList.select():
            if os.path.exists(f"{row.song_path}"):
                self.playlist.addItem(f"{row.duration} # {row.song_name}")
            self.play_list[row.id] = [row.song_name, row.song_path, row.duration, row.duration_sec, row.album]
            self.id.append(row.id)
        self.total_songs = len(self.play_list)
        self.number.display(str(self.total_songs))
        for key, word in self.play_list.items():
            album.append(word[4])
        self.album = ", ".join(set(album))
        self.album_txt.setText(self.album)
        for process in threading.enumerate():
            if process.name.count("set_color_album"):
                process.is_alive()
        threading.Thread(target=self.set_color_album, args=(), daemon=True).start()

    def set_color_album(self):
        for color in range(255, 0, -1):
            self.album_txt.setStyleSheet(f"border: 1px solid rgb(85, 0, 0); border-radius: 5px; color: rgb({color}, "
                                         f"{color}, {color});")
            time.sleep(0.01)

    def play_music(self):
        while get_time(pygame.mixer.music.get_pos()) != self.duration:
            if self.pause or not self.start:
                return
            self.clock.setText(get_time(pygame.mixer.music.get_pos()))
            pygame.mixer.music.set_volume(self.volume.value() / 100)
        self.next_song()

    def next_song(self):
        self.press_stop_button()
        if self.count < self.total_songs - 1:
            self.count += 1
        else:
            self.count = 0
        self.playlist.setCurrentRow(self.count)
        self.press_play_button()

    def back_song(self):
        self.press_stop_button()
        if self.count > 0:
            self.count -= 1
        else:
            self.count = self.total_songs - 1
        self.playlist.setCurrentRow(self.count)
        self.press_play_button()

    def exit_program(self):
        self.pause = True
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self.close()

    def save_playlist(self):
        self.save_window = SaveClass()
        self.save_window.show()


class SaveClass(QDialog):
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi("DIALOG/save.ui", self)
        self.setFixedSize(400, 120)
