from customtkinter import *
from os import path
from models import PlayList


def main():
    root = CTk()
    
    root.mainloop()
    

if __name__ == "__main__":
    if not path.exists('database/bot_base.db'):
        PlayList.create_table()
    main()