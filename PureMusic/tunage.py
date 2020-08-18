#!/usr/bin/env python

class EqTemp(object):
    ''' Creates Equal Temperament obj to be called '''
    def __init__(self, tone_p_oct: int =12, z00: float =16.35):
        self.tpo = tone_p_oct
        self.z00 = z00
    def __call__(self, tone: int, oct: int) -> float:
        return (2**(tone/self.tpo)) * (2**oct) * self.z00

def teiltone(von: float, partial: int, oct: int =0) -> float:
    return von * partial * (2**oct)
