import os
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from tinytag import TinyTag
from models import PlayList

import pygame


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
        
        self.play_list = {}
        self.pause = False
        self.start = False
        self.duration = None
        self.duretion_sec = None
        self.duratoin_old = None
        self.song_id = None
        self.song_id_old = None
        self.total_songs = 0
        self.wait = 0

        uic.loadUi("player.ui", self)
        
        self.playlist.setHeaderLabels(['Song','Time'])
        
        self.add.clicked.connect(self.file_add)
        self.play.clicked.connect(self.press_play_button)
        self.stop.clicked.connect(self.press_stop_button)
    
        
    def bind_tree_change_song(self, event):
        self.press_stop_button()
        self.press_play_button()

    def file_add(self):
        song_files = []
        songs = QtWidgets.QFileDialog.getOpenFileNames(filter="*.mp3 *.wav")[0]
        if not songs:
            return
        
        for element in songs:
            song_files += (element, )
        
        for song_file in song_files:
            song = TinyTag.get(song_file)
            text_name = song_file[song_file.rindex("/") + 1:]
            text_time = f"{get_time(song.duration * 1000)}"
            PlayList.create(song_name = text_name, 
                            song_path = song_file,
                            duration = text_time,
                            duration_sec = song.duration)
            
    def press_stop_button(self):
        self.start = False
        self.pause = False
        # self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/play.ico"), size=(24, 24)))
        # self.btn_play.place_configure(x=self.x_pos)
        # self.btn_play.update()
        pygame.mixer.music.stop()
        
    def press_play_button(self):
        # if not self.start:
            # self.start = True
            # path = self.playlist[int(self.tree.selection()[0])][1]
            # self.duration = self.playlist[int(self.tree.selection()[0])][2]
            # self.duration_sec = self.playlist[int(self.tree.selection()[0])][3]
            # self.wait = self.duration_sec / 250
            # print(self.wait)
            
            # if self.song_id_old != None:
            #     self.tree.tag_configure('white', foreground='white')
            #     self.tree.item(self.song_id_old, tag='white')
            #     self.tree.set(self.song_id, 1, self.duratoin_old)
            
            # self.song_id = str(self.tree.selection()[0])
            # self.song_id_old = self.song_id
            # self.duratoin_old = self.playlist[int(self.tree.selection()[0])][2]     
            # self.tree.tag_configure('pink', foreground='pink')
            # self.tree.item(self.song_id, tag='pink')
            # pygame.mixer.music.load(path)
            # pygame.mixer.music.play(loops=0)
            # for thred in threading.enumerate():
            #     if "play_music" in str(thred):
            #         return
            # else:
            #     threading.Thread(target=self.play_music, args=(), daemon=True).start()
            #     return
        
        if not self.pause:
            self.play.setIcon(QtGui.QIcon("IMG/pause.ico"))
            self.play.setIconSize(QtCore.QSize(28,28))
            self.pause = True
            # pygame.mixer.music.pause()
        else:
            self.play.setIcon(QtGui.QIcon("IMG/play.ico"))
            self.play.setIconSize(QtCore.QSize(28,28))
            self.pause = False
            # pygame.mixer.music.unpause()
            # threading.Thread(target=self.play_music, args=(), daemon=True).start()
    
    def play_music(self):
        while get_time(pygame.mixer.music.get_pos()) != self.duration:
            if self.pause or not self.start:
                return
            pygame.mixer.music.set_volume(self.slider_volume.get() / 100)
            # self.tree.set(self.song_id, 1, get_time(pygame.mixer.music.get_pos()))
            # time.sleep(self.wait)
            # self.x_pos += 1
            self.btn_play.place_configure(x=self.x_pos)
            self.btn_play.update()
        
        pygame.mixer.music.stop()
        
    def update_playlist(self):
        if self.tree.selection() != ():
            for delete_row in self.tree.get_children():
                self.tree.delete(delete_row)
        for row in PlayList.select():
            if os.path.exists(f"{row.song_path}"):
                self.tree.insert("", END, iid=str(row.id), values=(row.song_name, row.duration))
            self.playlist[row.id] = [row.song_name, row.song_path, row.duration, row.duration_sec]
        