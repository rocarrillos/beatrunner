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
        self.sfx = Synth("data/FluidR3_GM.sf2")
        self.volume = 100
        self.powerup_note = 69
        self.error_note = 60
        self.jump_note = 75
        self.effect_volume = 75

        # effects programming
        self.sfx.program(0, 0, 116) # taiko drum
        self.sfx.program(1, 0, 101) # goblins
        self.sfx.program(2, 0, 121) # breath noise
        self.sfx.program(3, 0, 97)  # soundtrack
        self.sfx.program(4, 0, 126) # applause

        # hook everything up
        self.mixer.add(self.song)
        self.mixer.add(self.sfx)
        self.active = True
        
    def toggle(self):
        self.active = not self.active

    def lower_volume(self):
        # reduce volume by half
        self.volume = self.volume * 0.5
        self.mixer.set_gain(self.volume)

    def raise_volume(self):
        # raise volume by 2x, up to 100
        self.volume = min(self.volume * 2, 100)
        self.mixer.set_gain(self.volume)

    def play_error_effect(self):
        self.sfx.noteon(0, self.error_note, self.effect_volume)

    def stop_error_effect(self):
        self.sfx.noteoff(0, self.error_note)

    def play_powerup_effect(self):
        self.sfx.noteon(1, self.powerup_note, self.effect_volume)

    def stop_powerup_effect(self):
        self.sfx.noteoff(1, self.powerup_note)

    def play_jump_effect(self):
        self.sfx.noteon(1, self.powerup_note, self.effect_volume)

    def stop_jump_effect(self):
        self.sfx.noteoff(2, self.powerup_note)

    def play_lose_effect(self):
        self.sfx.noteon(3, self.error_note, self.effect_volume)

    def stop_lose_effect(self):
        self.sfx.noteoff(3, self.error_note)

    def play_win_effect(self):
        self.sfx.noteon(4, self.powerup_note, self.effect_volume)
    
    def stop_win_effect(self):
        self.sfx.noteoff(4, self.powerup_note)

    def bass_boost(self):
        pass

    def vocals_boost(self):
        pass

    def underwater(self):
        pass

    def ethereal(self):
        pass

    def on_update(self):
        if self.active:
            self.audio.on_update()
