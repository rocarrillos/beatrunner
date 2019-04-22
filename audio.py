import sys

from common.core import *
from common.gfxutil import *
from common.audio import *
from common.synth import *
from common.clock import *
from common.mixer import *
from common.wavegen import *
from common.wavesrc import *

import numpy as np
import math

###############################################
# DESIGN:
# The Audio class will be in charge of playing the main track as well as FX.
# The main track will have certain effects that can be applied to it, i.e. bass boost
# This will have to happen via envelopes
# FX will happen via the Synth functionality


class AudioManager(object):
    def __init__(self, audiofile):
        super(AudioManager, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.song = WaveGenerator(WaveFile(audiofile))
        self.song.set_gain(0.50)
        self.speed_mod = SpeedModulator(self.song)
        self.filter = Filter(self.speed_mod)
        self.sfx = Synth("data/FluidR3_GM.sf2")
        self.volume = 100
        self.song.set_gain(0.25)
        self.mixer.set_gain(1)
        self.powerup_note = 69
        self.error_note = 60
        self.jump_note = 75
        self.effect_volume = 100

        # effects programming
        self.sfx.program(0, 0, 116) # taiko drum
        self.sfx.program(1, 0, 98) # crystal
        self.sfx.program(2, 0, 121) # breath noise
        self.sfx.program(3, 0, 114)  # soundtrack
        self.sfx.program(4, 0, 126) # applause

        # hook everything up
        self.mixer.add(self.filter)
        self.mixer.add(self.sfx)
        self.audio.set_generator(self.mixer)
        self.active = True
        
    def toggle(self):
        self.active = not self.active

    # VOLUME EFFECTS
    def lower_volume(self):
        # reduce volume by half
        self.volume = self.volume * 0.5
        self.mixer.set_gain(self.volume / 100)

    def raise_volume(self):
        # raise volume by 2x, up to 100
        self.volume = min(self.volume * 2, 100)
        self.mixer.set_gain(self.volume / 100)

    # SOUND EFFECTS
    def play_error_effect(self):
        self.sfx.noteon(0, self.error_note, self.effect_volume)

    def stop_error_effect(self):
        self.sfx.noteoff(0, self.error_note)

    def play_powerup_effect(self):
        self.sfx.noteon(1, self.powerup_note, self.effect_volume)

    def stop_powerup_effect(self):
        self.sfx.noteoff(1, self.powerup_note)

    def play_jump_effect(self):
        self.sfx.noteon(1, self.jump_note, self.effect_volume)

    def stop_jump_effect(self):
        self.sfx.noteoff(2, self.jump_note)

    def play_lose_effect(self):
        self.sfx.noteon(3, self.error_note, self.effect_volume)

    def stop_lose_effect(self):
        self.sfx.noteoff(3, self.error_note)

    def play_win_effect(self):
        self.sfx.noteon(4, self.powerup_note, self.effect_volume)
    
    def stop_win_effect(self):
        self.sfx.noteoff(4, self.powerup_note)

    # MAIN TRACK EFFECTS
    def bass_boost(self):
        self.filter.change_pass("low")

    def reset_filter(self):
        self.filter.change_pass("reset")

    def vocals_boost(self):
        self.filter.change_pass("high")

    def underwater(self):
        self.filter.change_pass("band")

    def ethereal(self):
        pass

    def speedup(self):
        self.speed_mod.set_speed(self.speed_mod.get_speed() * 2**(1/12))

    def slowdown(self):
        self.speed_mod.set_speed(self.speed_mod.get_speed() / 2**(1/12))

    def reset_speed(self):
        self.speed_mod.set_speed(1)

    def get_current_frame(self):
        return self.song.frame

    def on_update(self):
        if self.active:
            self.audio.on_update()


# Decided to include SpeedModulator for speedup/slowdown and key change effect
class SpeedModulator(object):
    def __init__(self, generator, speed = 1.0):
        super(SpeedModulator, self).__init__()
        self.generator = generator
        self.speed = speed
        self.continue_flag = True

    def set_speed(self, speed) :
        self.speed = speed

    def get_speed(self):
        return self.speed

    def release(self):
        self.continue_flag = False

    def generate(self, num_frames, num_channels) :
        # this is the fun part lol
        if num_channels == 2:
            frames_to_make = int(num_frames * num_channels * self.speed)
            frames_to_make = frames_to_make + frames_to_make % num_channels # to round it out
            # we have the number of frames we need to extract from the generator
            frames = self.generator.generate(int(frames_to_make / num_channels), num_channels)[0]
            # we have the frames. Now we need to interpolate
            lframes = frames[::2]
            rframes = frames[1::2]
            lneeds = np.linspace(0, len(lframes), num_frames)
            lhaves = np.arange(0, len(lframes))
            rneeds = np.linspace(0, len(rframes), num_frames)
            rhaves = np.arange(0, len(rframes))
            lframes = np.interp(lneeds, lhaves, lframes)
            rframes = np.interp(rneeds, rhaves, rframes)
            output = np.empty(num_channels * num_frames, dtype=lframes.dtype)
            output[0::2] = lframes
            output[1::2] = rframes
        else:
            frames = self.generator.generate(int(num_frames * self.speed))
            needs = np.linspace(0, len(frames), num_frames)
            output = np.interp(needs, np.arange(0, len(frames), num_frames), frames)
        return (output, self.continue_flag)


# Functions for applying audio filters
class Filter(object):
    def __init__(self, generator, filter_pass="low"):
        super(Filter, self).__init__()
        self.generator = generator
        self.filter_pass = filter_pass
        self.cutoff = 400.0 # just as default
        self.samplerate = 44100
        self.continue_flag = True
        self.active = False

    def release(self):
        self.continue_flag = False

    def change_pass(self, new_pass):
        valids = ["low", "high", "band"]
        if new_pass in valids:
            self.active = True
            self.filter_pass = new_pass
            if new_pass == valids[0]:
                self.cutoff = 600.0
            elif new_pass == valids[1]:
                self.cutoff = 300.0
            else:
                self.cutoff = 200.0
        elif new_pass == "reset":
            self.active = False
        else:
            pass

    def generate(self, num_frames, num_channels):
        frames = self.generator.generate(num_frames, num_channels)[0]
        if self.active:
            frames_left = frames[0::2]
            frames_right = frames[1::2]
            freq_ratio = self.cutoff / self.samplerate
            n = int(math.sqrt(0.196196 + freq_ratio**2) / freq_ratio)
            frames_left = running_mean(frames_left, n)
            frames_right = running_mean(frames_right, n)
            frames[0::2] = frames_left
            frames[1::2] = frames_right
        return (frames, self.continue_flag)



def running_mean(x, windowsize):
    cumesum = np.cumsum(np.insert([float(i) for i in x], 0, 0))
    ret = np.concatenate((cumesum[:windowsize - 1] / (windowsize), (cumesum[windowsize:] - cumesum[:-windowsize]) / (windowsize)), axis=None)
    return ret