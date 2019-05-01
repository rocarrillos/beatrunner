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

import random
import numpy as np
import bisect


##
# CONSTANTS
##

SCREEN_WIDTH = Window.size[0]
SCREEN_HEIGHT = Window.size[1]
PLAYER_X = int(SCREEN_WIDTH / 6)
SECONDS_FROM_RIGHT_TO_PLAYER = 4
INIT_RIGHT_SPEED = (SCREEN_WIDTH - PLAYER_X)/SECONDS_FROM_RIGHT_TO_PLAYER  # pixels/second
GROUND_Y = int(SCREEN_HEIGHT / 10)

BLOCK_HEIGHT = int(SCREEN_HEIGHT / 15)
BLOCK_UNIT_LENGTH = int(SCREEN_WIDTH/4)

PLAYER_HEIGHT = int(2 * SCREEN_HEIGHT / 20)
PLAYER_WIDTH = int(SCREEN_HEIGHT / 10)

POWERUP_LENGTH = int(SCREEN_WIDTH/20)

TEXTURES = {'vocals_boost': Image("img/mic.jpg").texture, 'bass_boost': Image("img/bass.jpg").texture,
            'powerup_note':Image("img/riser.png").texture,"lower_volume":Image("img/arrowdownred.png").texture,
            "raise_volume": Image("img/uparrowred.png").texture, "reset_filter":Image("img/reset_filter.png").texture,
            "reset_speed": Image("img/reset_speed.png").texture,"speedup":Image("img/speedup.png").texture,
            "slowdown": Image("img/ice.jpg").texture,"underwater":Image("img/sub.jpg").texture,
            "sample_on": Image("img/sample_on.png").texture, "sample_off": Image("img/sample_off.png").texture,
            "reset_sample":Image("img/sample_off.png").texture, "start_transition": Image("img/green_spiral.png").texture,
            "end_transition": Image("img/red_spiral.png").texture, "riser":Image("img/riser.png").texture,
            "trophy": Image("img/trophy.png").texture, "danger": Image("img/skull.png").texture}

gravity = np.array((0, -1800))


##
# PLAYER CLASS -
#   Object that contains player icon
#   arguments: listener functions
#   graphics regarding falling and jumping.
#   listens for collisions with blocks, powerups and ground.
##
class Player(InstructionGroup):
    def __init__(self, listen_collision_above_blocks=None, listen_collision_ground=None, listen_collision_powerup=None, listen_collision_below_blocks=None):
        super(Player, self).__init__()
        self.pos = (PLAYER_X-PLAYER_WIDTH, GROUND_Y)
        self.texture = Image('img/shark.png').texture
        self.add(Color(1,1,1))
        self.rect = Rectangle(pos=self.pos, size=(PLAYER_WIDTH, PLAYER_HEIGHT), texture=self.texture)
        self.add(self.rect)

        self.jump_anim = None
        self.fall_on = False
        self.fall_vel = np.array((0,0), dtype=np.float)

        self.dt = 0

        self.listen_collision_above_blocks = listen_collision_above_blocks
        self.listen_collision_below_blocks = listen_collision_below_blocks
        self.listen_collision_ground = listen_collision_ground
        self.listen_collision_powerup = listen_collision_powerup

    def get_pos(self):
        return self.rect.pos

    def set_y(self, new_y):
        self.rect.pos = self.rect.pos[0], new_y

    def on_jump(self):
        if not self.jump_anim and not self.fall_on:
            current_y = self.rect.pos[1]
            max_y = self.rect.pos[1] + int(7 * SCREEN_HEIGHT / 20)
            slow_down_y_1 = self.rect.pos[1] + int(SCREEN_HEIGHT / 5)  # some hardcoded anims right here
            slow_down_y_2 = self.rect.pos[1] + int(5 * SCREEN_HEIGHT / 20)
            slow_down_y_3 = self.rect.pos[1] + int(6.5 * SCREEN_HEIGHT/20)
            self.jump_anim = KFAnim((0,current_y), (0.25, slow_down_y_1), (0.35, slow_down_y_2), (0.5, slow_down_y_3), (0.6, max_y))
            self.fall_on = False

    def on_fall(self):
        self.reset_on_fall()

    def on_update(self, dt):
        # print("jump anim: ", self.jump_anim, "fall on: ", self.fall_on, "dt", self.dt, "fall vel", self.fall_vel, "rect pos", self.rect.pos)
        if self.jump_anim:
            self.rect.pos = self.rect.pos[0], self.jump_anim.eval(self.dt)
            self.dt += dt
        elif self.fall_on:
            self.fall_vel += gravity*dt
            self.rect.pos += self.fall_vel * dt
            self.jump_anim = None
            self.dt = 0
        # print("position", self.rect.pos, self.fall_vel * dt)
        if self.jump_anim and self.dt > 0.6:
            self.reset_on_fall()

        # LISTEN FOR COLLISIONS #

        if self.listen_collision_below_blocks and self.listen_collision_ground:
            collision = self.listen_collision_below_blocks(self) or self.listen_collision_ground(self)
            if collision:
                self.fall_on = False
                self.fall_vel = np.array((0, 0), dtype=np.float)
            elif self.get_pos()[1] > GROUND_Y and not self.jump_anim:
                self.reset_on_fall()

        if self.listen_collision_above_blocks:
            collision = self.listen_collision_above_blocks(self) and not self.fall_on
            if collision:
                self.reset_on_fall()
        powerup = self.listen_collision_powerup(self)
        return True

    def reset_on_fall(self):
        self.dt = 0
        self.jump_anim = None
        self.fall_on = True

    def set_texture(self, new_texture):
        self.rect.texture = Image(new_texture).texture


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
        self.add(Color(1,1,1))
        self.rect = Rectangle(pos=(0,0), size=[SCREEN_WIDTH, GROUND_Y], texture=Image("img/sand.png").texture)
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
        self.add(Color(1, 1, 1))
        self.counter = 0
        self.bgs = ["img/ocean.jpg", "img/field.jpg", "img/clouds.jpg"]
        self.bg = Rectangle(pos=(0, 0), size=[SCREEN_WIDTH, SCREEN_HEIGHT], texture=Image("img/ocean.jpg").texture)
        self.add(self.bg)

    def on_update(self, dt):
        return True

    def get_pos(self):
        return self.bg.pos

    def change(self):
        self.counter = self.counter + 1 if self.counter < len(self.bgs) else self.counter
        self.bg.texture = Image(self.bgs[self.counter]).texture


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
        super(Powerup, self).__init__()
        self.pos = pos
        self.powerup_type = powerup_type
        self.texture = TEXTURES[powerup_type]
        self.powerup = Rectangle(pos=self.pos, size=[POWERUP_LENGTH, POWERUP_LENGTH],texture=self.texture)
        self.add(self.powerup)
        self.triggered = False
        self.activation_listeners = activation_listeners
        self.speed = speed

    def on_update(self, dt):
        self.powerup.pos -= np.array([dt * self.speed, 0])
        return not self.fell_offscreen()

    def fell_offscreen(self):
        return self.powerup.pos[0] + self.powerup.size[0] < 0 or self.triggered

    def get_pos(self):
        return self.powerup.pos

    def get_size(self):
        return self.powerup.size

    def activate(self, args=None):
        for i,listener in enumerate(self.activation_listeners):
            if args is None:
                listener()
            else:
                listener(*args[i])
        self.triggered = True

    def change_speed(self, new_speed):
        self.speed = new_speed


##
# PROGRESS BAR CLASS
# object that holds all the progress bars for risers, primary songs, filters
# also manages the label of text for the progress bars
# tracks on update each 0.5 sec
##
class ProgressBars(InstructionGroup):
    def __init__(self, text_label):
        super(ProgressBars, self).__init__()
        self.progress_bars = {}
        self.bar_positions = [(3.7* SCREEN_WIDTH / 5, SCREEN_HEIGHT * 0.95), (3.7 * SCREEN_WIDTH/5, SCREEN_HEIGHT*0.9), (3.7*SCREEN_WIDTH/5, SCREEN_HEIGHT*0.85)]
        self.text_label = text_label

    # add a new bar - pass in a generator object to extract sample length, and the sound name to refer to it
    def add_bar(self, wave_src, sound_name):
        new_bar = SoundProgressBar(wave_src, sound_name, self.bar_positions[len(self.progress_bars)])
        self.progress_bars[sound_name] = new_bar
        self.add(new_bar)

    def remove_bar(self, sound_name):
        self.progress_bars.pop(sound_name)

    def on_update(self, dt):
        removed = []
        self.text_label.text = ""
        for bar in self.progress_bars:
            self.text_label.text += bar + "\n"
            kept = self.progress_bars[bar].on_update(dt)
            if not kept:
                removed.append(bar)
        for r in removed:
            self.remove(self.progress_bars[r])
            self.progress_bars.pop(r)

    # reset primary song progress bar on transition
    def reset_frame(self):
        self.progress_bars["Primary Song"].reset_frame()


##
# SOUND PROGRESS BAR OBJECT
# This object is an individual bar, and contains the graphics for animating the bar
# on progress through the audio sample.
# args: wave_src - the generator to extract length of sample from
# args: sound_name - the sound name to refer to the object
# pos: the position to draw the progress bar
##
class SoundProgressBar(InstructionGroup):
    def __init__(self, wave_src, sound_name, pos):
        super(SoundProgressBar, self).__init__()
        self.wave_gen = wave_src
        self.sound_name = sound_name
        self.dt = 0  # the total time we've spent playing the audio sample
        self.end_frame = wave_src.get_length()  # the total length of the sample.
        self.outside_color = Color(1,1,1)
        self.outside_rect = Rectangle(pos=pos, size=[SCREEN_WIDTH/6, SCREEN_HEIGHT/20-5])
        self.inside_color = Color(0,1,0)
        self.inside_rect = Rectangle(pos=pos+np.array([2,2]), size=[0, SCREEN_HEIGHT/20-9])
        self.max_length = SCREEN_WIDTH/6-4

        self.add(self.outside_color)
        self.add(self.outside_rect)
        self.add(self.inside_color)
        self.add(self.inside_rect)

    def on_update(self, dt):
        self.dt += dt
        if self.dt * Audio.sample_rate / self.end_frame > 0.9:  # red
            self.inside_color.g = 0
        elif self.dt * Audio.sample_rate / self.end_frame > 0.67:  # yellow
            self.inside_color.r = 1

        self.inside_rect.size = [int((self.dt * Audio.sample_rate / self.end_frame) * self.max_length), SCREEN_HEIGHT/20 -9]

        return not self.dt * Audio.sample_rate > self.end_frame

    # on transition, reset the progress bar.
    def reset_frame(self):
        self.dt = 0
        self.inside_color.r = 0
        self.inside_color.g = 1


##
# WRAPPER CLASS FOR THE GAME DISPLAY
# args: song_data, powerup_data: annotations indicating where blocks and powerups should be, respectively.
# song_data: [sec, measure, y_index, # units]
# powerup_data: [sec, measure, powerup_str]
# this class contains the PLAYER object, GROUND object, and all POWERUPS AND BLOCKS on screen
class GameDisplay(InstructionGroup):
    def __init__(self, song_data, powerup_data, audio_manager, label):
        super(GameDisplay, self).__init__()
        self.song_data = song_data
        self.powerup_data = powerup_data
        self.audio_manager = audio_manager
        self.color = Color(1,1,1)
        self.add(self.color)

        self.background = Background()
        self.add(self.background)
        self.player = Player(listen_collision_above_blocks=self.listen_collision_above_block,
                        listen_collision_ground=self.listen_collision_ground,
                             listen_collision_powerup=self.listen_collision_powerup,
                             listen_collision_below_blocks=self.listen_collision_below_block)

        self.add(self.player)
        self.ground = Ground()
        self.add(self.ground)        

        self.current_frame = 0
        self.current_block = 0  # current block ind to add from song_data
        self.current_powerup = 0  # current powerup ind to add from powerup_data

        self.blocks = set()  # on-screen blocks
        self.powerups = set()  # on-screen powerups

        self.paused = True

        self.index_to_y = [0, int(SCREEN_HEIGHT/5), int(SCREEN_HEIGHT * 2/5), int(SCREEN_HEIGHT*3/5)]

        self.powerup_listeners = {'powerup_note': [self.audio_manager.play_powerup_effect],
                                  'lower_volume': [self.audio_manager.lower_volume],
                                  'raise_volume': [self.audio_manager.raise_volume],
                                  'error': [self.audio_manager.play_error_effect],
                                  'bass_boost': [self.audio_manager.bass_boost],
                                  'vocals_boost': [self.audio_manager.vocals_boost],
                                  'reset_filter': [self.audio_manager.reset_filter],
                                  'underwater': [self.audio_manager.underwater],
                                  'speedup': [self.audio_manager.speedup, self.increase_game_speed],
                                  'slowdown': [self.audio_manager.slowdown, self.decrease_game_speed],
                                  'reset_speed': [self.audio_manager.reset_speed, self.reset_game_speed],
                                  'sample_on':[self.audio_manager.sample_on],
                                  'sample_off':[self.audio_manager.sample_off],
                                  'reset_sample':[self.audio_manager.reset_sample],
                                  'riser':[self.audio_manager.riser],
                                  "trophy": [self.audio_manager.toggle, self.toggle],
                                  'danger': [self.audio_manager.toggle, self.toggle]}

        self.game_speed = INIT_RIGHT_SPEED
        self.block_texture = "img/wave.png"

        # powerup progress bars
        self.powerup_bars = ProgressBars(label)
        self.powerup_bars.add_bar(self.audio_manager.primary_song, self.audio_manager.get_song_name())
        self.add(self.powerup_bars)
        self.last_powerup_bars_update = 0

    # toggle paused of game or not
    def toggle(self):
        self.paused = not self.paused

    def on_jump(self):
        self.player.on_jump()

    def on_fall(self):
        self.player.on_fall()

    # call every frame to make blocks and powerups flow towards player
    def on_update(self, dt):
        if not self.paused:
            self.player.on_update(dt)
            if abs(self.current_frame - self.last_powerup_bars_update) > Audio.sample_rate / 2:
                self.powerup_bars.on_update(dt + 0.5)
                self.last_powerup_bars_update = self.current_frame
            removed_items = set()

            # UPDATE EACH POWERUP AND BLOCK, AND TRACK IF THEY ARE REMOVED OR NOT FROM THE GAME FRAME
            # For blocks, track if a block goes off screen
            # for powerups, track if a powerup is activated or go off screen
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
                self.add_block(self.current_block)
                self.current_block += 1
                
            # this is how we add new blocks. export to individual functions so we can
            # add new blocks/powerups easily

            if self.current_powerup < len(self.powerup_data) and self.current_frame / Audio.sample_rate > self.powerup_data[
                self.current_powerup][0] - SECONDS_FROM_RIGHT_TO_PLAYER:
                self.add_powerup(self.current_powerup)
                self.current_powerup += 1

        return True

    # block adder function
    def add_block(self, block):
        """ Creates a new Block object from an index into the list of block tuples and adds it to the game."""
        y_pos = self.song_data[block][1]
        units = self.song_data[block][2]
        new_block = Block((SCREEN_WIDTH, self.index_to_y[y_pos] + GROUND_Y), Color(1,1,1), units, self.game_speed, self.block_texture)
        self.blocks.add(new_block)
        self.add(new_block)

    def add_powerup(self, powerup):
        """Creates a new Powerup object from an index into the list of powerup tuples and adds it to the game."""
        y_pos = self.powerup_data[powerup][1]
        p_type = self.powerup_data[powerup][2]
        new_powerup = Powerup((SCREEN_WIDTH, self.index_to_y[y_pos-1] + GROUND_Y + BLOCK_HEIGHT), p_type, self.game_speed, self.powerup_listeners[p_type])
        self.powerups.add(new_powerup)
        self.add(new_powerup)

    # add new blocks for new song
    def change_blocks(self):
        removed_items = set()
        for block in self.blocks:
            removed_items.add(block)
        for item in removed_items:
            self.remove(item)
        self.blocks = set()
        self.current_block = 0

    # add new powerups for new song
    def add_new_song_powerups(self, new_powerups):
        removed_items = set()
        for block in self.blocks:
            removed_items.add(block)
        for item in removed_items:
            self.remove(item)
        self.powerups = set()
        self.current_powerup = 0

    # update the local current frame variable
    def update_frame(self, frame):
        self.current_frame = frame

    # listener for player with block objects
    def listen_collision_below_block(self, player):
        for block in self.blocks:
            if block.get_pos()[0] < player.get_pos()[0] < block.get_pos()[0] + block.get_size()[0] \
                    or block.get_pos()[0] < player.get_pos()[0] + PLAYER_WIDTH < block.get_pos()[0] + block.get_size()[0]:
                if block.get_pos()[1] < player.get_pos()[1] <= block.get_pos()[1] + BLOCK_HEIGHT:
                    # CASE 1: FALL ONTO A NEW BLOCK
                    player.set_y(block.get_pos()[1] + BLOCK_HEIGHT)
                    return True
        return False

    def listen_collision_above_block(self, player):
        for block in self.blocks:
            if block.get_pos()[0] < player.get_pos()[0] < block.get_pos()[0] + block.get_size()[0] \
                    or block.get_pos()[0] < player.get_pos()[0] + PLAYER_WIDTH < block.get_pos()[0] + block.get_size()[0]:
                if block.get_pos()[1] < player.get_pos()[1] + PLAYER_HEIGHT < block.get_pos()[1] + BLOCK_HEIGHT:
                # CASE 2: PLAYER Top border is inside the block, which suggests a jump up into a block
                # (just fall back down)
                    return True
        return False

    # listener for player collision with ground
    def listen_collision_ground(self, player):
        if player.get_pos()[1] < GROUND_Y:
            player.set_y(GROUND_Y)
            return True
        return False

    # listener for player with powerups objects
    def listen_collision_powerup(self, player):
        for powerup in self.powerups:
            if powerup.get_pos()[0] < player.get_pos()[0] < powerup.get_pos()[0] + POWERUP_LENGTH or \
                                    powerup.get_pos()[0] < player.get_pos()[0] + PLAYER_WIDTH < powerup.get_pos()[0] + POWERUP_LENGTH:
                if player.get_pos()[1] < powerup.get_pos()[1] < player.get_pos()[1] + PLAYER_HEIGHT or \
                                        player.get_pos()[1] < powerup.get_pos()[1] + POWERUP_LENGTH < player.get_pos()[1] + PLAYER_HEIGHT:
                    if powerup.powerup_type == "sample_on" or powerup.powerup_type == "sample_off":
                        powerup.activate([[self.current_frame]])
                    elif powerup.powerup_type == "riser":
                        powerup.activate([[self.powerup_bars.add_bar]])
                    else:
                        powerup.activate()
                    return powerup
        return None

    # like with audio, increase or decrease game speed
    def increase_game_speed(self):
        self.game_speed = self.game_speed * 2**(1/12)
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def decrease_game_speed(self):
        self.game_speed = self.game_speed / 2**(1/12)
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    def reset_game_speed(self):
        self.game_speed = INIT_RIGHT_SPEED
        for block in self.blocks:
            block.change_speed(self.game_speed)
        for powerup in self.powerups:
            powerup.change_speed(self.game_speed)

    # on transition, change the images, reset game speed, and reset the progress bar.
    def transition(self, player_texture, ground_texture, block_texture):
        self.player.set_texture(player_texture)
        self.ground.set_texture(ground_texture)
        self.background.change()
        self.block_texture = block_texture
        self.reset_game_speed()
        self.powerup_bars.reset_frame()
