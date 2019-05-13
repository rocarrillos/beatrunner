AUDIO_FILES = ["data/babyshark.wav", "data/closerremix_98bpm.wav", "data/migente_short.wav"]
SONG_DATA_FILES = [("data/babyshark_blocks.txt", "data/babyshark_powerups.txt"),
                    ("data/closer_blocks.txt", "data/closer_powerups.txt"),
                    ("data/migente_blocks.txt", "data/migente_powerups.txt")]

PLAYER_IMAGES = [["img/shark.png", "img/shark_jump.png","img/shark_fall.png"],["img/dinosaur.png","img/dinosaur_jump.png","img/dinosaur_fall.png"], ["img/bird.png","img/bird_jump.png","img/bird_fall.png"]]
BLOCK_IMAGES = ["img/wav.png", "img/forest_block.png", "img/cloud.png"]
GROUND_IMAGES = ["img/sand.png", "img/rock_ground.png", "img/blank.png"]
BACKGROUND_IMAGES = ["img/ocean.jpg", "img/forest.jpg", "img/clouds.jpg"]
SONG_NAMES = ["Baby Shark","Closer (Shaun \nFrank Remix)", "Mi Gente"]


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
        self.bg_image = BACKGROUND_IMAGES[self.level]
        self.song_name = SONG_NAMES[self.level]

    def get_song(self):
        return self.audio_file_name

    def get_next_song(self):
        return self.next_song_name

    def transition(self):
        self.level += 1
        self.audio_file_name = AUDIO_FILES[self.level]
        self.song_data_files = SONG_DATA_FILES[self.level]
        self.player_images = PLAYER_IMAGES[self.level]
        self.block_image = BLOCK_IMAGES[self.level]
        self.ground_image = GROUND_IMAGES[self.level]
        self.next_song_name = AUDIO_FILES[self.level + 1 ] if self.level < len(AUDIO_FILES) else None

        self.bg_image = BACKGROUND_IMAGES[self.level]
        self.song_name = SONG_NAMES[self.level]
