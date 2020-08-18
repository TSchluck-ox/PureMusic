#!/usr/bin/env python
import numpy as np

'''
notes.py

Contains functions used for note generation
all functions in a set take the same arguments to make function switching easier in score.py
'''

VOLU = 0.2

class WaveError(Exception):
    pass

''' Wave functions '''
def sine(freq: float =440.0, dur: float =1.0, vol: float =0.5, rate: int =44100,
         over: list =[], freq2: float =550.0):
    '''
    Sine wave without overtone
    '''
    if vol > 1.0 or freq < 0.0:
        raise WaveError
    return ((VOLU*vol) * np.sin(2 * np.pi * np.arange(rate*dur) *
             freq/rate)).astype(np.float32)

def ramp(freq: float =440.0, dur: float =1.0, vol: float =0.5, rate: int =44100,
         over: list =[], freq2: float =550.0):
    '''
    Ramp wave without overtone
    '''
    if vol > 1.0 or freq < 0.0:
        raise WaveError
    return ((VOLU*vol) * np.mod((np.arange(rate*dur) * 
             freq/(2*rate)), 1.0)).astype(np.float32)

def noise(freq: float = 0.0, dur: float =1.0, vol: float =0.5, rate: int =44100,
          over: list =[], freq2: float =550.0):
    '''
    Static noise
    '''
    if vol > 1.0:
        raise WaveError
    return ((VOLU*vol) * np.random.rand(int(rate*dur))).astype(np.float32)

def any_acc(freq: float =330.0, dur: float =1.0, vol: float =0.5, rate: int =44100,
            over: list =[], freq2: float =550.0):
    '''
    Sine wave with overtone
    '''
    if vol > 1.0 or freq < 0.0:
        raise WaveError
    wave = sine(freq, dur, vol, rate, over, freq2)

    for partial, volmod in over:
        wave += sine(freq*partial, dur, vol*volmod, rate)

    return wave

def gliss_sine(freq: float =440.0, dur: float =1.0, vol: float =0.5, rate: int =44100,
               over: list =[], freq2: float =550.0):
    '''
    Gliss sine wave without overtone
    '''
    if vol > 1.0 or freq < 0.0 or freq2 < 0.0:
        raise WaveError

    rfreq2 = freq + (freq2-freq)/2.0
    return ((VOLU*vol) * np.sin(2 * np.pi * np.multiply(np.arange(rate*dur), 
                                np.linspace(freq, rfreq2, int(dur*rate)))/rate)).astype(np.float32)

def gliss_sine_acc(freq: float =440.0, dur: float =1.0, vol: float =0.5, rate: int =44100,
                   over: list =[], freq2: float =550.0):
    '''
    Gliss sine wave with overtone
    '''
    if vol > 1.0 or freq < 0.0 or freq2 < 0.0:
        raise WaveError
    wave = gliss_sine(freq, dur, vol, rate, over, freq2)

    for partial, volmod in over:
        wave += gliss_sine(freq*partial, dur, vol*volmod, rate, over, freq2*partial)

    return wave

''' TODO: ramp with overtone, square wave, others? '''

''' Envelope functions '''
def rectangular(wave: np.ndarray, rate: int =44100, attc: float =0.05, dec: float =0.05):
    '''
    Creates a linear attack and decay envelope
    '''
    attack = np.linspace(0.0, 1.0, int(attc*rate), dtype=np.float32)
    decay = np.linspace(1.0, 0.0, int(rate*dec), dtype=np.float32)
    mid = np.ones((len(wave)-len(attack)-len(decay),), dtype=np.float32)
    mask = np.concatenate((attack, mid, decay))
    return np.multiply(wave, mask)

''' TODO: ADSR, others? '''

''' Dynamic functions '''
def no_dyn(wave: np.ndarray, rate: int =44100, to: float =2.0, start_d: float =0.0,
           end_d=None):
    '''
    No dynamic function
    '''
    return wave

def cresc(wave: np.ndarray, rate: int =44100, to: float =2.0, start_d: float =0.0,
          end_d=None):
    '''
    Crescendo or decay dynamic funciton
    '''
    if start_d < 0.0 or (end_d is not None and (end_d*rate > len(wave) or start_d >= end_d)):
        raise WaveError
    endspl = len(wave) if end_d is None else int(rate*end_d)
    startspl = int(rate*start_d)
    precrc = np.ones(startspl, dtype=np.float32)
    postcrc = np.full(len(wave)-endspl, to, dtype=np.float32)
    cresc = np.linspace(1.0, to, endspl-startspl, dtype=np.float32)
    mask = np.concatenate((precrc, cresc, postcrc))
    return np.multiply(wave, mask)

''' TODO: swell, reverse swell, others? '''