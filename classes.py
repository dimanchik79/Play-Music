from tkinter.ttk import Treeview
from PIL import Image
from customtkinter import *
from tkinter import ttk, font, filedialog
from models import PlayList
import threading
import time


class MainClass:
    def __init__(self, root: list) -> None:
        self.playlist = {}
        self.root = root
        self.pause = False
        self.start = False
        self.x_pos = 2

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
        self.slider_volume.place()

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

        # список tree
        style = ttk.Style()
        style.theme_use("clam")
        font.nametofont('TkHeadingFont').configure(size=10)
        style.configure(".", font=('Calibri', 10, "roman"), foreground="black")
        columns = ("name_song", "time_song")
        self.tree = Treeview(self.root[3], name="tree", columns=columns, show="headings", height=13, padding=5)
        ttk.Style().configure("Treeview", foreground="#BAF300", fieldbackground="dark slate grey")
        self.tree.pack(side=LEFT)
        self.tree.heading("name_song", text="Song`s name", anchor=W)
        self.tree.heading("time_song", text="Time", anchor=W)
        self.tree.column("#1", stretch=NO, width=330, anchor=W)
        self.tree.column("#2", stretch=NO, width=80, anchor=E)
        # tree.bind("<Return>", keypress_tree_change_song)
        # tree.bind("<Double-ButtonPress-1>", keypress_tree_change_song)
        scrollbar = ttk.Scrollbar(self.root[3], orient=VERTICAL, command=self.tree.yview)
        self.tree["yscrollcommand"] = scrollbar.set
        scrollbar.place(y=0, x=374)
        scrollbar.pack(side="right", fill="y")
        self.update_playlist()

    def thred_do_file_add(self):
        if "file_add" in threading.enumerate():
            return
        else:
            threading.Thread(target=self.file_add, args=(), daemon=True).start()

    def file_add(self):


    def press_stop_button(self):
        self.start = False
        self.pause = False
        self.x_pos = 2
        self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/play.ico"), size=(24, 24)))
        self.btn_play.place_configure(x=self.x_pos)
        self.btn_play.update()

    def press_play_button(self):
        if not self.start:
            self.start = True
            threading.Thread(target=self.play_music, args=(), daemon=True).start()
            return

        if self.start and not self.pause:
            self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/pause.ico"), size=(24, 24)))
            self.pause = True
        else:
            self.btn_play.configure(image=CTkImage(light_image=Image.open("IMG/play.ico"), size=(24, 24)))
            self.pause = False
            threading.Thread(target=self.play_music, args=(), daemon=True).start()

    def play_music(self):
        while True:
            if self.pause or not self.start:
                return
            self.x_pos += 1
            self.btn_play.place_configure(x=self.x_pos)
            self.btn_play.update()
            time.sleep(0.4)

    def update_playlist(self):
        if self.tree.selection() != ():
            for delete_row in self.tree.get_children():
                self.tree.delete(delete_row)

        for row in PlayList.select():
            self.playlist[row.id] = [row.song_name, row.song_path, row.duration, row.duration_sec]
        print(self.playlist)

