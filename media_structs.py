'''
    This file contains the objects used to store media data. It will be helpful to have a
    strcutured system for storing needed data for media. Ideallly this would be a c strcut
    but this is the most light weight option I can think of that is available in python.
    no getters or setters because these are not real objects they're *structs*
'''

class _Media():
    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def __str__(self):
        return f"{self.name} - {self.path}"


class Movie(_Media):
    def __init__(self, name: str, last_watched: int, path: str):
        super().__init__(name=name, path=path)
        self.last_watched = last_watched

    def __str__(self):
        return f"{super().__str__()} - Last watched: {self.last_watched}"
    

class Season(_Media):
    def __init__(self, name: str, last_watched: int, path: str):
        super().__init__(name=name, path=path)
        self.last_watched = last_watched

    def __str__(self):
        return f"{super().__str__()} - Last watched: {self.last_watched}"


class Show(_Media):
    def __init__(self, name: str, path, seasons: list[Season]):
        super().__init__(name=name, path=path)
        self.seasons = seasons

    def __str__(self):  
        seasons_str = ""
        for i in self.seasons:
            seasons_str += f" {i}" 

        return f"{super().__str__()} - Seasons: {seasons_str}"
