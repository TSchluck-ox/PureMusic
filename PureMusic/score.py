#!/usr/bin/env python
import os
import json
import wave
import struct
import pyaudio
import numpy as np
from . import notes

'''
score.py

Contains the main object: Score, which has some number of notes, which can be converted to
bytes to be played through speakers, or written to .wav
Can be stored or loaded as a .pmusic file, a .json filetype
'''

PM_EXT = '.pmusic'

class ScoreError(Exception):
    pass

def render_note(note_j: dict, rate: int) -> np.ndarray:
    '''
    Renders ndarray of note from a note dictionary

    Args:
        note_j: dict -> of note kws
        rate: int -> sample rate Hz
    Returns:
        ndarray of compiled note
    I/O:
        None
    '''
    dyn = getattr(notes, note_j['dyn'])
    env = getattr(notes, note_j['envelope'])
    wave = getattr(notes, note_j['wave'])
    return dyn(env(wave(note_j['freq'], note_j['dur'], note_j['vol'], rate, note_j['over'],
                        note_j['freq2']),
                   rate, note_j['attc'], note_j['dec']), rate, note_j['to'],
                   note_j['start_d'], note_j['end_d'])

class Score(object):
    ''' Stores data for a given project and handles operations '''
    def __init__(self, rate: int =44100, title: str ='untitled'):
        self.rate = rate
        self.title = title
        self.notes_j = []
        self.notes_b = []
        self.end = 0.0

    def add(self, freq: float, dur: float, vol: float, attc: float =0.05, dec: float =0.05,
            over: list =[], wave: str ='sine', envelope: str ='rectangular', dyn: str ='no_dyn',
            start: float =0.0, to: float =2.0, start_d: float =0.0, end_d=None, freq2: float =550.0):
        '''
        Adds a note given all possible arguments for a note

        Args:
            all that stuff
        Returns:
            None
        I/O:
            None
        '''
        if not hasattr(notes, wave) or not hasattr(notes, envelope) or not hasattr(notes, dyn):
            raise ScoreError

        new_note = {
            'freq': freq,
            'dur': dur,
            'vol': vol,
            'attc': attc,
            'dec': dec,
            'over': over,
            'freq2': freq2,
            'wave': wave,
            'envelope': envelope,
            'dyn': dyn,
            'start': start,
            'to': to,
            'start_d': start_d,
            'end_d': end_d,
        }

        if dur + start > self.end:
            self.end = dur + start

        self.notes_j.append(new_note)
        self.notes_b.append(render_note(new_note, self.rate))

    def add_trill(self, freq1: float, freq2: float, length: float, num: int, vol: float, attc: float =0.01, 
                  dec: float =0.01, over: list =[], wave: str ='sine', envelope: str ='rectangular',
                  dyn: str ='no_dyn', start: float =0.0, to: float =2.0, start_d: float =0.0, end_d=None):
        '''
        Simplifies the creation of a trill
        '''
        ind_dur = length / num
        this_s = start
        for i in range(num):
            freq = freq1 if i % 2 == 0 else freq2
            self.add(freq, ind_dur, vol, attc, dec, over, wave, envelope, dyn, this_s, to, start_d, end_d)
            this_s += ind_dur

    def _pad(self, idx: int) -> np.ndarray:
        '''
        pads a note to have empty sound an either side
        '''
        start_spl = int(self.rate * self.notes_j[idx]['start'])
        end_spl = int(self.end * self.rate) - (start_spl + len(self.notes_b[idx]))
        begin = np.zeros((start_spl,), dtype=np.float32)
        endd = np.zeros((end_spl,), dtype=np.float32)
        return np.concatenate((begin, self.notes_b[idx], endd))

    def render(self) -> bytes:
        '''
        Returns bytes from all notes in timing
        '''
        cvs = np.zeros(int(self.end*self.rate), dtype=np.float32)
        for idx in range(len(self.notes_j)):
            cvs += self._pad(idx)
        
        return cvs.tobytes()

    def __repr__(self):
        d = {
            'title': self.title,
            'rate': self.rate,
            'notes': self.notes_j,
        }

        return json.dumps(d)

    def save(self, path: str):
        if not path.endswith(PM_EXT):
            path += PM_EXT
        
        with open(path, 'w') as out:
            out.write(self.__repr__())

    def export(self, path: str):
        if not path.endswith('.wav'):
            path += '.wav'

        cvs = np.zeros(int(self.end*self.rate), dtype=np.float32)
        for idx in range(len(self.notes_j)):
            cvs += self._pad(idx)
        audio = cvs.tolist()

        with wave.open(path, 'wb') as wv:
            wv.setparams((1, 2, self.rate, len(audio),
                          "NONE", "not compressed"))
            for sample in audio:
                wv.writeframes(struct.pack('h', int(sample*32767)))

def load(path: str) -> Score:
    if not os.path.exists(path) or not path.endswith(PM_EXT):
        raise ScoreError
    
    with open(path, 'r') as jobj:
        dict_s = json.load(jobj)
    
    scr = Score(dict_s['rate'], dict_s['title'])

    for note in dict_s['notes']:
        scr.add(**note)

    return scr

def play(thing, rate=None):
    if isinstance(thing, Score):
        bstr = thing.render()
        rate = thing.rate
    elif isinstance(thing, bytes):
        bstr = thing
        if rate is None:
            raise ScoreError
    else:
        raise ScoreError

    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paFloat32,
                     channels=1,
                     rate=rate,
                     output=True)
    stream.write(bstr)
    stream.stop_stream()
    stream.close()
    pa.terminate()