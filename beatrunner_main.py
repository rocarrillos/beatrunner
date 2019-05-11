from audio import *
from gamevisuals import GameDisplay, MenuDisplay, TutorialDisplay
from transition import *

import time

# MAINWIDGET FOR TESTING GAME VISUALS INDEPENDENTLY OF THE ENTIRE GAME
class MainWidget(BaseWidget) :
    def __init__(self):
        super(MainWidget, self).__init__()
        self.anim_group = AnimGroup()
        self.other_label = topright_label()
        self.other_label.text = ""
        self.game_data = GameData()
        self.audio_manager = AudioManager(self.game_data.get_song(), self.game_data.get_next_song())
        self.screen = "menu"
        self.song_data = SongData()
        self.song_data.read_data(*self.game_data.song_data_files, 0)
        self.game_display = GameDisplay(self.song_data.blocks, self.song_data.powerups, self.audio_manager, self.other_label, self.handle_transition)
        self.menu_display = MenuDisplay()
        self.tutorial_display = TutorialDisplay(self.song_data.blocks, self.song_data.powerups, self.audio_manager, self)
        self.anim_group.add(self.menu_display)

        self.playing = False
        self.lifetime = 0
        self.button = 1
        self.prev_time = time.time()
        self.new_time = time.time()

        self.canvas.add(self.anim_group)

        self.label = topleft_label()
        self.add_widget(self.label)

        self.add_widget(self.other_label)

    def on_key_down(self, keycode, modifiers):
        if keycode[1] == 'p':  # PAUSE/PLAY
            if self.screen == "game":
                self.game_display.toggle()
                self.audio_manager.toggle()
                self.playing = not self.playing

        # if keycode[1] == 't':
        #     self.game_data.transition()
        #     self.audio_manager.start_transition_song(self.game_data.audio_file_name)

        if keycode[1] == 'w':
            if self.screen == "game":
                self.audio_manager.play_jump_effect()
                self.game_display.on_jump()
            if self.screen == "tutorial":
                self.audio_manager.play_jump_effect()
                self.tutorial_display.on_jump()

        if keycode[1] == "m":
            if self.screen == "game":
                if not self.playing:
                    self.anim_group.remove(self.game_display)
                    self.anim_group.add(self.menu_display)
                    self.screen = "menu"
            if self.screen == "tutorial":
                self.anim_group.remove(self.tutorial_display)
                self.anim_group.add(self.menu_display)
                self.screen = "menu"

        if keycode[1] == "1":
            if self.screen == "menu":
                self.anim_group.remove(self.menu_display)
                self.anim_group.add(self.game_display)
                self.screen = "game"

        if keycode[1] == "t":
            if self.screen == "menu":
                if not self.playing:
                    self.anim_group.remove(self.menu_display)
                    self.anim_group.add(self.tutorial_display)
                    self.screen = "tutorial"

        if keycode[1] == "up":
            if self.screen == "menu":
                self.button += 1
                self.menu_display.highlight_button(1)

        if keycode[1] == "down":
            if self.screen == "menu":
                self.button -= 1
                self.menu_display.highlight_button(-1)

        if keycode[1] == "enter":
            if self.screen == "menu":
                if self.button % 2 == 0:
                    self.anim_group.remove(self.menu_display)
                    self.anim_group.add(self.tutorial_display)
                    self.screen = "tutorial"
                if self.button % 2 == 1:
                    self.anim_group.remove(self.menu_display)
                    self.anim_group.add(self.game_display)
                    self.screen = "game"
            if self.screen == "tutorial":
                print("give instructins")
        

    def on_key_up(self, keycode):
        if keycode[1] == "w":
            if self.screen == "game":
                self.game_display.on_fall()
            if self.screen == "tutorial":
                self.tutorial_display.on_fall()

        # if keycode[1] == 't':
        #     self.handle_transition()
            
    def handle_transition(self):
        self.game_data.transition()
        self.audio_manager.add_transition_song(self.game_data.audio_file_name)
        self.song_data.read_data(*self.game_data.song_data_files, self.lifetime)  ## transition
        self.audio_manager.end_transition_song(self.game_data.get_next_song())
        self.game_display.graphics_transition(self.game_data.player_images, self.game_data.ground_image,
                                        self.game_data.bg_image, self.game_data.block_image)

    def on_update(self) :
        if self.screen == "game":
            self.label.text = "Level "+str(self.game_data.level + 1) + "\n"
            # Welcome to Beat Runner\n[p] play/pause [w] jump [t hold] transition\n
            self.label.text += "Score: " + str(self.audio_manager.score) + "\n"
            if not self.playing:
                self.label.text += "Press P to play"
        if self.screen == "tutorial":
            self.label.text = "Tutorial Mode\n"
        if self.screen == "menu":
            self.label.text = ""
        self.anim_group.on_update()
        self.audio_manager.on_update()
        self.game_display.update_frame(self.audio_manager.get_current_frame())
        if self.playing:
            self.prev_time = self.new_time
            self.new_time = time.time()
            self.lifetime += self.new_time - self.prev_time


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
    def read_data(self, blockpath, poweruppath, time):
        print(time)
        blocklines = self.lines_from_file(blockpath)

        for line in blocklines:
            blockline = line.split()
            self.blocks.append((time + float(blockline[0]), int(blockline[2]), int(blockline[3])))
        powerups = self.lines_from_file(poweruppath)
        for p in powerups:
            powerup = p.split()
            self.powerups.append((float(powerup[0]), int(powerup[2]), str(powerup[3])))


run(MainWidget)