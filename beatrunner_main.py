from audio import *
from gamevisuals import *
from transition import *


# MAINWIDGET FOR TESTING GAME VISUALS INDEPENDENTLY OF THE ENTIRE GAME
class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()
        self.anim_group = AnimGroup()
        self.other_label = topright_label()
        self.game_data = GameData()
        self.audio_manager = AudioManager(self.game_data.audio_file_name)

        self.song_data = SongData()
        self.song_data.read_data(*self.game_data.song_data_files)
        self.game_display = GameDisplay(self.song_data.blocks, self.song_data.powerups, self.audio_manager, self.other_label)
        self.anim_group.add(self.game_display)

        self.playing = False

        self.canvas.add(self.anim_group)

        self.label = topleft_label()
        self.add_widget(self.label)

        self.add_widget(self.other_label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'p':  # PAUSE
            self.game_display.toggle()

        if keycode[1] == 'z':
            pass

        if keycode[1] == 't':
            self.game_data.transition()
            self.audio_manager.start_transition_song(self.game_data.audio_file_name)

        if keycode[1] == 'w':
            self.audio_manager.play_jump_effect()
            self.game_display.on_jump()

        #############################################
        # Testing functions
        # These are put in by Rodrigo and will be taken out once
        # the thing is complete
        #############################################
        if keycode[1] == "u":
            self.audio_manager.speedup()
        if keycode[1] == "d":
            self.audio_manager.slowdown()

        if keycode[1] == "w":
            self.audio_manager.play_win_effect()

        if keycode[1] == "l":
            self.audio_manager.play_lose_effect()

        if keycode[1] == "b":
            self.audio_manager.bass_boost()

    def on_key_up(self, keycode):
        self.game_display.on_fall()

        if keycode[1] == "w":
            self.audio_manager.stop_win_effect()

        if keycode[1] == "l":
            self.audio_manager.stop_lose_effect()

        if keycode[1] == "b":
            self.audio_manager.reset_filter()

        if keycode[1] == 't':
            self.song_data.read_data(*self.game_data.song_data_files)  ## transition
            self.game_display.transition(self.game_data.player_image, self.game_data.ground_image,
                                         self.game_data.block_image)
            self.audio_manager.end_transition_song()

    def on_update(self) :
        self.label.text = "Welcome to Beat Runner\nw to jump\nhold down t to transition\nLevel "+str(self.game_data.level + 1) + "\n"
        self.label.text += "Score: " + str(self.audio_manager.score) + "\n"
        self.anim_group.on_update()
        self.audio_manager.on_update()
        self.game_display.update_frame(self.audio_manager.get_current_frame())


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
            self.blocks.append((float(blockline[0]), int(blockline[2]), int(blockline[3])))
        powerups = self.lines_from_file(poweruppath)
        for p in powerups:
            powerup = p.split()
            self.powerups.append((float(powerup[0]), int(powerup[2]), str(powerup[3])))

run(MainWidget)