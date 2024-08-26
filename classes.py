import os
import sys
import time
import threading

import pygame
import requests
import webbrowser

from bs4 import BeautifulSoup
from tinytag import TinyTag
from models import PlayList, Albums

from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QDialog, QTableWidgetItem, QFileDialog, QAction, QMenu


TRAY_STYLE = """
        color: black;
        background-color: rgb(255, 255, 246);
        font-size: 16px;
        font-weight: bold;
"""

TRAY_STYLE += "QMenu::item:hover { background-color: black; color: white; }"


pygame.mixer.init()


def show_git():
    """Функция открывает страницу на github"""
    webbrowser.open("https://github.com/dimanchik79/Player-Music", new=0, autoraise=True)


def get_time(duration: float) -> str:
    """Функция преобразует полученную длину песни в формат 00:00:00"""
    temp, secs = divmod(int(duration / 1000), 60)
    hours, minuts = divmod(int(temp), 60)
    return f'{hours:02d}:{minuts:02d}:{secs:02d}'


def get_news() -> list:
    """Функция парсит сайт и возвращает список с анонсами новостей"""
    news = []
    try:
        response = requests.get("https://lenta.ru/parts/news/")
    except Exception:
        news.append("Check your Internet connect ...")
        return news
    soup = BeautifulSoup(response.text, 'lxml')
    block = soup.find_all('h3')
    for row in block:
        news.append(row.text + ' (LENTA.RU) ... ')
    return news


class MainClass(QMainWindow):
    """Модель инициализации интерфейса плейера
    play_list: dict -

    """

    def __init__(self) -> None:
        super().__init__()
        self.open_window = None
        (self.play_list, self.pause, self.start, self.duration,
         self.duration_sec, self.duration_old, self.song_id,
         self.song_id_old, self.total_songs, self.wait, self.vol,
         self.p_text, self.save_window, self.count, self.id,
         self.album, self.news_count, self.x_pos) = [{}, False, False, None, None, None, None, 0, 0, 0, 0, "", None, 0,
                                                     [], "", 0, 481]

        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon("IMG/icon.ico"))

        show_action = QAction("Show Player", self)
        show_action.triggered.connect(self.show)
        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.triggered.connect(self.exit_program)

        tray_menu = QMenu(self)
        tray_menu.setStyleSheet(TRAY_STYLE)
        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.tray_icon.show()

        uic.loadUi("DIALOG/player.ui", self)

        self.setFixedSize(501, 648)

        self.volume.valueChanged.connect(self.volume_change)
        self.git.clicked.connect(show_git)
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

    def exit_program(self):
        """Метод закрывает окно программы"""
        self.pause = True
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        sys.exit()


    def delete_song(self) -> None:
        """Метод удаляет одну песню из списка воспроизведения"""
        if not self.id:
            return
        if self.start:
            self.press_stop_button()
        row = self.playlist.row(self.playlist.currentItem())
        PlayList.delete().where(PlayList.id == self.id[row]).execute()

        self.update_playlist()
        self.playlist.setCurrentRow(row if row < self.playlist.count() else row - 1)
        self.playlist.setFocus()

    def volume_change(self) -> None:
        """Метод устанавливает громкость песни"""
        if self.start:
            pygame.mixer.music.set_volume(self.volume.value() / 100)

    def closeEvent(self, event) -> None:
        """Метод вызывает метод выхода из программы"""
        event.ignore()  # Не вызывать метод closeEvent
        self.hide()

    def keyPressEvent(self, event) -> None:
        """Метод реализует обработку нажатия клавиши Enter"""
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.bind_tree_change_song()

    def bind_tree_change_song(self) -> None:
        """Метод реализует смену песни"""
        self.press_stop_button()
        self.press_play_button()

    def thread_soft_volume_off(self) -> None:
        """Метод вызывает в потоке процедуру мягкой смены громкости звука"""
        for process in threading.enumerate():
            if process.name.count("soft_volume_off"):
                return
        else:
            threading.Thread(target=self.soft_volume_off, args=(), daemon=True).start()

    def soft_volume_off(self) -> None:
        """Метод реализует мягкую смены громкости звука"""
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
        """Метод реализует добавление песен из файлов"""
        songs = QFileDialog.getOpenFileNames(self, "Open Music files", "", "Music Files (*.mp3 *.wav)")[0]
        if not songs:
            return
        for song_file in songs:
            try:
                song = TinyTag.get(song_file)
                text_name = song_file[song_file.rindex("/") + 1:]
                text_time = f"{get_time(song.duration * 1000)}"
                PlayList.create(song_name=text_name,
                                song_path=song_file,
                                duration=text_time,
                                duration_sec=song.duration,
                                album=self.p_text if self.p_text != "" else "*")
            except Exception:
                continue
        self.update_playlist()
        self.playlist.setCurrentRow(self.count)
        self.playlist.setFocus()

    def press_stop_button(self) -> None:
        """Метод обрабатывает нажатие на кнопку Стоп"""
        if not self.id:
            return
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
        """Метод обрабатывает нажатие на кнопку Плай"""
        if not self.id:
            return
        if not self.start:
            self.play.setIcon(QtGui.QIcon("IMG/pause.ico"))
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
            self.number.setText(f"{self.count + 1}/{self.total_songs}")
            pygame.mixer.music.load(path_file)
            pygame.mixer.music.play(loops=0)
            pygame.mixer.music.set_volume(self.volume.value() / 100)
            self.start = True
            return

        if not self.pause:
            self.play.setIcon(QtGui.QIcon("IMG/play.ico"))
            self.pause = True
            pygame.mixer.music.pause()
        else:
            self.play.setIcon(QtGui.QIcon("IMG/pause.ico"))
            self.pause = False
            pygame.mixer.music.unpause()

    def update_playlist(self):
        """Метод реализует обновление списка воспроизведения"""
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
        """Метод реализует отсчет таймера и проверяет окончание песни"""
        while True:
            time.sleep(1)
            if not self.start:
                self.clock.setText('---')
                self.number.setText(f"{self.total_songs}")
            if self.pause:
                self.clock.setText('pause')
            else:
                if self.start:
                    self.clock.setText(get_time(self.duration_sec * 1000))
                    self.duration_sec -= 1
                    if pygame.mixer.music.get_pos() == -1:
                        self.next_song()

    def next_song(self):
        """Метод увеличивает счетчик песен на 1"""
        if self.count < self.total_songs - 1:
            self.count += 1
        else:
            self.count = 0
        self.next_play()

    def back_song(self):
        """Метод уменьшает счетчик песен на 1"""
        if self.count > 0:
            self.count -= 1
        else:
            self.count = self.total_songs - 1
        self.next_play()

    def next_play(self):
        """Метод иницилизирует проигрывание следующей песни"""
        self.press_stop_button()
        self.playlist.setCurrentRow(self.count)
        self.press_play_button()

    def save_playlist(self):
        """Метод вызывает диалог записи плей-листа"""
        if not self.id:
            return
        self.save_window = SaveAlbum(self.album)
        self.save_window.show()
        self.save_window.exec_()
        if self.save_window.result() == 1:
            self.save_album()

    def open_playlist(self):
        """Метод вызывает диалог открытия плей-листа"""
        self.open_window = OpenAlbum()
        self.open_window.show()
        self.open_window.exec_()
        if self.open_window.result() == 1 and self.open_window.playlists:
            self.open_album()

    def open_album(self):
        """Метод вызывает открытия плей-листа"""
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
        """Метод очистки плей-листа"""
        if not self.id:
            return
        PlayList.delete().execute()
        self.press_stop_button()
        self.play_list = {}
        self.update_playlist()

    def save_album(self):
        """Метод записи плей-листа"""
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
        """Метод вызывает бегущую строку"""
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
                continue


class SaveAlbum(QDialog):
    """Класс инициализирует диалоговон окно записи плей-листа"""

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
        self.info_table.setHorizontalHeaderLabels(["Song", "Path", "Duration"])
        self.info_table.setColumnWidth(0, 300)
        self.info_table.setColumnWidth(1, 400)

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
        self.playlists = []

        uic.loadUi("DIALOG/open.ui", self)
        self.setFixedSize(400, 428)
        self.r_open.setChecked(True)
        self.see.clicked.connect(self.album_information)
        self.erase.clicked.connect(self.erase_album)
        self.update_albums()

        if self.playlists:
            self.albums.setCurrentRow(0)
            self.albums.setFocus()

    def album_information(self):
        if not self.playlists:
            return
        self.info = Information(self.albums.currentItem().text())
        self.info.show()
        self.info.exec_()

    def erase_album(self):
        if not self.playlists:
            return
        row = self.albums.row(self.albums.currentItem())
        Albums.delete().where(Albums.album == self.albums.currentItem().text()).execute()
        self.update_albums()
        if self.playlists:
            self.albums.setCurrentRow(row if row < self.albums.count() else row - 1)
            self.albums.setFocus()

    def update_albums(self):
        self.playlists.clear()
        self.albums.clear()
        self.playlists = [row.album for row in Albums.select()]
        for album in set(self.playlists):
            self.albums.addItem(album)
