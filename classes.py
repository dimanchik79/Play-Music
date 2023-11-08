import os
import time
import threading

import pygame
import requests

from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QDialog, QTableWidgetItem

from bs4 import BeautifulSoup
from tinytag import TinyTag

from models import PlayList, Albums

pygame.mixer.init()


def get_time(duration: float) -> str:
    """Функция преобразует число в формат 00:00:00"""
    duration /= 1000
    second = f"{0}{int(duration % 60)}"
    minute = '00' if (duration % 60) == 0 else f"{0}{int(duration / 60)}"
    hour = '00' if (duration % 3600) == 0 else f"{0}{int(duration / 3600)}"
    return f"{hour:}:{minute}:{second[0:] if len(second) < 3 else second[1:]}"


def get_news() -> list:
    """Функция парсит сайт и возвращает список с анонсами новостей"""
    news = []
    response = requests.get("https://lenta.ru/parts/news/")
    if response.status_code > 400:
        news.append("Check your Internet connect ...")
        return news
    response = response.text
    soup = BeautifulSoup(response, 'lxml')
    block = soup.find_all('h3')
    for row in block:
        news.append(row.text + ' (РИА НОВОСТИ) ... ')
    return news


class MainClass(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.open_window = None
        (self.play_list, self.pause, self.start, self.duration,
         self.duration_sec, self.duration_old, self.song_id,
         self.song_id_old, self.total_songs, self.wait, self.vol,
         self.p_text, self.save_window, self.count, self.id,
         self.album, self.news_count, self.x_pos) = [{}, False, False, None, None, None, None, 0, 0, 0, 0, "", None, 0,
                                                     [], "", 0, 481]

        uic.loadUi("DIALOG/player.ui", self)

        self.setFixedSize(501, 648)

        self.volume.valueChanged.connect(self.volume_change)
        self.add.clicked.connect(self.file_add)
        self.del_song.clicked.connect(self.delete_song)
        self.play.clicked.connect(self.press_play_button)
        self.stop.clicked.connect(self.press_stop_button)
        self.forward.clicked.connect(self.next_song)
        self.back.clicked.connect(self.back_song)

        self.exit_btn.clicked.connect(self.exit_program)

        self.playlist.doubleClicked.connect(self.bind_tree_change_song)
        self.soft.clicked.connect(self.thread_soft_volume_off)
        self.save.clicked.connect(self.save_playlist)
        self.open.clicked.connect(self.open_playlist)
        self.clear.clicked.connect(self.clear_playlist)

        self.update_playlist()
        self.playlist.setCurrentRow(self.count)
        self.playlist.setFocus()

        self.news = get_news()

        self.news_text = QtWidgets.QLabel(self.runstring)
        self.news_text.setText(self.news[self.news_count])
        self.news_text.setStyleSheet("color: black; border: 0;")

        threading.Thread(target=self.run_string, args=(), daemon=True).start()
        threading.Thread(target=self.play_music, args=(), daemon=True).start()

    def delete_song(self):
        # TODO удаление песни из списка
        if not self.id:
            return
        if self.start:
            self.press_stop_button()
        row = self.playlist.row(self.playlist.currentItem())
        PlayList.delete().where(PlayList.id == self.id[row]).execute()

        self.update_playlist()
        self.playlist.setCurrentRow(row if row < self.playlist.count() else row - 1)
        self.playlist.setFocus()

    def volume_change(self):
        if self.start:
            pygame.mixer.music.set_volume(self.volume.value() / 100)

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
                return
        else:
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
                            album=self.p_text if self.p_text != "" else "*")
        self.update_playlist()
        self.playlist.setCurrentRow(self.count)
        self.playlist.setFocus()

    def press_stop_button(self) -> None:
        try:
            self.start = False
            self.pause = False
            self.clock.setText("00:00:00")
            self.play.setIcon(QtGui.QIcon("IMG/play.ico"))
            self.play.setIconSize(QtCore.QSize(28, 28))
            self.playlist.item(self.song_id_old).setForeground(QtGui.QColor('black'))
            pygame.mixer.music.unload()
        except RuntimeError:
            return

    def press_play_button(self) -> None:
        if not self.id:
            return
        if not self.start:
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

            self.clock.setText(self.duration)

            pygame.mixer.music.load(path_file)
            pygame.mixer.music.play(loops=0)

            pygame.mixer.music.set_volume(self.volume.value() / 100)
            self.start = True
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

    def update_playlist(self):
        album, self.id = [], []
        self.playlist.clear()
        self.play_list = {}
        self.count = 0
        for row in PlayList.select():
            if os.path.exists(f"{row.song_path}"):
                song = TinyTag.get(row.song_path)
                self.playlist.addItem(f"{row.duration}│{song.title} ♫ {song.artist}")
                self.play_list[row.id] = [f"{song.title} ♫ {song.artist}", row.song_path, row.duration,
                                          row.duration_sec, row.album]
                self.id.append(row.id)
        self.total_songs = len(self.play_list)
        self.number.setText(str(self.total_songs))

        for key, word in self.play_list.items():
            album.append(word[4])
        self.album = ", ".join(set(album))
        self.album_txt.setText(self.album if self.album != "*" else "NoName")
        if "*" in self.album:
            self.album_txt.setStyleSheet("border: 1px solid rgb(85, 0, 0);border-radius: 5px;color: rgb(255, 0, 0);")
        else:
            self.album_txt.setStyleSheet("border: 1px solid rgb(85, 0, 0);border-radius: 5px;color: rgb(0, 0, 0);")

    def play_music(self):
        while True:
            time.sleep(1)
            if not self.start:
                self.clock.setText('---')
            if self.pause:
                pass
            else:
                if self.start:
                    mins, secs = divmod(int(self.duration_sec), 60)
                    self.clock.setText(f'{mins:02d}:{secs:02d}')
                    self.duration_sec -= 1
                    if pygame.mixer.music.get_pos() == -1:
                        self.next_song()

    def next_song(self):
        if self.count < self.total_songs - 1:
            self.count += 1
        else:
            self.count = 0
        self.next_back()

    def next_back(self):
        self.press_stop_button()
        self.playlist.setCurrentRow(self.count)
        self.press_play_button()

    def back_song(self):
        if self.count > 0:
            self.count -= 1
        else:
            self.count = self.total_songs - 1
        self.next_back()

    def exit_program(self):
        self.pause = True
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self.close()

    def save_playlist(self):
        self.save_window = SaveAlbum(self.album)
        self.save_window.show()
        self.save_window.exec_()
        if self.save_window.result() == 1:
            self.save_album()

    def open_playlist(self):
        self.open_window = OpenAlbum()
        self.open_window.show()
        self.open_window.exec_()
        if self.open_window.result() == 1:
            self.open_album()

    def open_album(self):
        if self.start:
            self.press_stop_button()
        if self.open_window.r_open.isChecked():
            PlayList.delete().execute()
        for row in Albums.select().where(Albums.album == self.open_window.albums.currentItem().text()):
            PlayList.create(song_name=row.song_name,
                            song_path=row.song_path,
                            duration=row.duration,
                            duration_sec=row.duration_sec,
                            album=row.album)
        self.play_list = {}
        self.update_playlist()
        self.count = 0
        self.playlist.setCurrentRow(self.count)
        self.playlist.setFocus()

    def clear_playlist(self):
        PlayList.delete().execute()
        self.press_stop_button()
        self.play_list = {}
        self.update_playlist()

    def save_album(self):
        Albums.delete().where(Albums.album == self.save_window.name.text()).execute()
        PlayList.delete().execute()
        for key, word in self.play_list.items():
            Albums.create(song_name=word[0],
                          song_path=word[1],
                          duration=word[2],
                          duration_sec=word[3],
                          album=self.save_window.name.text())
            PlayList.create(song_name=word[0],
                            song_path=word[1],
                            duration=word[2],
                            duration_sec=word[3],
                            album=self.save_window.name.text())

        self.press_stop_button()
        self.play_list = {}
        self.update_playlist()
        self.playlist.setCurrentRow(self.count)

    def run_string(self):
        while True:
            try:
                self.news_text.setGeometry(self.x_pos, 8, len(self.news[self.news_count]) * 8, 12)
                self.x_pos -= 1
                time.sleep(0.009)
                if self.x_pos == -(len(self.news[self.news_count]) * 8):
                    self.x_pos = 481
                    self.news_count += 1
                    if self.news_count == len(self.news):
                        self.news = get_news()
                        self.news_count = 0
                self.news_text.setText(self.news[self.news_count])
            except RuntimeError:
                break


class SaveAlbum(QDialog):
    def __init__(self, album) -> None:
        super().__init__()
        self.album = album
        uic.loadUi("DIALOG/save.ui", self)
        self.setFixedSize(400, 120)
        self.name.setText(self.album)
        self.name.setDisabled(True)
        self.ch_name.stateChanged.connect(self.enabled_textline)

    def enabled_textline(self, checked):
        if checked == 2:
            self.name.setDisabled(False)
            self.name.setFocus()
        else:
            self.name.setDisabled(True)


class Information(QDialog):
    def __init__(self, album) -> None:
        super().__init__()

        uic.loadUi("DIALOG/info.ui", self)
        self.setFixedSize(881, 596)

        info = []

        self.info_table.setColumnCount(3)
        self.info_table.setHorizontalHeaderLabels(["File", "Path", "Duration"])
        self.info_table.setColumnWidth(0, 400)
        self.info_table.setColumnWidth(1, 300)

        for album in Albums.select().where(Albums.album == album):
            info.append([album.song_name, album.song_path, album.duration])
        self.info_table.setRowCount(len(info))

        for row in range(len(info)):
            for col in range(3):
                item = QTableWidgetItem(info[row][col])
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.info_table.setItem(row, col, item)


class OpenAlbum(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.info = None

        uic.loadUi("DIALOG/open.ui", self)
        self.setFixedSize(400, 428)
        self.r_open.setChecked(True)
        self.see.clicked.connect(self.album_information)

        self.playlists = [row.album for row in Albums.select()]
        if len(self.playlists) != 0:
            for album in set(self.playlists):
                self.albums.addItem(album)
            self.albums.setCurrentRow(0)
            self.albums.setFocus()

    def album_information(self):
        self.info = Information(self.albums.currentItem().text())
        self.info.show()
        self.info.exec_()
