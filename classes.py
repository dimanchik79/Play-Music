from tkinter.ttk import Treeview
from PIL import Image
from customtkinter import *
from tkinter.filedialog import askopenfilenames
from tkinter import ttk, font
from models import PlayList
from tinytag import TinyTag
import threading
import time
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


class MainClass:
    def __init__(self, root: list) -> None:
        self.playlist = {}
        self.root = root
        self.pause = False
        self.start = False
        self.x_pos = 2
        self.duration = None
        self.duratoin_old = None
        self.song_id = None
        self.song_id_old = None
        self.total_songs = 0
        
        # кнопка play
        img = CTkImage(light_image=Image.open("IMG/play.ico"), size=(24, 24))
        self.btn_play = CTkButton(self.root[1], image=img, text="", width=24, height=24,
                                  command=self.press_play_button)
        self.btn_play.place_configure(x=self.x_pos, y=2)

        # кнопка stop
        img = CTkImage(light_image=Image.open("IMG/stop.ico"), size=(24, 24))
        self.btn_stop = CTkButton(self.root[0], image=img, text="", width=24, height=24,
                                  command=self.press_stop_button)
        self.btn_stop.place_configure(x=260, y=112)

        # кнопка next
        img = CTkImage(light_image=Image.open("IMG/next.ico"), size=(24, 24))
        self.btn_next = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_next.place_configure(x=300, y=112)

        # бегунок slider
        self.slider_volume = CTkSlider(self.root[2], from_=0, to=100, height=12, width=95)
        self.slider_volume.place_configure(x=5, y=17)

        # кнопка add
        img = CTkImage(light_image=Image.open("IMG/add.ico"), size=(24, 24))
        self.btn_add = CTkButton(self.root[0], image=img, text="", width=24, height=24, command=self.thred_do_file_add)
        self.btn_add.place_configure(x=5, y=461)

        # кнопка delete
        img = CTkImage(light_image=Image.open("IMG/delete.ico"), size=(24, 24))
        self.btn_delete = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_delete.place_configure(x=45, y=461)

        # кнопка clear
        img = CTkImage(light_image=Image.open("IMG/clear.ico"), size=(24, 24))
        self.btn_clear = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_clear.place_configure(x=85, y=461)

        # кнопка exit
        img = CTkImage(light_image=Image.open("IMG/exit.ico"), size=(24, 24))
        self.btn_exit = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_exit.place_configure(x=407, y=461)
        
         # кнопка up
        img = CTkImage(light_image=Image.open("IMG/up.ico"), size=(24, 24))
        self.btn_up = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_up.place_configure(x=200, y=461)

        # кнопка down
        img = CTkImage(light_image=Image.open("IMG/down.ico"), size=(24, 24))
        self.btn_down = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_down.place_configure(x=240, y=461)
        
        # кнопка pin
        img = CTkImage(light_image=Image.open("IMG/pin.ico"), size=(24, 24))
        self.btn_pin = CTkButton(self.root[0], image=img, text="", width=24, height=24)
        self.btn_pin.place_configure(x=280, y=461)
        
        # список tree
        style = ttk.Style()
        style.theme_use("clam")
        font.nametofont('TkHeadingFont').configure(family="Calibri", size=10)
        style.configure(".", font=('Calibri', 9, "roman"), foreground="black")
        columns = ("name_song", "time_song")
        self.tree = Treeview(self.root[3], name="tree", columns=columns, show="headings", height=13, padding=2)
        ttk.Style().configure("Treeview", background="black", foreground="white", fieldbackground="black")
        self.tree.pack(side=LEFT)
        self.tree.heading("name_song", text="Song`s name", anchor=W)
        self.tree.heading("time_song", text="Time", anchor=W)
        self.tree.column("#1", stretch=NO, width=348, anchor=W)
        self.tree.column("#2", stretch=NO, width=70, anchor=E)
        self.tree.bind("<Return>", self.bind_tree_change_song)
        self.tree.bind("<Double-ButtonPress-1>", self.bind_tree_change_song)
        scrollbar = ttk.Scrollbar(self.root[3], orient=VERTICAL, command=self.tree.yview)
        self.tree["yscrollcommand"] = scrollbar.set
        scrollbar.place(y=0, x=374)
        scrollbar.pack(side="right", fill="y")
        self.update_playlist()
        
    def bind_tree_change_song(self, event):
        self.press_stop_button()
        self.press_play_button()

    def thred_do_file_add(self):
        for thred in threading.enumerate():
                if "file_add" in str(thred):
                    return
        else:
            threading.Thread(target=self.file_add, args=(), daemon=True).start()

    def file_add(self):
        allowed_extensions = ('.mp3', '.wav', ".mp4", '.avi')
        song_files = []
        songs = list(askopenfilenames())
        for element in songs:
            for ext in allowed_extensions:
                if element.find(ext) != -1:
                    song_files += (element, )
                    break
        if song_files == "":
            return
        
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
        self.x_pos = 2
        self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/play.ico"), size=(24, 24)))
        self.btn_play.place_configure(x=self.x_pos)
        self.btn_play.update()
        pygame.mixer.music.stop()
        
    def press_play_button(self):
        if not self.start:
            self.start = True
            path = self.playlist[int(self.tree.selection()[0])][1]
            self.duration = self.playlist[int(self.tree.selection()[0])][3]
            
            if self.song_id_old != None:
                self.tree.tag_configure('white', foreground='white')
                self.tree.item(self.song_id_old, tag='white')
                self.tree.set(self.song_id, 1, self.duratoin_old)
            
            self.song_id = str(self.tree.selection()[0])
            self.song_id_old = self.song_id
            self.duratoin_old = self.playlist[int(self.tree.selection()[0])][2]     
            self.tree.tag_configure('pink', foreground='pink')
            self.tree.item(self.song_id, tag='pink')
            
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(loops=0)
            for thred in threading.enumerate():
                if "play_music" in str(thred):
                    return
            else:
                threading.Thread(target=self.play_music, args=(), daemon=True).start()
                return
        
        if self.start and not self.pause:
            self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/pause.ico"), size=(24, 24)))
            self.pause = True
            pygame.mixer.music.pause()
        else:
            self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/play.ico"), size=(24, 24)))
            self.pause = False
            pygame.mixer.music.unpause()
            threading.Thread(target=self.play_music, args=(), daemon=True).start()

    def play_music(self):
        while get_time(pygame.mixer.music.get_pos()) != self.duration:
            if self.pause or not self.start:
                return
            pygame.mixer.music.set_volume(self.slider_volume.get() / 100)
            self.tree.set(self.song_id, 1, get_time(pygame.mixer.music.get_pos()))
            self.x_pos += 1
            self.btn_play.place_configure(x=self.x_pos)
            self.btn_play.update()
            time.sleep(0.4)
        pygame.mixer.music.stop()
        

    def update_playlist(self):
        if self.tree.selection() != ():
            for delete_row in self.tree.get_children():
                self.tree.delete(delete_row)
        for row in PlayList.select():
            if os.path.exists(f"{row.song_path}"):
                self.tree.insert("", END, iid=str(row.id), values=(row.song_name, row.duration))
            self.playlist[row.id] = [row.song_name, row.song_path, row.duration, row.duration_sec]
        
    def play_time_duration():
        # 
        #     run_string_news()
        #     if get_flags("addplay") == 1:
        #         t
        #     pygame.mixer.music.set_volume(volume_scale.get() / 100)
        #     progress.config(value=pygame.mixer.music.get_pos())
        #     progress.update()
        #     label_time.config(text=get_time(pygame.mixer.music.get_pos()), fg="black")
        #     label_time.update()
        # set_flags('music_play', 0)
        # next_song()
        pass