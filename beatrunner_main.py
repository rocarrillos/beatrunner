from audio import *
from gamevisuals import *


# MAINWIDGET FOR TESTING GAME VISUALS INDEPENDENTLY OF THE ENTIRE GAME
class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()
        self.anim_group = AnimGroup()
        self.audio_manager = AudioManager(## file ##)
        self.song_data = SongData()
        self.song_data.read_data("test_data/block_data.txt", "test_data/powerup_data.txt")
        self.game_display = GameDisplay(self.song_data.blocks, self.song_data.powerups, self.audio_manager)
        self.anim_group.add(self.game_display)

        self.playing = False

        self.canvas.add(self.anim_group)

        self.label = topleft_label()
        self.add_widget(self.label)

    def on_key_down(self, keycode, modifiers):
        self.game_display.on_button_down(keycode[1])

        if keycode[1] == 'z':
            pass
        
        if keycode[1] == 'w':
            self.audio_manager.play_jump_effect()

    def on_key_up(self, keycode):
        self.game_display.on_button_up(keycode[1])

    def on_update(self) :
        self.label.text = "Welcome to Beat Runner\n"
        self.anim_group.on_update()


# holds data for blocks and powerups.
class SongData(object):
    def __init__(self):
        super(SongData, self).__init__()
        self.blocks = []  # list of tuples (seconds, index), ST index is 1-5
        self.powerups = []  # list of ints for frames to add a barline

    # from lab 2
    def lines_from_file(self, filename):
        f = open(filename)
        g = f.readlines()
        f.close()
        return g

    # read the blocks and powerup data. You may want to add a secondary filepath
    # argument if your poweruppath data is stored in a different txt file.
    def read_data(self, blockpath, poweruppath):
        blocklines = self.lines_from_file(blockpath)
        for line in blocklines:
            blockline = line.split()
            for i in range(2, len(blockline)):
                self.blocks.append((float(blockline[0]), int(blockline[i])))
        powerups = self.lines_from_file(poweruppath)
        for p in powerups:
            powerup = p.split()
            self.powerups.append((float(powerup[0]), str(powerup[2])))

run(MainWidget)