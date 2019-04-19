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

BLOCK_HEIGHT = int(SCREEN_HEIGHT / 15)
BLOCK_UNIT_LENGTH = int(SCREEN_WIDTH/4)

PLAYER_HEIGHT = int(SCREEN_HEIGHT / 5)
PLAYER_WIDTH = int(SCREEN_HEIGHT / 15)

POWERUP_LENGTH = int(SCREEN_WIDTH/20)

TEXTURES = {'rewind':None}

gravity = np.array((0, -1800))


class Player(InstructionGroup):
    def __init__(self, listen_collision_blocks=None, listen_collision_ground=None, listen_collision_powerup=None):
        super(Player, self).__init__()
        self.pos = (PLAYER_X, GROUND_Y)
        self.texture = Image('img/stick_figure.jpg').texture
        self.add(Color(1,1,1,0.5))
        self.rect = Rectangle(pos=self.pos, size=(PLAYER_WIDTH, PLAYER_HEIGHT))
        self.add(self.rect)

        self.jump_anim = None
        self.fall_on = False
        self.fall_vel = np.array((0,0), dtype=np.float)

        self.dt = 0

        self.listen_collision_blocks = listen_collision_blocks
        self.listen_collision_ground = listen_collision_ground
        self.listen_collision_powerup = listen_collision_powerup

    def get_pos(self):
        return self.rect.pos

    def set_y(self, new_y):
        self.rect.pos = self.rect.pos[0], new_y

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
            self.fall_vel += gravity*dt
            self.rect.pos += self.fall_vel * dt

        if self.jump_anim and self.dt > 0.35:
            self.dt = 0
            self.fall_on = True
            self.jump_anim = None

        if self.listen_collision_blocks:
            collision = self.listen_collision_blocks(self) or self.listen_collision_ground(self)
            if collision:
                self.fall_on = False
                self.fall_vel = np.array((0, 0), dtype=np.float)
            else:
                self.fall_on = True
                self.dt = 0
                self.jump_anim = None

            powerup_collision = self.listen_collision_powerup(self)
        return True


class Block(InstructionGroup):
    def __init__(self, pos, color, units):
        super(Block, self).__init__()
        self.pos = pos
        self.color = color
        self.add(self.color)
        self.block = Rectangle(pos=self.pos, size=[units * BLOCK_UNIT_LENGTH, BLOCK_HEIGHT])
        self.add(self.block)

    def on_update(self, dt):
        self.block.pos -= np.array([dt* RIGHT_SPEED, 0])
        return self.fell_offscreen()

    def fell_offscreen(self):
        return not self.block.pos[0] + self.block.size[0] < 0

    def get_pos(self):
        return self.block.pos

    def get_size(self):
        return self.block.size


class Ground(InstructionGroup):
    def __init__(self):
        super(Ground, self).__init__()
        self.rect = Rectangle(pos=(0,0), size=[SCREEN_WIDTH, GROUND_Y])

    def on_update(self, dt):
        return True

    def get_pos(self):
        return self.rect.pos


class Powerup(InstructionGroup):
    def __init__(self, pos, powerup_type):
        super(Powerup, self).__init__()
        self.pos = pos
        self.texture = TEXTURES[powerup_type]
        self.powerup = Rectangle(pos=self.pos, size=[POWERUP_LENGTH, POWERUP_LENGTH],texture=self.texture)
        self.add(self.powerup)
        self.triggered = False

    def on_update(self, dt):
        self.powerup.pos -= np.array([dt * RIGHT_SPEED, 0])
        return self.fell_offscreen()

    def fell_offscreen(self):
        return not self.powerup.pos[0] + self.powerup.size[0] < 0 or self.triggered

    def get_pos(self):
        return self.powerup.pos

    def get_size(self):
        return self.powerup.size


class GameDisplay(InstructionGroup):
    def __init__(self, song_data, powerup_data):
        super(GameDisplay, self).__init__()
        self.song_data = song_data
        self.powerup_data = powerup_data
        self.color = Color(1,1,1)
        self.add(self.color)

        self.player = Player(listen_collision_blocks=self.listen_collision_block,
                        listen_collision_ground=self.listen_collision_ground,
                             listen_collision_powerup=self.listen_collision_powerup)

        self.add(self.player)
        self.ground = Ground()
        self.add(self.ground)

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
            self.player.on_jump()

    def on_button_up(self, key_pressed):
        if key_pressed == 'w':
            self.player.on_fall()

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

    def listen_collision_block(self, player):
        for block in self.blocks:
            if block.get_pos()[0] < player.get_pos()[0] < block.get_pos()[0] + block.get_size()[0]:
                if block.get_pos()[1] < player.get_pos()[1] <= block.get_pos()[1] + BLOCK_HEIGHT:
                    # FALL ONTO A NEW BLOCK
                    player.set_y(block.get_pos()[1] + BLOCK_HEIGHT)
                    return True
                elif block.get_pos()[1] < player.get_pos()[1] + PLAYER_HEIGHT < block.get_pos()[1] + BLOCK_HEIGHT:
                    # jump up into a block (just fall back down)
                    return False
        return False

    def listen_collision_ground(self, player):
        if player.get_pos()[1] <= GROUND_Y:
            player.set_y(GROUND_Y)
            return True
        return False

    def listen_collision_powerup(self, player):
        for powerup in self.powerups:
            ## TODO(clhsu): track powerup collisions
            pass
