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
from kivy.core.text import Label as CoreLabel

import random
import numpy as np
import bisect


##
# CONSTANTS
##

SCREEN_WIDTH = Window.size[0]
SCREEN_HEIGHT = Window.size[1]
PLAYER_X = int(SCREEN_WIDTH / 6)
SECONDS_FROM_RIGHT_TO_PLAYER = 3
INIT_RIGHT_SPEED = (SCREEN_WIDTH - PLAYER_X)/SECONDS_FROM_RIGHT_TO_PLAYER  # pixels/second
GROUND_Y = int(SCREEN_HEIGHT / 10)

BLOCK_HEIGHT = int(SCREEN_HEIGHT / 15)
BLOCK_UNIT_LENGTH = int(SCREEN_WIDTH/4)

PLAYER_HEIGHT = int(2 * SCREEN_HEIGHT / 20)
PLAYER_WIDTH = int(SCREEN_HEIGHT / 10)

POWERUP_LENGTH = int(SCREEN_WIDTH / 20)

TEXTURES = {'vocals_boost': Image("img/high.png").texture, 'bass_boost': Image("img/low.png").texture,
            'powerup_note':Image("img/riser.png").texture,"lower_volume":Image("img/arrowdownred.png").texture,
            "raise_volume": Image("img/uparrowred.png").texture, "reset_filter":Image("img/reset_filter.png").texture,
            "reset_speed": Image("img/reset_speed.png").texture,"speedup":Image("img/speedup.png").texture,
            "slowdown": Image("img/ice.png").texture,"reg_to_high":Image("img/reg_to_high.png").texture,
            "sample_on": Image("img/sample_on.png").texture, "sample_off": Image("img/sample_off.png").texture,
            "reset_sample":Image("img/sample_off.png").texture, "start_transition": Image("img/green_spiral.png").texture,
            "end_transition": Image("img/red_spiral.png").texture, "riser":Image("img/riser.png").texture,
            "trophy": Image("img/trophy.png").texture, "danger": Image("img/skull.png").texture,
            "transition_token":Image("img/coin.png").texture, "transition":Image("img/transition_final.png").texture,
            "reset": Image("img/reset.png").texture}
## TODO: CHANGE THIS TO AN R IMAGE OR SOMEHINTG


BPM = {
    "Baby Shark": 120,
    "Closer": 90,
    "Mi Gente": 140
}
# Color constants
BLACK = Color(0, 0, 0)
WHITE = Color(1, 1, 1)
RED = Color(1, 0, 0)
GREEN = Color(0, 1, 0)
BLUE = Color(0, 0, 1)
LBLUE = Color(0.75, 0.75, 1)
YELLOW = Color(1, 1, 0)

gravity = np.array((0, -1800))


##
# PLAYER CLASS -
#   Object that contains player icon
#   arguments: listener functions
#   graphics regarding falling and jumping.
#   listens for collisions with blocks, powerups and ground.
##
class Player(InstructionGroup):
    def __init__(self, listen_collision_above_blocks=None, listen_collision_ground=None, 
            listen_collision_powerup=None, listen_collision_below_blocks=None):
        """
        Object representing a player character.
        @params:
            listen_collision_above_blocks:
            listen_collision_ground:
            listen_collision_powerup:
            listen_collision_below_blocks:
        """
        super(Player, self).__init__()
        self.pos = (PLAYER_X-PLAYER_WIDTH, GROUND_Y)
        self.texture = Image('img/shark.png').texture
        self.jump_texture = Image('img/shark_jump.png').texture
        self.fall_texture = Image('img/shark_fall.png').texture
        self.glow_color = Color(1,1,1)
        self.blue_glow_color = Color(0,0.3,1)
        self.add(self.glow_color)
        self.rect = Rectangle(pos=self.pos, size=(PLAYER_WIDTH, PLAYER_HEIGHT), texture=self.texture)
        self.add(self.rect)

        self.jump_anim = None
        self.fall_on = False
        self.fall_vel = np.array((0,0), dtype=np.float)
        self.airtime = 0.6

        self.dt = 0

        self.listen_collision_above_blocks = listen_collision_above_blocks
        self.listen_collision_below_blocks = listen_collision_below_blocks
        self.listen_collision_ground = listen_collision_ground
        self.listen_collision_powerup = listen_collision_powerup

        self.glow = False
        self.glow_anim = KFAnim((0, 1), (0.3, 0.5), (0.6, 1))
        self.glow_dt = 0

        self.blue_glow = False
        self.blue_glow_anim = KFAnim((0, 1), (0.3, 0.5), (0.6, 1))
        self.blue_glow_dt = 0

    def get_pos(self):
        """
        Arguments:
            None
        Returns:
            (x, y) tuple of the lower left corner of the Player
        """
        return self.rect.pos

    def set_y(self, new_y):
        """
        Arguments:
            new_y (int) 
        Returns:
            None
        """
        self.rect.pos = self.rect.pos[0], new_y

    def on_jump(self):
        if not self.jump_anim and not self.fall_on:
            current_y = self.rect.pos[1]
            max_y = self.rect.pos[1] + int(7 * SCREEN_HEIGHT / 20)
            slow_down_y_1 = self.rect.pos[1] + int(SCREEN_HEIGHT / 5)  # some hardcoded anims right here 
            slow_down_y_2 = self.rect.pos[1] + int(5 * SCREEN_HEIGHT / 20) # Justin Solomon would be proud
            slow_down_y_3 = self.rect.pos[1] + int(6.5 * SCREEN_HEIGHT/20)
            self.jump_anim = KFAnim((0,current_y), (0.25, slow_down_y_1), 
                                    (0.35, slow_down_y_2), (0.5, slow_down_y_3), (0.6, max_y))
            self.fall_on = False
            self.rect.texture = self.jump_texture

    def on_fall(self):
        self.dt = 0
        self.jump_anim = None
        self.fall_on = True
        self.rect.texture = self.fall_texture

    def toggle_blue_glow(self, glow):
        if glow != self.blue_glow:
            self.blue_glow = glow
            if not self.blue_glow:
                self.glow_color.r, self.glow_color.g, self.glow_color.b = (1,1,1) if not self.glow else (1,1,0)
            else:
                self.glow_color.r, self.glow_color.g, self.glow_color.b = 0,0.6,1
            

    def toggle_glow(self, glow, glow_colors=(1,1,0)):
        self.glow = glow
        if not self.glow and not self.blue_glow:
            self.glow_color.r, self.glow_color.g, self.glow_color.b = 1,1,1
        elif not self.blue_glow:
            self.glow_color.r, self.glow_color.g, self.glow_color.b = glow_colors

    def on_update(self, dt):
        if self.glow or self.blue_glow:
            b_value = self.glow_anim.eval(self.glow_dt % 0.6)
            if self.blue_glow:
                self.glow_color.g = b_value
            else:
                self.glow_color.b = b_value
            self.glow_dt += dt

        if self.jump_anim:
            self.rect.pos = self.rect.pos[0], self.jump_anim.eval(self.dt)
            self.dt += dt
        elif self.fall_on:
            self.fall_vel += gravity * dt
            self.rect.pos += self.fall_vel * dt
            self.jump_anim = None
            self.dt = 0

        if self.jump_anim and self.dt > self.airtime:
            self.on_fall()

        # collision handlers
        if self.listen_collision_below_blocks and self.listen_collision_ground:  # blocks and ground
            collision = self.listen_collision_below_blocks(self) or self.listen_collision_ground(self)
            if collision:
                self.fall_on = False
                self.fall_vel = np.array((0, 0), dtype=np.float)
                if not self.jump_anim: self.rect.texture = self.texture
            elif self.get_pos()[1] > GROUND_Y and not self.jump_anim:
                self.on_fall()

        if self.listen_collision_above_blocks:  # blocks
            collision = self.listen_collision_above_blocks(self) and not self.fall_on
            if collision:
                self.on_fall()

        powerup = self.listen_collision_powerup(self)  # powerups
        return True        

    def set_textures(self, new_textures):
        self.texture, self.jump_texture, self.fall_texture = [Image(new_texture).texture for new_texture in new_textures]
        self.rect.texture = self.texture


##
# BLOCK CLASS -
# contains blocks for game
#   args: position pos (x,y) for each block object
#   args: color to make the block
#   units: number of square blocks in a row to create the whole block.
#   speed: how fast the block should be travelling
#   texture: texture of the block image
##
class Block(InstructionGroup):
    def __init__(self, pos, color, units, speed, texture):
        super(Block, self).__init__()
        self.pos = pos
        self.color = color
        self.add(self.color)
        self.blocks = []
        for i in range(units):
            block = Rectangle(pos=self.pos + np.array([BLOCK_UNIT_LENGTH * i, 0]),
                                         size=[BLOCK_UNIT_LENGTH, BLOCK_HEIGHT],
                                         texture=Image(texture).texture)
            self.blocks.append(block)
            self.add(block)
        self.size = [BLOCK_UNIT_LENGTH * units, BLOCK_HEIGHT]
        self.speed = speed

    def on_update(self, dt):
        for block in self.blocks:
            block.pos -= np.array([dt* self.speed, 0])
        return not self.fell_offscreen()

    def fell_offscreen(self):
        return self.blocks[-1].pos[0] + self.blocks[-1].size[0] < 0

    def get_pos(self):
        return self.blocks[0].pos

    def get_size(self):
        return self.size

    def change_speed(self, new_speed):
        self.speed = new_speed

    def set_texture(self, new_texture):
        for b in self.blocks:
            b.texture = Image(new_texture).image


##
# GROUND CLASS
#   DOES NOT MOVE, CONSTANT RECTANGLE
##
class Ground(InstructionGroup):
    def __init__(self):
        super(Ground, self).__init__()
        self.add(WHITE)
        self.rect = Rectangle(pos=(0, 0), size=[SCREEN_WIDTH, GROUND_Y], texture=Image("img/sand.png").texture)
        self.add(self.rect)

    def on_update(self, dt):
        return True

    def get_pos(self):
        return self.rect.pos

    def set_texture(self, new_texture):
        self.rect.texture = Image(new_texture).texture


class Background(InstructionGroup):
    def __init__(self):
        super(Background, self).__init__()
        self.add(WHITE)
        self.bg = Rectangle(pos=(0, 0), size=[SCREEN_WIDTH, SCREEN_HEIGHT], texture=Image("img/ocean.jpg").texture)
        self.add(self.bg)

    def on_update(self, dt):
        return True

    def get_pos(self):
        return self.bg.pos

    def set_texture(self, new_texture):
        self.bg.texture = Image(new_texture).texture

    def show_death(self):
        self.bg.texture = Image("img/youdied.jpg").texture


##
# POWERUP CLASS
# object containing each powerup in the game
# args: position (x,y) for initial position for powerup
# args: powerup_type (string? integer?) that contributes to determining texture of block
# args: activation_listener - passed in function that is activated when powerup is run into
# waits to see powerup is activated (and whether it should be taken off canvas)
##
class Powerup(InstructionGroup):
    def __init__(self, pos, powerup_type, speed, activation_listeners=None):
        """
        Object handling powerup visuals.
        Arguments:
            pos (tuple): location to render at
            powerup_type (string): type of powerup to instantiate
            speed (float): speed to be traveling at
            activation_listeners (list or None): list of functions to be called upon activation
        """
        super(Powerup, self).__init__()
        self.pos = pos
        self.powerup_type = powerup_type
        self.texture = TEXTURES[powerup_type]
        self.powerup = Rectangle(pos=self.pos, size=[POWERUP_LENGTH, POWERUP_LENGTH],texture=self.texture)
        self.bg_color = Color(1,1,1)
        self.add(self.bg_color)
        self.add(self.powerup)
        self.triggered = False
        self.activation_listeners = activation_listeners
        self.speed = speed
        

    def set_transition_or_reset(self, flag, set_listeners):
        if self.powerup_type in ("reset","transition"):
            self.powerup_type = "transition" if flag else "reset"
            self.powerup.texture = TEXTURES[self.powerup_type]
            set_listeners(self, self.powerup_type)

    def set_glow_background(self, flag):
        self.bg_color.b = 0 if flag else 1

    def on_update(self, dt):
        self.powerup.pos -= np.array([dt * self.speed, 0])
        return not self.fell_offscreen()

    def fell_offscreen(self):
        """
        Returns True if block is no longer visible.
        """
        return self.powerup.pos[0] + self.powerup.size[0] < 0 or self.triggered

    def get_pos(self):
        """
        Returns powerup position.
        """
        return self.powerup.pos

    def get_size(self):
        """
        Returns powerup size.
        """
        return self.powerup.size

    def activate(self, args=None):
        """
        Activates powerup. For use upon contact with the Player.
        """
        for i,listener in enumerate(self.activation_listeners):
            if args is None:
                listener()
            else:
                listener(*args[i])
        self.triggered = True

    def change_speed(self, new_speed):
        """
        Updates speed to new_speed.
        """
        self.speed = new_speed


##
# PROGRESS BAR CLASS
# object that holds all the progress bars for risers, primary songs, filters
# also manages the label of text for the progress bars
# tracks on update each 0.5 sec
##
class ProgressBars(InstructionGroup):
    """
    Object for all progress bar visuals, such as risers, songs, etc.
    Also manages the text labels. Updates every 0.5 seconds.
    """
    def __init__(self, text_label):
        super(ProgressBars, self).__init__()
        self.progress_bars = {}
        self.bar_positions = {"RISER":(3.9 * SCREEN_WIDTH / 5, SCREEN_HEIGHT * 0.8),
                              "FILTER":(3.9 * SCREEN_WIDTH / 5, SCREEN_HEIGHT * 0.75)}
        self.text_label = text_label

    # add a new bar - pass in a sample length, and the sound name to refer to it
    def add_bar(self, duration, sound_name):
        """
        Add a new bar.
        Arguments:
            wave_src (WaveGenerator): sound source 
            sound_name (string): label text
        """
        if sound_name in self.progress_bars:
            self.remove_bar(sound_name)
        new_bar = SoundProgressBar(duration, sound_name, self.bar_positions[sound_name])
        self.progress_bars[sound_name] = new_bar
        self.add(new_bar)

    def remove_bar(self, sound_name):
        """
        Removes the progress bar for the specified song.
        Arguments:
            sound_name (string): name of the bar to be removed
        Returns:
            nothing
        """
        if sound_name in self.progress_bars:
            self.remove(self.progress_bars[sound_name])
            self.progress_bars.pop(sound_name)

    def can_transition(self):
        return len(self.progress_bars) > 0

    def on_update(self, dt):
        removed = []
        self.text_label.text = ""
        for p_type in self.bar_positions:
            self.text_label.text += p_type if p_type in self.progress_bars else ""
            self.text_label.text += "\n"
            if p_type in self.progress_bars:
                kept = self.progress_bars[p_type].on_update(dt)
                if not kept:
                    removed.append(p_type)
        for r in removed:
            self.remove(self.progress_bars[r])
            self.progress_bars.pop(r)


##
# SOUND PROGRESS BAR OBJECT
# This object is an individual bar, and contains the graphics for animating the bar
# on progress through the audio sample.
# args: wave_src - the generator to extract length of sample from
# args: sound_name - the sound name to refer to the object
# pos: the position to draw the progress bar
##
class SoundProgressBar(InstructionGroup):
    def __init__(self, duration, sound_name, pos):
        """
        Object for a single sound progress bar.
        Arguments:
            duration (int): audio sample duration
            sound_name (String): label for progress bar
            pos (tuple): position of bar 
        """
        super(SoundProgressBar, self).__init__()
        self.sound_name = sound_name
        self.dt = 0  # the total time we've spent playing the audio sample
        self.end_frame = duration  # the total length of the sample.
        self.outside_color = Color(rgba=(0.5, 0.5, 0.5, 0.75))
        self.outside_rect = Rectangle(pos=pos, size=[SCREEN_WIDTH / 6, SCREEN_HEIGHT / 20 - 5])
        self.inside_color = LBLUE
        self.inside_rect = Rectangle(pos=pos+np.array([2, 2]), size=[0, SCREEN_HEIGHT / 20 - 9])
        self.max_length = SCREEN_WIDTH / 6 - 4

        self.add(self.outside_color)
        self.add(self.outside_rect)
        self.add(self.inside_color)
        self.add(self.inside_rect)

    def on_update(self, dt):
        self.dt += dt
        self.remove(self.inside_rect)
        if self.dt * Audio.sample_rate / self.end_frame > 0.9:  # red
            self.inside_color.r, self.inside_color.g, self.inside_color.b = 1,0,0
        elif self.dt * Audio.sample_rate / self.end_frame > 0.67:  # yellow
            self.inside_color.r, self.inside_color.g, self.inside_color.b = 1,1,0  # double refrence to yellow at certain places leads to color changing problems
        self.inside_rect.size = [int((self.dt * Audio.sample_rate / self.end_frame) * self.max_length), SCREEN_HEIGHT / 20 - 9]
        self.add(self.inside_rect)
        return not self.dt * Audio.sample_rate > self.end_frame


##
# MAIN PROGRESS BAR OBJECT
# This object is an individual bar that reflects the road map of the game and the collection
# of transition tokens. 5 tokens to allow player to transition, and three levels
class MainProgressBar(InstructionGroup):
    def __init__(self, song_length, trigger_glow_listener=None):
        super(MainProgressBar, self).__init__()
        self.pos = np.array([int(SCREEN_WIDTH/3), int(0.9*SCREEN_HEIGHT)])
        self.outside_color = Color(1,1,1,1)
        self.outside_rect = Rectangle(pos=self.pos, size=[SCREEN_WIDTH / 3, SCREEN_HEIGHT / 15 - 5])
        self.inside_color = Color(1,1,0)  # will changing inside_color in glow_anim change global YELLOW?
        self.inside_rect = Rectangle(pos=self.pos + np.array([2, 2]), size=[0, SCREEN_HEIGHT / 15 - 9])
        self.max_length = SCREEN_WIDTH / 3 - 4

        self.add(self.outside_color)
        self.add(self.outside_rect)
        self.add(self.inside_color)
        self.add(self.inside_rect)
        self.add(BLACK)
        self.add(Line(points=[int(self.max_length/3)+int(SCREEN_WIDTH/3), int(0.9*SCREEN_HEIGHT),
                              int(self.max_length/3)+int(SCREEN_WIDTH/3), int(0.9*SCREEN_HEIGHT)+SCREEN_HEIGHT / 15 - 5]))
        self.add(Line(points=[int(2*self.max_length/3)+int(SCREEN_WIDTH/3), int(0.9*SCREEN_HEIGHT),
                              int(2*self.max_length/3)+int(SCREEN_WIDTH/3), int(0.9*SCREEN_HEIGHT)+SCREEN_HEIGHT / 15 - 5]))

        self.current_song_progress_line = Line(points=[int(SCREEN_WIDTH/3)+2, int(0.9*SCREEN_HEIGHT)-3,int(SCREEN_WIDTH/3)+5, int(0.9*SCREEN_HEIGHT)-3], width=3)
        self.progress_color = Color(0,1,0)
        self.add(self.progress_color)
        self.add(self.current_song_progress_line)

        # progress bar state - info on level, transition powerups collected, current song info
        self.powerups_collected = 0
        self.level = 0  # level is 0 indexed
        self.song_length = song_length
        self.song_frame = 0

        # glow anim stuff
        self.glow = False
        self.glow_anim = KFAnim((0,0),(0.3, 0.8),(0.6,0))
        self.glow_dt = 0
        self.trigger_glow_listener=trigger_glow_listener
        self.a_anim = KFAnim((0,1),(0.3,0.5),(0.6,1))
        self.a_anim_dt = 0

    def on_glow_update(self, dt):
        if self.can_transition():
            self.outside_color.a = self.a_anim.eval(self.a_anim_dt % 0.6) if self.can_transition() else 1
            self.a_anim_dt += dt
        if self.glow:
            b_value = self.glow_anim.eval(self.glow_dt % 0.6)
            self.inside_color.b = b_value
            self.glow_dt += dt
        return True

    def on_progress_bar_update(self, dt):
        self.song_frame += int(dt * Audio.sample_rate)
        new_line_length = int((self.song_frame / self.song_length) * self.max_length)
        self.current_song_progress_line.points = self.current_song_progress_line.points[:2]+[int(SCREEN_WIDTH/3) + new_line_length, self.current_song_progress_line.points[3]]
    
    def add_powerup(self, can_add=True):
        if not self.can_transition():
            if can_add: self.powerups_collected += 1
            self.inside_rect.size = [int(self.max_length * (self.level * 2 + self.powerups_collected)/6),SCREEN_HEIGHT / 15 - 9]
            self.glow = self.can_transition()
            if self.trigger_glow_listener: self.trigger_glow_listener(self.glow)

    def add_level(self):
        self.level += 1
        self.glow_dt = 0
        self.glow = False
        self.inside_color.b = 0
        self.powerups_collected = 0
        self.trigger_glow_listener(self.glow)

    def reset_song_frame(self, next_song_frame, next_song_length):
        self.song_frame = next_song_frame
        self.song_length = next_song_length

    def can_transition(self):
        return self.powerups_collected >= 2



class BeatMatcher(InstructionGroup):
    def __init__(self, audio_manager, primary_speed, secondary_speed):
        super(BeatMatcher, self).__init__()
        self.primary_speed = primary_speed
        self.secondary_speed = secondary_speed
        self.audio_manager = audio_manager
        self.base = 70
        self.width = SCREEN_WIDTH / 6
        self.x_pos = 3.9 * SCREEN_WIDTH / 5
        self.y_pos = SCREEN_HEIGHT * 0.9
        self.color = Color(rgba=(0.5, 0.5, 0.5, 0.75))
        self.add(self.color)
        # size=[SCREEN_WIDTH / 6, SCREEN_HEIGHT / 20 - 5]
        # how to keep everything lined up between 70 and 140?
        # 90. double = 180. 90%70=20. 180%70=40 270%70 = 60. 
        # so (current_speed % base) / int(current_speed / base_speed)
        self.bg = Rectangle(pos=(self.x_pos, self.y_pos), size=(self.width, SCREEN_HEIGHT / 20))
        self.add(self.bg)
        self.target = CEllipse(cpos=(self.x_pos + (self.width / self.base) * self.calculate_pos(self.audio_manager.get_secondary_bpm(), self.audio_manager.get_secondary_speed()), self.y_pos + 15), csize=(25, 25))
        self.add(RED)
        self.add(self.target)
        self.aimer = CEllipse(cpos=(self.x_pos + (self.width / self.base) * self.calculate_pos(self.audio_manager.get_primary_bpm(), self.audio_manager.get_primary_speed()), self.y_pos + 15), csize=(20, 20))
        self.add(YELLOW)
        self.add(self.aimer)

        self.transition_possible = False
        self.a_anim = KFAnim((0,0.75),(0.3, 0.3),(0.6,0.75))
        self.a_anim_dt = 0

    def calculate_pos(self, bpm, base_speed):
        if base_speed > 2: 
            print(base_speed)
        return (bpm % self.base) / int(bpm / self.base)

    def transition(self):
        self.remove(RED)
        self.remove(GREEN)
        self.remove(self.target)
        self.remove(self.aimer)
        self.target = CEllipse(cpos=(self.x_pos + 2 * self.calculate_pos(self.audio_manager.get_secondary_bpm(), self.audio_manager.get_secondary_speed()), self.y_pos + 15), csize=(25, 25))
        self.add(RED)
        self.add(self.target)
        self.aimer = CEllipse(cpos=(self.x_pos + 2 * self.calculate_pos(self.audio_manager.get_primary_bpm(), self.audio_manager.get_primary_speed()), self.y_pos + 15), csize=(20, 20))
        self.add(GREEN)
        self.add(self.aimer)

    def on_update(self, dt):
        self.color.a = self.a_anim.eval(self.a_anim_dt % 0.6) if self.transition_possible else 0.75
        self.a_anim_dt += dt
        diff = abs(2 * self.calculate_pos(self.audio_manager.get_secondary_bpm(), self.audio_manager.get_secondary_speed()) - 2 * self.calculate_pos(self.audio_manager.get_primary_bpm(), self.audio_manager.get_primary_speed()))
        self.remove(self.aimer)
        self.aimer = CEllipse(cpos=(self.x_pos + 2 * self.calculate_pos(self.audio_manager.get_primary_bpm(), self.audio_manager.get_primary_speed()), self.y_pos + 15), csize=(20, 20))
        self.transition_possible = diff <= 15
        self.add(GREEN if self.transition_possible else YELLOW)
        self.add(self.aimer)
        return True

    def can_transition(self):
        return self.transition_possible


class MenuDisplay(InstructionGroup):
    def __init__(self):
        super(MenuDisplay, self).__init__()
        self.color = Color(rgba=(0.5, 0, 1, 0.5))
        self.add(self.color)
        self.bg = Rectangle(pos=(0, 0), size=[SCREEN_WIDTH, SCREEN_HEIGHT])
        self.add(self.bg)
        self.buttons = list()
        self.lvl1_button = MenuButton("Level 1", 0, True)
        self.tut_button = MenuButton("Walkthrough", 1, False)
        self.buttons.append(self.tut_button)
        self.buttons.append(self.lvl1_button)
        self.add(self.lvl1_button)
        self.add(self.tut_button)
        self.title = CoreLabel(text="Beat Runner", font_size=56, halign="center")
        self.title.refresh()
        self.title_rec = Rectangle(pos=(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT - 150), size=(200, 50), font_name="RobotoMono", texture=self.title.texture)
        self.add(WHITE)
        self.add(self.title_rec)
        self.highlit_button = 1

    def highlight_button(self, delta):
        for button in self.buttons:
            button.unhighlight()
        self.highlit_button += delta
        if self.highlit_button >= len(self.buttons):
            self.highlit_button = 0
        if self.highlit_button < 0:
            self.highlit_button = len(self.buttons) - 1
        self.buttons[self.highlit_button].highlight()

    def on_update(self, dt):
        for button in self.buttons:
            button.on_update(dt)
        return True


class MenuButton(InstructionGroup):
    def __init__(self, labeltext, offset, selected=False):
        super(MenuButton, self).__init__()
        # setup ree
        self.width = 200
        self.text_color = WHITE
        self.button_color = Color(0.5, 0.5, 0.5)
        self.highlight_color = Color(1, 1, 0)
        self.label = CoreLabel(text=labeltext, font_size=48, halign="center")
        self.label.refresh()
        self.outer_rec = Rectangle(pos=(SCREEN_WIDTH / 2 - self.width / 2, SCREEN_HEIGHT / 2 - 60 * offset), size=(self.width, 50))
        self.inner_rec = Rectangle(pos=(SCREEN_WIDTH / 2 - self.width / 2 + 2, SCREEN_HEIGHT / 2 - 60 * offset + 2), size=(self.width - 5, 45))
        self.text_rec  = Rectangle(pos=(SCREEN_WIDTH / 2 - self.width / 2 + 20, SCREEN_HEIGHT / 2 - 60 * offset + 10), size=(self.width - 40, 30), texture=self.label.texture)
        
        self.selected = selected
        self.alpha = 0
        self.direction = 0.5

        # draw the buttons
        if self.selected:
            self.add(self.highlight_color)
        else:
            self.add(Color(0.5, 0.5, 0.5))
        self.add(self.outer_rec)
        self.add(self.button_color)
        self.add(self.inner_rec)
        self.add(self.text_color)
        self.add(self.text_rec)

    def highlight(self):
        self.remove(self.outer_rec)
        self.add(self.highlight_color)
        self.add(self.outer_rec)
        self.selected = True

    def unhighlight(self):
        self.remove(self.outer_rec)
        self.remove(self.inner_rec)
        self.remove(self.text_rec)
        self.add(self.button_color)
        self.add(self.outer_rec)
        self.add(self.inner_rec)
        self.add(self.text_color)
        self.add(self.text_rec)
        self.selected = False

    def on_update(self, dt):
        if self.selected:
            self.alpha += dt * self.direction
            if self.alpha > 0.5:
                self.alpha = 0.5
                self.direction = -0.5
            if self.alpha < 0:
                self.alpha = 0
                self.direction = 0.5
            self.remove(self.outer_rec)
            self.add(Color(rgba=(1, 1, 0, self.alpha)))
            self.add(self.outer_rec)

        return True


class TutorialDisplay(InstructionGroup):
    def __init__(self, block_data, powerup_data, audio_manager, label, game_engine):
        super(TutorialDisplay, self).__init__()
        self.color = GREEN
        self.game_engine = game_engine
        self.audio_manager = audio_manager
        self.bg = Rectangle(pos=(0, 0), size=[SCREEN_WIDTH, SCREEN_HEIGHT], texture=Image("img/cl.jpg").texture)
        self.add(self.bg)
        self.message = 0
        self.description = 0  
        self.current_frame = 0
        self.game_speed = INIT_RIGHT_SPEED
        self.last_powerup_bars_update = 0
        self.current_powerup = 0
        self.current_block = 0
        self.playing = True  
        self.block_data = []
        self.powerup_data = [
            (3.0, 1, "speedup"),
            (3.7, 1, "speedup"),
            (4.5, 1, "speedup"),
            (5.0, 2, "speedup"),
            (5.4, 1, "speedup"),
            (5.9, 1, "transition_token"),
            (6.4, 1, "lower_volume"),
            (6.999, 1, "raise_volume"),
            (7.7, 2, "slowdown"),
            (8.4, 1, "slowdown"),
            (8.8, 1, "slowdown"),
            (9.7, 2, "slowdown"),
            (9.9, 1, "speedup"),
            (10.5, 1, "transition_token"),
            (11.5, 1, "speedup"),
            (11.5, 2, "speedup"),
            (13.0, 1, "transition_token"),
            (13.5, 2, "slowdown"),
            (14.5, 1, "reset"),
            (15.0, 1, "transition_token"),
            (15.5, 2, "danger"),
            (17.0, 1, "trophy")
        ]
        self.blocks = []
        self.powerups = []
        self.player = Player(listen_collision_above_blocks=self.listen_collision_above_block,
                        listen_collision_ground=self.listen_collision_ground,
                             listen_collision_powerup=self.listen_collision_powerup,
                             listen_collision_below_blocks=self.listen_collision_below_block)
        self.add(self.player)
        self.main_bar = MainProgressBar(self.audio_manager.get_current_length(), self.player.toggle_glow)
        self.add(self.main_bar)
        self.ground = Ground()
        self.add(self.ground)
        
        self.powerup_bars = ProgressBars(label)
        self.add(self.powerup_bars)
        self.last_powerup_bars_update = 0

        self.beatmatcher = BeatMatcher(self.audio_manager, 120, 90)
        self.add(self.beatmatcher)
        self.index_to_y = [0, int(SCREEN_HEIGHT/5), int(SCREEN_HEIGHT * 2/5), int(SCREEN_HEIGHT*3/5)]  # maps block/powerup indices to y coords

        self.messages = [
            "Press W to jump",
            "Hit powerups to change the sound",
            "Adjust the speed (yellow) to match the next song (red)",
            "Fill the top bar to change songs",
            "Avoid dangers"
        ]
        self.descriptions = [
            "Tempo matcher",
            "Song duration",
            "Powerup meter"
        ]

        self.powerup_listeners = {'powerup_note': [self.audio_manager.play_powerup_effect],
                                  'lower_volume': [self.audio_manager.lower_volume],
                                  'raise_volume': [self.audio_manager.raise_volume],
                                  'error': [self.audio_manager.play_error_effect],
                                  'bass_boost': [self.audio_manager.bass_boost],
                                  'vocals_boost': [self.audio_manager.vocals_boost],
                                  'reset_filter': [self.audio_manager.reset_filter],
                                  'speedup': [self.audio_manager.speedup, self.increase_game_speed],
                                  'slowdown': [self.audio_manager.slowdown, self.decrease_game_speed],
                                  'reset_speed': [self.audio_manager.reset_speed, self.reset_game_speed],
                                  'sample_on':[self.audio_manager.sample_on],
                                  'sample_off':[self.audio_manager.sample_off],
                                  'reset_sample':[self.audio_manager.reset_sample],
                                  'riser':[self.audio_manager.riser],
                                  "trophy": [self.audio_manager.toggle, self.toggle, self.win_game],
                                  'danger': [self.audio_manager.toggle, self.toggle, self.lose_game],
                                  'transition_token': [self.audio_manager.add_transition_token, self.main_bar.add_powerup, self.change_text],
                                  "transition": [self.win_game, self.change_text],
                                  "reset":[self.audio_manager.reset, self.main_bar.add_powerup]}
        message_label = CoreLabel(text=self.messages[self.message], font_size=56)
        description_label = CoreLabel(text=self.descriptions[self.description])
        message_label.refresh()
        self.message_rec = Rectangle(pos=(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 3.5), size=(300,50), texture=message_label.texture)
        self.add(WHITE)
        self.add(self.message_rec)

    def change_text(self):
        self.remove(self.message_rec)
        self.message += 1
        message_label = CoreLabel(text=self.messages[self.message] if self.message < len(self.messages) else "", font_size=56)
        message_label.refresh()
        self.message_rec = Rectangle(pos=(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 3.5), size=(300,50), texture=message_label.texture)
        self.add(self.message_rec)

    def on_update(self, dt):
        if self.playing:
            self.player.on_update(dt)
            self.main_bar.on_glow_update(dt)
            self.beatmatcher.on_update(dt)
            if abs(self.current_frame - self.last_powerup_bars_update) > Audio.sample_rate / 2:
                self.powerup_bars.on_update(dt + 0.5)
                self.last_powerup_bars_update = self.current_frame
                self.main_bar.on_progress_bar_update(dt + 0.5)

            removed_items = set()

            # UPDATE EACH POWERUP AND BLOCK, AND TRACK IF THEY ARE REMOVED OR NOT FROM THE GAME FRAME
            # For blocks, track if a block goes off screen
            # for powerups, track if a powerup is activated or go off screen
            # remove removed items from the animation.
            for block in self.blocks:
                if not block.on_update(dt):
                    removed_items.add(block)

            for powerup in self.powerups:
                if not powerup.on_update(dt):
                    if powerup.powerup_type == "danger":
                        self.win_game()
                    removed_items.add(powerup)
            for item in removed_items:
                self.remove(item)

            self.powerups = set([p for p in self.powerups if p not in removed_items])
            self.blocks = set([b for b in self.blocks if b not in removed_items])

            # add new blocks and powerups
            # COMPARE ANNOTATION NOTES TO CURRENT FRAME AND ADD NEW OBJECTS ACCORDINGLY
            block_valid = self.current_block < len(self.block_data)
            block_onscreen = block_valid and self.current_frame / Audio.sample_rate > self.block_data[self.current_block][0] - SECONDS_FROM_RIGHT_TO_PLAYER
            
            if block_onscreen:
                self.add_block(self.current_block)
                self.current_block += 1

            powerup_valid = self.current_powerup < len(self.powerup_data)
            powerup_onscreen = powerup_valid and self.current_frame / Audio.sample_rate > self.powerup_data[self.current_powerup][0] - SECONDS_FROM_RIGHT_TO_PLAYER
            
            if powerup_onscreen:
                self.add_powerup(self.current_powerup)
                self.current_powerup += 1
        return True

    def reset(self):
        self.playing = False
        self.message = 0
        self.current_block = 0
        self.current_frame = 0
        self.current_powerup = 0
        self.last_powerup_bars_update = 0

    def on_jump(self):
        self.player.on_jump()

    def on_fall(self):
        self.player.on_fall()

    def toggle(self):
        print(self.blocks[self.current_block])
        self.playing = not self.playing

    def win_game(self):
        self.game_engine.anim_group.remove(self)
        self.game_engine.anim_group.add(self.game_engine.menu_display)
        self.game_engine.screen = "menu"
        self.toggle()
        self.game_engine.tutorial_audio_manager.toggle()

    def lose_game(self):
        pass

    def update_frame(self, frame):
        """
        Updates the current frame.
        Arguments:
            frame (int): frame to set game frame to
        """
        self.current_frame = frame

    def add_powerup(self, powerup):
        """
        Creates a new Powerup object from an index into the list of powerup tuple data and adds it to the game.
        Arguments:
            powerup (int): index of powerup tuple to be instantiated
        """
        y_pos = self.powerup_data[powerup][1]
        p_type = self.powerup_data[powerup][2]
        if p_type == "transition" and self.main_bar.powerups_collected != 5:
            return
        new_powerup = Powerup((SCREEN_WIDTH, self.index_to_y[y_pos-1] + GROUND_Y + BLOCK_HEIGHT), p_type, self.game_speed, self.powerup_listeners[p_type])
        self.powerups.add(new_powerup)
        self.add(new_powerup)

    def listen_collision_below_block(self, player):
        """
        Listener for collision between rising player and blocks.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        for block in self.blocks:
            block_x = block.get_pos()[0]
            block_y = block.get_pos()[1]
            player_x = player.get_pos()[0]
            player_y = player.get_pos()[1]

            if block_x < player_x < block_x + block.get_size()[0] or \
                    block_x < player_x + PLAYER_WIDTH < block_x + block.get_size()[0]:
                if block_y < player_y <= block_y + BLOCK_HEIGHT:
                    # case 1: fall onto a new block
                    player.set_y(block_y + BLOCK_HEIGHT)
                    return True
        return False

    def listen_collision_above_block(self, player):
        """
        Listener for collision between falling player and blocks.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        for block in self.blocks:
            block_x = block.get_pos()[0]
            block_y = block.get_pos()[1]
            player_x = player.get_pos()[0]
            player_y = player.get_pos()[1]

            if block_x < player_x < block_x + block.get_size()[0] or \
                    block_x < player_x + PLAYER_WIDTH < block_x + block.get_size()[0]:
                if block_y < player_y + PLAYER_HEIGHT < block_y + BLOCK_HEIGHT:
                # case 2: top of player collides with bottom of a block
                    return True
        return False

    def listen_collision_ground(self, player):
        """
        Listener for collision between player and ground.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        if player.get_pos()[1] < GROUND_Y:
            player.set_y(GROUND_Y)
            return True
        return False

    # listener for player with powerups objects
    def listen_collision_powerup(self, player):
        """
        Listener for collision between player and powerups.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        for powerup in self.powerups:
            powerup_x = powerup.get_pos()[0]
            powerup_y = powerup.get_pos()[1]
            player_x = player.get_pos()[0]
            player_y = player.get_pos()[1]

            if powerup_x < player_x < powerup_x + POWERUP_LENGTH or \
                    powerup_x < player_x + PLAYER_WIDTH < powerup_x + POWERUP_LENGTH:
                if player_y < powerup_y < player_y + PLAYER_HEIGHT or \
                        player_y < powerup_y + POWERUP_LENGTH < player_y + PLAYER_HEIGHT:
                    if powerup.powerup_type == "sample_on" or powerup.powerup_type == "sample_off":
                        powerup.activate([[self.current_frame]])
                    elif powerup.powerup_type == "riser":
                        powerup.activate([[self.powerup_bars.add_bar]])
                    else:
                        powerup.activate()
                    return powerup
        return None

    def increase_game_speed(self):
        """
        Increases game speed.
        For use with audio pitch/speed increases.
        """
        self.game_speed = self.game_speed * 2**(1/12)
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def decrease_game_speed(self):
        """
        Decreases game speed.
        For use with audio pitch/speed decreases.
        """
        self.game_speed = self.game_speed / 2**(1/12)
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def reset_game_speed(self):
        """
        Resets game to normal speed.
        For use with audio pitch/speed resets.
        """
        self.game_speed = INIT_RIGHT_SPEED
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

        
##
# WRAPPER CLASS FOR THE GAME DISPLAY
# args: song_data, powerup_data: annotations indicating where blocks and powerups should be, respectively.
# song_data: [sec, measure, y_index, # units]
# powerup_data: [sec, measure, powerup_str]
# data_audio_transition_listener - activates a listener function in beatrunner_main, which activates transition in other classes
# this class contains the PLAYER object, GROUND object, and all POWERUPS AND BLOCKS on screen
class GameDisplay(InstructionGroup):
    def __init__(self, block_data, powerup_data, audio_manager, label, data_audio_transition_listener):
        """
        Object handling all of the visual elements of a game instance.
        Arguments:
            block_data (list): specifies time and location of blocks
            powerup_data (list): specifies time and location of powerups
            audio_manager (AudioManager): Object handling all audio aspects
            label (string): label to display on first progress bar
        """
        super(GameDisplay, self).__init__()
        self.block_data = block_data
        self.powerup_data = powerup_data
        self.audio_manager = audio_manager
        self.data_audio_transition_listener = data_audio_transition_listener

        self.bg_color = Color(1,1,1)
        self.add(self.bg_color)
        self.label = label

        self.background = Background()
        self.player = Player(listen_collision_above_blocks=self.listen_collision_above_block,
                        listen_collision_ground=self.listen_collision_ground,
                             listen_collision_powerup=self.listen_collision_powerup,
                             listen_collision_below_blocks=self.listen_collision_below_block)
        self.main_bar = MainProgressBar(self.audio_manager.get_current_length(), self.player.toggle_glow)
        self.ground = Ground()
   
        self.add(self.background)
        self.add(self.main_bar)
        self.add(self.player)
        self.add(self.ground)        

        self.current_frame = 0  # current frame in song
        self.current_block = 0  # current block ind to add from song_data
        self.current_powerup = 0  # current powerup ind to add from powerup_data

        self.blocks = set()  # on-screen blocks
        self.powerups = set()  # on-screen powerups
        self.index_to_y = [0, int(SCREEN_HEIGHT/5), int(SCREEN_HEIGHT * 2/5), int(SCREEN_HEIGHT*3/5)]  # maps block/powerup indices to y coords
        self.powerup_listeners = {'powerup_note': [self.audio_manager.play_powerup_effect],
                                  'lower_volume': [self.audio_manager.lower_volume],
                                  'raise_volume': [self.audio_manager.raise_volume],
                                  'error': [self.audio_manager.play_error_effect],
                                  'bass_boost': [self.audio_manager.bass_boost],
                                  'vocals_boost': [self.audio_manager.vocals_boost],
                                  'reset_filter': [self.audio_manager.reset_filter],
                                  'reg_to_high': [self.audio_manager.reg_to_high_boost],
                                  'speedup': [self.audio_manager.speedup, self.increase_game_speed],
                                  'slowdown': [self.audio_manager.slowdown, self.decrease_game_speed],
                                  'reset_speed': [self.audio_manager.reset_speed, self.reset_game_speed],
                                  'sample_on':[self.audio_manager.sample_on],
                                  'sample_off':[self.audio_manager.sample_off],
                                  'reset_sample':[self.audio_manager.reset_sample],
                                  'riser':[self.audio_manager.riser],
                                  "trophy": [self.audio_manager.toggle, self.toggle, self.win_game],
                                  'danger': [self.audio_manager.toggle, self.toggle, self.lose_game],
                                  'transition_token': [self.audio_manager.add_transition_token, self.main_bar.add_powerup],
                                  "transition": [self.data_audio_transition_listener],
                                  "reset":[self.audio_manager.reset, self.main_bar.add_powerup, self.player.toggle_blue_glow, self.reset_game_speed]}

        # game states
        self.paused = True
        self.over = False
        self.game_speed = INIT_RIGHT_SPEED
        self.block_texture = "img/wave.png"

        # powerup progress bars (righthand side)
        self.powerup_bars = ProgressBars(label)
        self.add(self.powerup_bars)
        self.last_powerup_bars_update = 0

        # transition tempo meter
        self.beatmatcher = BeatMatcher(self.audio_manager, 120, 90)
        self.add(self.beatmatcher)

    def reset(self):
        self.__init__(self.block_data, self.powerup_data, self.audio_manager, self.label, self.data_audio_transition_listener)

    # toggle paused of game or not
    def toggle(self):
        """
        Play or pause the game.
        """
        print(self.current_block)
        self.paused = not self.paused

    def on_jump(self):
        """
        Calls player jump function.
        """
        self.player.on_jump()

    def on_fall(self):
        """
        Calls player fall function.
        """
        self.player.on_fall()

    def is_over(self):
        return self.over

    def lose_game(self):
        """
        Show game-losing screen.
        """
        self.over = True
        self.playing = False
        self.remove(self.background)
        self.background.show_death()
        self.add(self.background)
        self.add(WHITE)
        text = CoreLabel(text="press any key to exit", font_size=56)
        text.refresh()
        self.add(Rectangle(pos=(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 4), size=(300, 50), texture=text.texture))

    def win_game(self):
        """
        Show game-winning screen.
        """
        self.over = True
        self.playing = False
        self.add(Rectangle(pos=(0, 0), size=[SCREEN_WIDTH, SCREEN_HEIGHT], texture=Image("img/darksky.jpg").texture))
        self.add(WHITE)
        message = CoreLabel(text="you win!", font_size=56)
        text = CoreLabel(text="press any key to exit", font_size=56)
        text.refresh()
        message.refresh()
        self.add(Rectangle(pos=(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2), size=(300, 60), texture=message.texture))
        self.add(Rectangle(pos=(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 3), size=(300, 50), texture=text.texture))

    def set_activation_listeners(self, powerup, new_p_type):
        powerup.activation_listeners = self.powerup_listeners[new_p_type]

    # call every frame to make blocks and powerups flow towards player
    def on_update(self, dt):
        if not self.paused:
            self.player.on_update(dt)
            self.player.toggle_blue_glow(self.audio_manager.enough_past_powerups())
            self.main_bar.on_glow_update(dt)
            self.beatmatcher.on_update(dt)
            if abs(self.current_frame - self.last_powerup_bars_update) > Audio.sample_rate / 2:
                self.powerup_bars.on_update(dt + 0.5)
                self.last_powerup_bars_update = self.current_frame
                self.main_bar.on_progress_bar_update(dt + 0.5)

            removed_items = set()

            # UPDATE EACH POWERUP AND BLOCK, AND TRACK IF THEY ARE REMOVED OR NOT FROM THE GAME FRAME
            # For blocks, track if a block goes off screen
            # for powerups, track if a powerup is activated or go off screen
            # remove removed items from the animation.
            for block in self.blocks:
                if not block.on_update(dt):
                    removed_items.add(block)

            for powerup in self.powerups:
                powerup.set_transition_or_reset(self.beatmatcher.can_transition() and self.main_bar.can_transition() and self.powerup_bars.can_transition(), self.set_activation_listeners)
                if powerup.powerup_type == "reset":
                    powerup.set_glow_background(self.audio_manager.enough_past_powerups())
                if not powerup.on_update(dt):
                    removed_items.add(powerup)
            for item in removed_items:
                self.remove(item)

            self.powerups = set([p for p in self.powerups if p not in removed_items])
            self.blocks = set([b for b in self.blocks if b not in removed_items])

            # add new blocks and powerups
            # COMPARE ANNOTATION NOTES TO CURRENT FRAME AND ADD NEW OBJECTS ACCORDINGLY
            block_valid = self.current_block < len(self.block_data)
            block_onscreen = block_valid and self.current_frame / Audio.sample_rate > self.block_data[self.current_block][0] - SECONDS_FROM_RIGHT_TO_PLAYER
            if block_onscreen:
                self.add_block(self.current_block)
                self.current_block += 1

            powerup_valid = self.current_powerup < len(self.powerup_data)
            powerup_onscreen = powerup_valid and self.current_frame / Audio.sample_rate > self.powerup_data[self.current_powerup][0] - SECONDS_FROM_RIGHT_TO_PLAYER
            
            if powerup_onscreen:
                self.add_powerup(self.current_powerup)
                self.current_powerup += 1

        return True

    # block adder function
    def add_block(self, block):
        """ 
        Creates a new Block object from an index into the list of block tuple data and adds it to the game.
        Arguments:
            block (int): index of block tuple to be instantiated
        """
        y_pos = self.block_data[block][1]
        units = self.block_data[block][2]
        new_block = Block((SCREEN_WIDTH, self.index_to_y[y_pos] + GROUND_Y), Color(1,1,1), units, self.game_speed, self.block_texture)
        self.blocks.add(new_block)
        self.add(new_block)

    def add_powerup(self, powerup):
        """
        Creates a new Powerup object from an index into the list of powerup tuple data and adds it to the game.
        Arguments:
            powerup (int): index of powerup tuple to be instantiated
        """
        y_pos = self.powerup_data[powerup][1]
        p_type = self.powerup_data[powerup][2]

        if p_type == "transition" and not self.main_bar.can_transition():
            p_type = "reset"  # if you can't transition yet, just set the powerup to be a reset instead of a transition
        new_powerup = Powerup((SCREEN_WIDTH, self.index_to_y[y_pos-1] + GROUND_Y + BLOCK_HEIGHT), p_type, self.game_speed, self.powerup_listeners[p_type])
        self.powerups.add(new_powerup)
        self.add(new_powerup)

    # add new blocks for new song
    def change_blocks(self, new_blocks, new_powerups):
        """
        Removes blocks for previous song from play and adds blocks for new song.
        """
        for item in self.blocks:
            self.remove(item)
        for item in self.powerups:
            self.remove(item)
        self.blocks, self.powerups = set(), set()
        self.block_data, self.powerup_data = new_blocks, new_powerups

        self.current_block, self.current_powerup = 0, 0

    def update_frame(self, frame):
        """
        Updates the current frame.
        Arguments:
            frame (int): frame to set game frame to
        """
        self.current_frame = frame

    def listen_collision_below_block(self, player):
        """
        Listener for collision between rising player and blocks.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        for block in self.blocks:
            block_x = block.get_pos()[0]
            block_y = block.get_pos()[1]
            player_x = player.get_pos()[0]
            player_y = player.get_pos()[1]

            if block_x < player_x < block_x + block.get_size()[0] or \
                    block_x < player_x + PLAYER_WIDTH < block_x + block.get_size()[0]:
                if block_y < player_y <= block_y + BLOCK_HEIGHT:
                    # case 1: fall onto a new block
                    player.set_y(block_y + BLOCK_HEIGHT)
                    return True
        return False

    def listen_collision_above_block(self, player):
        """
        Listener for collision between falling player and blocks.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        for block in self.blocks:
            block_x = block.get_pos()[0]
            block_y = block.get_pos()[1]
            player_x = player.get_pos()[0]
            player_y = player.get_pos()[1]

            if block_x < player_x < block_x + block.get_size()[0] or \
                    block_x < player_x + PLAYER_WIDTH < block_x + block.get_size()[0]:
                if block_y < player_y + PLAYER_HEIGHT < block_y + BLOCK_HEIGHT:
                # case 2: top of player collides with bottom of a block
                    return True
        return False

    def listen_collision_ground(self, player):
        """
        Listener for collision between player and ground.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        if player.get_pos()[1] < GROUND_Y:
            player.set_y(GROUND_Y)
            return True
        return False

    # listener for player with powerups objects
    def listen_collision_powerup(self, player):
        """
        Listener for collision between player and powerups.
        Arguments:
            player (Player): player instance to handle collisions for
        """
        for powerup in self.powerups:
            powerup_x = powerup.get_pos()[0]
            powerup_y = powerup.get_pos()[1]
            player_x = player.get_pos()[0]
            player_y = player.get_pos()[1]

            if powerup_x < player_x < powerup_x + POWERUP_LENGTH or \
                    powerup_x < player_x + PLAYER_WIDTH < powerup_x + POWERUP_LENGTH:
                if player_y < powerup_y < player_y + PLAYER_HEIGHT or \
                        player_y < powerup_y + POWERUP_LENGTH < player_y + PLAYER_HEIGHT:
                    if powerup.powerup_type == "sample_on" or powerup.powerup_type == "sample_off":
                        powerup.activate([[self.current_frame]])
                    elif powerup.powerup_type == "riser" or "boost" in powerup.powerup_type or powerup.powerup_type=="reg_to_high":
                        powerup.activate([[self.powerup_bars.add_bar]])
                    elif powerup.powerup_type == "reset":
                        powerup.activate([[self.powerup_bars.remove_bar],[self.audio_manager.enough_past_powerups()],[False],[]])
                    else:
                        powerup.activate()
                    return powerup
        return None

    def increase_game_speed(self):
        """
        Increases game speed.
        For use with audio pitch/speed increases.
        """
        self.game_speed = self.game_speed * 2**(1/12)
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def decrease_game_speed(self):
        """
        Decreases game speed.
        For use with audio pitch/speed decreases.
        """
        self.game_speed = self.game_speed / 2**(1/12)
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def reset_game_speed(self):
        """
        Resets game to normal speed.
        For use with audio pitch/speed resets.
        """
        self.game_speed = INIT_RIGHT_SPEED
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def graphics_transition(self, new_blocks, new_powerups, player_textures, ground_texture, background_texture, block_texture):
        """
        Handler for song-to-song transitions.
        Updates player object, resets song progress bar, and resets game speed.
        Arguments:
            player_texture (texture): new texture for the player character
            ground_texture (texture): new texture for the ground
            block_texture  (texture): new texture for the blocks
        """
        self.player.set_textures(player_textures)
        self.ground.set_texture(ground_texture)
        self.background.set_texture(background_texture)
        self.block_texture = block_texture
        self.reset_game_speed()
        self.main_bar.add_level()
        self.main_bar.reset_song_frame(self.audio_manager.get_current_frame(), self.audio_manager.get_current_length())
        self.beatmatcher.transition()
        self.change_blocks(new_blocks, new_powerups)