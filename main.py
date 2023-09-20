from customtkinter import *
from os import path
from models import PlayList
from classes import MainClass


def main():
    root = CTk()
    root.title("MUSIC PLAYER")
    root.geometry("450x500")
    root.resizable(False, False)

    frame_main = CTkFrame(root, height=100, width=440, border_width=1, border_color="black")
    frame_main.place_configure(x=5, y=5, bordermode="inside")
    frame_main.place()

    frame_progress = CTkFrame(root, height=35, width=250, border_width=1, border_color="black")
    frame_progress.place_configure(x=5, y=110, bordermode="inside")
    frame_progress.place()

    frame_volume = CTkFrame(root, height=35, width=103, border_width=1, border_color="black")
    frame_volume.place_configure(x=342, y=110, bordermode="inside")
    frame_volume.place()
    lbl = CTkLabel(frame_volume, text="volume", font=("Calibri", 9), height=8)
    lbl.place_configure(x=5, y=5)
    lbl.place()

    frame_list = CTkFrame(root, height=300, width=440, border_width=1, border_color="black")
    frame_list.place_configure(x=5, y=150, bordermode="inside")
    frame_list.place()

    all_widget = MainClass(root=[root, frame_progress, frame_volume, frame_list])

    root.mainloop()
    

if __name__ == "__main__":
    if not path.exists('database/bot_base.db'):
        PlayList.create_table()
    main()
