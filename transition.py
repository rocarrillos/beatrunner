AUDIO_FILES = ["data/babyshark.wav", "data/closerremix.wav", "data/migente_short.wav"]
SONG_DATA_FILES = [("data/babyshark_blocks.txt", "data/babyshark_powerups.txt"),
                    ("data/closer_blocks.txt", "data/closer_powerups.txt"),
                    ("data/migente_blocks.txt", "data/migente_powerups.txt")]

PLAYER_IMAGES = ["img/shark.png","img/lizard.png", "img/eagle.jpg"]
BLOCK_IMAGES = ["img/wav.png", "img/brick.jpg", "img/cloud.png"]
GROUND_IMAGES = ["img/sand.png", "img/grass.jpg", "img/blank.png"]


##
# Game data file. This file basically stores all file metadata and image names
# and iterates through them on transition
# To add a new level, just
#  - add the audio path to AUDIO_FILES
#  - add the blocks and powerup paths in tuple form to SONG_DATA_FILES
#  - add a new player image to PLAYER_IMAGES
#  - add a new block image to BLOCK_IMAGES
#  - add a new ground image to GROUND_IMAGES
##
class GameData(object):
    def __init__(self):
        super(GameData, self).__init__()
        self.level = 0
        self.audio_file_name = AUDIO_FILES[self.level]
        self.song_data_files = SONG_DATA_FILES[self.level]

        self.player_image = PLAYER_IMAGES[self.level]
        self.block_image = BLOCK_IMAGES[self.level]
        self.ground_image = GROUND_IMAGES[self.level]
        self.next_song_name = AUDIO_FILES[self.level + 1]

    def get_song(self):
        return self.audio_file_name

    def get_next_song(self):
        return self.next_song_name

    def transition(self):
        self.level += 1
        self.audio_file_name = AUDIO_FILES[self.level]
        self.song_data_files = SONG_DATA_FILES[self.level]
        self.player_image = PLAYER_IMAGES[self.level]
        self.block_image = BLOCK_IMAGES[self.level]
        self.ground_image = GROUND_IMAGES[self.level]
        self.next_song_name = AUDIO_FILES[self.level + 1 ] if self.level < len(AUDIO_FILES) else None

