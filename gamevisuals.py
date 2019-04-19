# VISUAL WRAPPER CLASS FOR GAME

from common.core import *
from common.audio import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *
from common.gfxutil import *
from common.writer import *
from kivy.core.window import Window
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.core.image import Image
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.clock import Clock as kivyClock

import random
import numpy as np
import bisect

SCREEN_WIDTH = Window.size[0]
SCREEN_HEIGHT = Window.size[1]
PLAYER_X = int(SCREEN_WIDTH / 6)
SECONDS_FROM_RIGHT_TO_PLAYER = 4
RIGHT_SPEED = (SCREEN_WIDTH - PLAYER_X)/SECONDS_FROM_RIGHT_TO_PLAYER  # pixels/second
FALL_SPEED = ()
GROUND_Y = int(SCREEN_HEIGHT / 5)

PLAYER_HEIGHT = int(SCREEN_HEIGHT / 5)
PLAYER_WIDTH = int(SCREEN_HEIGHT / 15)


class Player(InstructionGroup):
    def __init__(self):
        super(Player, self).__init__()
        self.pos = (PLAYER_X, GROUND_Y)
        self.texture = Image('img/stick_figure.jpg').texture
        self.add(Color(1,1,1,0.5))
        self.rect = Rectangle(pos=self.pos, size=(PLAYER_WIDTH, PLAYER_HEIGHT))
        self.add(self.rect)

        self.jump_anim = None
        self.fall_on = False

        self.dt = 0

    def on_jump(self):
        current_y = self.rect.pos[1]
        max_y = self.rect.pos[1] + int(7 * SCREEN_HEIGHT / 20)
        slow_down_y_1 = self.rect.pos[1] + int(SCREEN_HEIGHT / 5)
        slow_down_y_2 = self.rect.pos[1] + int(3 * SCREEN_HEIGHT / 10)
        self.jump_anim = KFAnim((0,current_y), (0.1, slow_down_y_1), (0.2, slow_down_y_2), (0.35, max_y))

    def on_fall(self):
        self.fall_on = True

    def on_update(self, dt):
        if self.jump_anim:
            self.rect.pos = self.rect.pos[0], self.jump_anim.eval(self.dt)
            self.dt += dt
        elif self.fall_on:
            ## PHYSICS FALLING CODE

        if self.jump_anim and self.dt > 0.35:
            self.dt = 0
            self.fall_on = True
            self.jump_anim = None

        ## WATCH FOR COLLISIONS
        return True


class Block(InstructionGroup):
    def __init__(self, pos, color):
        super(Block, self).__init__()


class Powerup(InstructionGroup):
    def __init__(self, pos, powerup_type):
        super(Powerup, self).__init__()


class GameDisplay(InstructionGroup):
    def __init__(self, song_data, powerup_data):
        super(GameDisplay, self).__init__()
        self.song_data = song_data
        self.powerup_data = powerup_data
        self.color = Color(1,1,1)
        self.add(self.color)

        self.add(Player())

        self.current_frame = 0
        self.current_block = 0  # current block to add from song_data
        self.current_powerup = 0

        self.blocks = set()
        self.powerups = set()

        self.paused = True

    def toggle(self):
        self.paused = not self.paused

    def on_button_down(self, key_pressed):
        if key_pressed == 'w':
            self.jump_on()

    def on_button_up(self, key_pressed):
        self.jump_off()

    # call every frame to make gems and barlines flow down the screen
    def on_update(self, dt):
        if not self.paused:
            removed_items = set()

            # UPDATE EACH GEM AND BAR, AND TRACK IF THEY ARE REMOVED OR NOT FROM THE GAME FRAME
            # For gems, track if a gem was completely missed.
            # remove removed items from the animation.
            for block in self.blocks:
                kept = block.on_update(dt)
                if not kept:
                    removed_items.add(block)

            for powerup in self.powerups:
                kept = powerup.on_update(dt)
                if not kept:
                    removed_items.add(powerup)

            for item in removed_items:
                self.remove(item)

            self.powerups = set([p for p in self.powerups if p not in removed_items])
            self.blocks = set([b for b in self.blocks if b not in removed_items])

            # ADD NEW BLOCKS AND POWERUPS
            # COMPARE ANNOTATION NOTES TO CURRENT FRAME AND ADD NEW OBJECTS ACCORDINGLY
            if self.current_block < len(self.song_data) and self.current_frame / Audio.sample_rate > \
                            self.song_data[self.current_block][0] - SECONDS_FROM_RIGHT_TO_PLAYER:
                y_pos = self.song_data[self.current_block][1] - 1
                new_block = Block((self.index_to_y[y_pos], SCREEN_WIDTH), Color(1,1,1))
                self.blocks.add(new_block)
                self.add(new_block)
                self.current_block += 1

            if self.current_powerup < len(self.powerup_data) and self.current_frame / Audio.sample_rate > self.powerup_data[
                self.current_powerup] - SECONDS_FROM_RIGHT_TO_PLAYER:
                y_pos = self.powerup_data[self.current_powerup][1] - 1
                p_type = self.powerup_data[self.current_powerup][2] - 1
                new_powerup = Powerup((self.index_to_y[y_pos], SCREEN_WIDTH), p_type)
                self.powerups.add(new_powerup)
                self.add(new_powerup)
                self.current_powerup += 1

        return True

    # update the local current frame variable
    def update_frame(self, frame):
        self.current_frame = frame
