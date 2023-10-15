from peewee import *

"""В модуле реализованы модели базы банных
   с помощью библиотеки PEEWEE"""

DB = SqliteDatabase('DB/playlist.db')


class BaseModel(Model):
    class Meta:
        database = DB


class PlayList(BaseModel):
    song_name = CharField(max_length=250)
    song_path = CharField(max_length=250)
    duration = CharField(max_length=8)
    duration_sec = FloatField()
    list_name = CharField(max_length=250)


