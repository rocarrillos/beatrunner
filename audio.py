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
    def __init__(self, first_file, second_file):
        super(AudioManager, self).__init__()
        self.audio = Audio(2)
        self.mixer = Mixer()
        self.sfx = Synth("data/FluidR3_GM.sf2")
        self.mixer.add(self.sfx)
        self.audio.set_generator(self.mixer)
        self.mixer.set_gain(1)

        # setup audio files
        self.primary_song = Song(first_file)
        self.secondary_song = Song(second_file)

        # effects notes
        self.powerup_note = 69
        self.error_note = 60
        self.jump_note = 75
        self.effect_volume = 100

        # effects programming
        self.sfx.program(0, 0, 116) # taiko drum
        self.sfx.program(1, 0, 98)  # crystal
        self.sfx.program(2, 0, 121) # breath noise
        self.sfx.program(3, 0, 114) # soundtrack
        self.sfx.program(4, 0, 126) # applause

        self.bpms = [120, 90, 140]
        self.transitions = 0

        # hook everything up
        self.mixer.add(self.primary_song)
        
        self.active = False

        # frame data for last transitions hit. used for determining token collection and bar management
        self.transition_lasthit_dict = {"riser":-1000000, "filter":-1000000, "volume": -1000000,
                                      "sample":-1000000, "speed":-1000000}

        self.transition_expiration_dict={"riser":9*Audio.sample_rate, "filter":8.5*Audio.sample_rate, "volume":3*Audio.sample_rate,
                                        "sample":3*Audio.sample_rate, "speed":3*Audio.sample_rate}
        self.ongoing_effects = []
        self.score = 0
        
    def toggle(self):
        self.active = not self.active

    # OVERALL VOLUME EFFECTS
    def lower_volume(self):
        # reduce volume by half
        self.mixer.set_gain(self.mixer.get_gain() * 0.5)

    def raise_volume(self):
        # raise volume by 2x, up to 100
        self.mixer.set_gain(min(self.mixer.get_gain() * 2, 1))

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
    def bass_boost(self, add_bar=None):
        # self.primary_filter.change_pass("low")
        self.primary_song.set_filter("low")
        self.transition_lasthit_dict["filter"] = self.get_current_frame()
        if add_bar: add_bar(8*Audio.sample_rate, "FILTER")

    def reset_filter(self):
        # self.primary_filter.change_pass("reset")
        self.primary_song.change_pass("reset")

    def vocals_boost(self, add_bar=None):
        # self.primary_filter.change_pass("high")
        self.primary_song.set_filter("high")
        self.transition_lasthit_dict["filter"] = self.get_current_frame()
        if add_bar: add_bar(8*Audio.sample_rate, "FILTER")

    def underwater(self):
        # self.primary_filter.change_pass("band")
        self.primary_song.change_pass("band")

    def riser(self, add_bar=None):
        riser = WaveGenerator(WaveFile("data/riser1.wav"))
        self.mixer.add(riser)
        self.transition_lasthit_dict["riser"] = self.get_current_frame()
        if add_bar: add_bar(riser.get_length(), "RISER")

    def ethereal(self):
        pass

    def get_primary_speed(self):
        return self.primary_song.get_speed()
    
    def get_secondary_speed(self):
        return self.secondary_song.get_speed() if self.secondary_song is not None else 1

    def get_primary_bpm(self):
        return self.bpms[self.transitions] * self.primary_song.get_speed()

    def get_secondary_bpm(self):
        if self.transitions < len(self.bpms) and self.secondary_song is not None:
            return self.bpms[self.transitions + 1] * self.secondary_song.get_speed()
        else:
            return 0

    # speedup the song and/or sampler
    def speedup(self):
        self.primary_song.set_speed(self.primary_song.get_speed() * 2**(1/12))
        self.transition_lasthit_dict["speed"] = self.get_current_frame()
        self.score += 10

    # slow down the song and /or sampler
    def slowdown(self):
        self.primary_song.set_speed(self.primary_song.get_speed() / 2**(1/12))   
        self.transition_lasthit_dict["speed"] = self.get_current_frame()     
        self.score += 10

    ###### SAMPLE EFFECTS #########
    # start the sample by retaining current frame
    def sample_on(self, frame):
        self.primary_song.set_sampling_on_frame(frame)
    # end the sample by loading in an audio snippet from [sample_on to sample off]
    # add it to the mixer, and set the primary song gain to 0 (but keep it playing)
    def sample_off(self, frame):
        self.primary_song.set_sampling_off_frame(frame)
        self.transition_lasthit_dict["sample"] = self.get_current_frame()


    # start the song transition. Here, init the new song as a WaveGenerator and add it to the mixer.
    def add_transition_song(self, audio_file):
        # self.secondary_song = Song(audio_file, gain=0.25)
        self.mixer.add(self.secondary_song)

    # end the song transition by putting all the secondary song refs as the primary song refs.
    # remove the primary song from the mixer.
    # remove any samples that may be playing.
    def end_transition_song(self, next_song):
        self.score += self.get_transition_score()
        self.mixer.remove(self.primary_song)
        self.primary_song.reset_sample()
        self.primary_song = self.secondary_song
        self.secondary_song = Song(next_song)
        self.transitions += 1
        
    # reset the sampling and reinstate the normal playing song
    def reset_sample(self):
        self.primary_song.reset_sample()

    def reset_speed(self):
        self.primary_song.set_speed(1)

    def reset_filter(self, remove_bar=None):
        self.primary_song.reset_filter()
        if remove_bar: remove_bar("FILTER")

    def reset(self, remove_bar=None):
        self.reset_speed()
        self.reset_sample()
        self.reset_filter(remove_bar)
        
    def add_transition_token(self):
        pass

    def get_current_frame(self):
        return self.primary_song.get_frame()

    def get_current_length(self):
        return self.primary_song.get_length()

    # calc the transition score based off of risers/samplers (and other effects in the future)
    def get_transition_score(self):
        score = 0
        # if self.transition_score_dict["riser"]:
        #     riser_frames = 8.34 * Audio.sample_rate
        #     riser_score = riser_frames - (self.get_current_frame() - self.transition_score_dict["riser"])
        #     score += abs(int(riser_score *100 / riser_frames) if riser_score > -1 * riser_frames else 0)
        # if self.sampler or (self.transition_score_dict["sample"] and self.transition_score_dict["sample"] - 2 * self.sample_off_frame < -1 * self.sample_on_frame):
        #     sampler_score = int(100 * self.sample_on_frame/self.sample_off_frame)
        #     score += sampler_score
        return score

    def get_ongoing_effects(self):
        return 

    def enough_past_powerups(self):
        c_frame = self.get_current_frame()
        past = 0
        for t in self.transition_lasthit_dict:
            if c_frame - self.transition_lasthit_dict[t] < self.transition_expiration_dict[t]:
                past += 1
        return past >= 2

    def on_update(self):
        if self.active:
            self.audio.on_update()


# Decided to include SpeedModulator for speedup/slowdown and key change effect
class SpeedModulator(object):
    def __init__(self, generator, speed = 1.0, gain=1.0):
        super(SpeedModulator, self).__init__()
        self.generator = generator
        self.speed = speed
        self.continue_flag = True

        self.set_gain(gain)

    def set_gain(self, new_gain):
        self.generator.set_gain(new_gain)

    def get_gain(self):
        return self.generator.get_gain()

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
            frames, self.continue_flag = self.generator.generate(int(num_frames * self.speed))
            needs = np.linspace(0, len(frames), num_frames)
            output = np.interp(needs, np.arange(0, len(frames), num_frames), frames)
        return (output, self.continue_flag)


class Song(object):
    def __init__(self, audiofile, speed = 1.0, gain = 0.9):
        super(Song, self).__init__()
        self.audio_file = audiofile
        self.wave_gen = WaveGenerator(WaveFile(self.audio_file))
        self.speed_mod = SpeedModulator(self.wave_gen)
        self.song_filter = FilterMixer(self.audio_file, self.speed_mod, self.get_gain, self.get_frame)
        self.gain = gain
        self.wave_gen.set_gain(self.gain)

        self.sampler_filter = None
        self.sampler_on_frame, self.sampler_off_frame = 0,0

    def set_gain(self, new_gain):
        self.speed_mod.set_gain(new_gain)
        if self.sampler_filter: self.sampler_filter.set_gain(new_gain)
        self.gain = new_gain

    def get_gain(self):
        return self.gain

    def set_speed(self, new_speed):
        self.song_filter.set_speed(new_speed)
        if self.sampler_filter: self.sampler_filter.set_speed(new_speed)

    def get_speed(self):
        return self.speed_mod.get_speed()

    def set_filter(self, filter_type):
        self.song_filter.set_filter(filter_type)
        if self.sampler_filter: self.sampler_filter.set_filter(filter_type)

    def reset_filter(self):
        self.song_filter.reset_filter()
        if self.sampler_filter: self.sampler_filter.reset_filter()

    def get_frame(self):
        return self.wave_gen.frame

    def get_length(self):
        return self.wave_gen.get_length()

    def set_sampling_on_frame(self, frame):
        self.sampler_on_frame = frame

    def set_sampling_off_frame(self, frame):
        if self.sampler_on_frame and not self.sampler_off_frame:
            self.sampler_off_frame = frame
            self.sampler_filter = FilterMixer(self.audio_file, SpeedModulator(WaveGenerator(WaveBuffer(self.audio_file, self.sampler_on_frame,self.get_frame() - self.sampler_on_frame), loop=True),speed=self.get_speed()), self.get_gain, self.get_frame)
            self.sampler_filter.set_gain(self.get_gain())
        elif self.sampler_off_frame:
            self.reset_sample()

    def reset_sample(self):
        self.sampler_filter = None
        self.sampler_on_frame, self.sampler_off_frame = 0, 0

    def generate(self, num_frames, num_channels):
        # if sampling on, you still want to generate from main song, to keep it playing. just don't return it.
        returned_frames = self.song_filter.generate(num_frames, num_channels)
        if self.sampler_filter:
            returned_frames = self.sampler_filter.generate(num_frames, num_channels)
        return returned_frames


class FilterMixer(object):
    def __init__(self, name, speed_mod, get_gain=None, get_frame=None, low=None, high=None):
        super(FilterMixer, self).__init__()
        self.audiofile_name = name
        self.regular = speed_mod
        self.high = high
        self.low = low
        self.get_gain = get_gain
        self.get_frame = get_frame
        self.mixer = Mixer()
        self.mixer.add(self.regular)
        self.frame, self.filter_frame_on = 0, 0
        self.f_type = None

        self.reg_to_anim = KFAnim((0,0),(8,1))

    def update(self):
        local_frame_secs = (self.frame - self.filter_frame_on) / Audio.sample_rate
        if self.f_type == "reg_to_high":
            # TODO(clhsu): gain setting here for dynamic filtering. Call self.frame
            self.high.set_gain(self.reg_to_anim.eval(local_frame_secs))
            self.regular.set_gain(1 - self.reg_to_anim.eval(local_frame_secs))
        elif self.f_type == "reg_to_low":
            self.low.set_gain(self.reg_to_anim.eval(local_frame_secs))
            self.regular.set_gain(1 - self.reg_to_anim.eval(local_frame_secs))
        if self.filter_frame_on and self.frame - self.filter_frame_on > 8 * Audio.sample_rate:
            self.reset_filter()

    def set_speed(self, new_speed):
        self.regular.set_speed(new_speed)
        if self.high: self.high.set_speed(new_speed)
        if self.low: self.low.set_speed(new_speed)

    def set_filter(self, f_type):
        self.f_type = f_type
        if f_type == "high":
            self.high = SpeedModulator(WaveGenerator(
                WaveBuffer(self.audiofile_name[:-4] + "_high.wav", self.get_frame(), 
                self.get_frame() + 4*Audio.sample_rate))
            )
            self.mixer.add(self.high)
            self.high.set_gain(self.get_gain())
            self.regular.set_gain(0)
        elif f_type == "low":
            self.low = SpeedModulator(WaveGenerator(
                WaveBuffer(self.audiofile_name[:-4] + "_low.wav", self.get_frame(), 
                self.get_frame() + 4*Audio.sample_rate))
            )
            self.mixer.add(self.low)
            self.low.set_gain(self.get_gain())
            self.regular.set_gain(0)

        elif f_type == "reg_to_high":
            self.high = SpeedModulator(WaveGenerator(
                WaveBuffer(self.audiofile_name[:-4] + "_high.wav", self.get_frame(), 
                self.get_frame() + 4*Audio.sample_rate)), gain=0.0
            )
            self.mixer.add(self.high)

        self.filter_frame_on = self.frame
    
    def reset_filter(self):
        if self.high:
            self.regular.set_gain(self.high.get_gain())
            self.mixer.remove(self.high)
        if self.low:
            self.regular.set_gain(self.low.get_gain())
            self.mixer.remove(self.low)
        self.filter_frame_on = 0
        self.f_type = None

    def set_gain(self, new_gain):
        self.regular.set_gain(new_gain)
        if self.high: self.high.set_gain(new_gain)
        if self.low: self.low.set_gain(new_gain)

    def generate(self, num_frames, num_channels):
        self.frame += num_frames
        self.update()
        return self.mixer.generate(num_frames, num_channels)


def running_mean(x, windowsize):
    cumesum = np.cumsum(np.insert([float(i) for i in x], 0, 0))
    ret = np.concatenate((cumesum[:windowsize - 1] / (windowsize), (cumesum[windowsize:] - cumesum[:-windowsize]) / (windowsize)), axis=None)
    return ret