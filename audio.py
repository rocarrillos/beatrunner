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

        self.mixer.add(self.song)
        self.mixer.add(self.sfx)
        self.active = True
        
    def toggle(self):
        self.active = not self.active

    def lower_volume(self):
        pass

    def raise_volume(self):
        pass

    def play_error_effect(self):
        pass

    def play_powerup_effect(self):
        pass

    def play_jump_effect(self):
        pass

    def play_lose_effect(self):
        pass

    def play_win_effect(self):
        pass

    def on_update(self):
        if self.active:
            self.audio.on_update()
