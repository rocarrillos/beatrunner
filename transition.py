AUDIO_FILES = ["data/babyshark.wav", "data/closerremix.wav", "data/migenteremix.wav"]
SONG_DATA_FILES = [("data/babyshark_blocks.txt", "data/babyshark_powerups.txt"),
                    ("data/closer_blocks.txt", "data/closer_powerups.txt"),
                    ("data/migente_blocks.txt", "data/migente_powerups.txt")]

PLAYER_IMAGES = ["img/shark.png","img/lizard.png", "img/eagle.jpg"]
BLOCK_IMAGES = ["img/wav.png", "img/brick.jpg", "img/cloud.png"]
GROUND_IMAGES = ["img/sand.png", "img/grass.jpg", "img/blank.png"]


class GameData(object):
    def __init__(self):
        super(GameData, self).__init__()
        self.level = 0
        self.audio_file_name = AUDIO_FILES[0]
        self.song_data_files = SONG_DATA_FILES[0]

        self.player_image = PLAYER_IMAGES[0]
        self.block_image = BLOCK_IMAGES[0]
        self.ground_image = GROUND_IMAGES[0]

    def transition(self):
        self.level += 1
        self.audio_file_name = AUDIO_FILES[self.level]
        self.song_data_files = SONG_DATA_FILES[self.level]
        self.player_image = PLAYER_IMAGES[self.level]
        self.block_image = BLOCK_IMAGES[self.level]
        self.ground_image = GROUND_IMAGES[self.level]

