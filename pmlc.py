#!/usr/bin/env python
import os
import sys
import json
import argparse
import PureMusic

VERSION = 'PureMusic version 0.0.3\n    Build date: 2020-14-08'

'''
"Compiler" for PureMusicLanguage files '.pml' or '.json'
also player for PureMusic files '.pmusic'
export to wav for '.pmusic' as well

Modes:
(default) -c, --compile: compiles into .pmusic file, which can be played [PML]
-w, --wave: exports to .wav file [PMUSIC, PML]
-p, --play: plays audio from file [PMUSIC, PML]
-g, --generate: creates new project in current directory []

Can use '.json' as specifiers for overtones, must be included in compilation [PML]
'''

PML_EXT = '.pml'
PMUSIC_EXT = '.pmusic'
JSON_EXT = '.json'
WAV_EXT = '.wav'

class CLIArgumentError(Exception):
    pass

class PMLError(Exception):
    pass

def pmusic_play(path: str) -> None:
    '''
    Given a path to a valid pmusic file, will open and play

    Args:
        path: str -> a path to .pmusic file
    Returns:
        None 
    I/O:
        loads file at path
    '''
    score = PureMusic.load(path)
    PureMusic.play(score)

def pmusic_wav(path: str, output=None) -> None:
    '''
    Given a path to a valid pmusic file, will open and export to output.wav

    Args:
        path: str -> a path to .pmusic file
        output: None or str -> output destination of .wav
    Returns:
        None
    I/O:
        opens path.pmusic, creates and writes output.wav
    '''
    dest = output or path[:-7]
    if not dest.endswith(WAV_EXT):
        dest += WAV_EXT

    score = PureMusic.load(path)
    score.export(dest)

def from_TET(*args) -> float:
    '''
    Converts from TET command string to a float

    Args:
        *args -> var number of int-able to be passed to PureMusic.EqTemp
    Returns:
        calcuated frequency from PureMusic.EqTemp
    I/O:
        None
    '''
    if len(args) == 3:
        return PureMusic.EqTemp(int(args[0]))(int(args[1]), int(args[2]))
    elif len(args) == 4:
        return PureMusic.EqTemp(int(args[0]), float(args[1]))(int(args[2]), int(args[3]))
    else:
        raise PMLError('TET takes 3 or 4 arguments, {} provided'.format(len(args)))

def from_OVT(txt: str) -> float:
    '''
    Converts from OVT command string to float

    Args:
        txt: str -> text string representation of OVT usage
    Returns:
        float calculated from supplied args
    I/O:
        None
    '''
    if txt.startswith('(TET '):
        args = txt[4:txt.index(')')].split()
        first = from_TET(*args)
        remain = txt[txt.index(')')+1:].split()
    else:
        spl = txt.split(maxsplit=1)
        first = float(spl[0])
        remain = spl[1].split()

    if len(remain) == 1:
        return PureMusic.teiltone(first, int(remain[0]))
    elif len(remain) == 2:
        return PureMusic.teiltone(first, int(remain[0]), int(remain[1]))
    else:
        raise PMLError('OVT takes 2 or 3 arguments, {} provided'.format(len(remain)+1))

def freq_parse(nto_obj, key) -> None:
    '''
    Parses strings for frequency related keys
    Does not return, dicts or lists are immutable and so are updated

    Args:
        nto_obj: dict or list -> representation of trill or note PureMusic objs
        key: int or str -> key in nto_obj to 'freq' type arg to be parsed
    Returns:
        None
    I/O:
        None
    '''
    if any((isinstance(nto_obj, dict) and key in nto_obj and isinstance(nto_obj[key], str),
            isinstance(nto_obj, list) and len(nto_obj) > key and isinstance(nto_obj[key], str))):
        if nto_obj[key].startswith('TET '):
            args = nto_obj[key][4:].split()
            nto_obj[key] = from_TET(*args)

        elif nto_obj[key].startswith('OVT '):
            nto_obj[key] = from_OVT(nto_obj[key][4:])
        else:
            raise PMLError('{} string could not be parsed'.format(nto_obj[key]))

def overtone_parse(note: dict, packages: dict, key: str) -> None:
    '''
    Parses strings for overtone related keys
    Does not return, dicts are immutable

    Args:
        note: dict -> representation of trill or note PureMusic objs
        packages: dict -> dictionary of packages used in this project
        key: str -> string key in note dictionary to be parsed as overtone
    Returns:
        None
    I/O:
        None
    '''
    if key in note and isinstance(note[key], str):
        pkg, itm = note[key].split('.', 1)

        if pkg in packages and itm in packages[pkg]:
            note[key] = packages[pkg][itm]

        else:
            raise PMLError('Could not resolve over: {}'.format(note[key]))

def parse_note_list(note: list, packages: dict) -> tuple:
    '''
    Parses a note written as a list

    Args:
        note: list -> list representation of a note obj
        packages: dict -> dictionary of packages used in this project
    Returns:
        note: list -> input note with popped args and parsed freq args
        outdict: dict -> dictionary of kwargs popped from note list
    I/O:
        None
    '''
    outdict = {}

    if len(note) > 3:
        outdict['start'] = note.pop(3)
    if len(note) > 3:
        outdict['wave'] = note.pop(3)
    if len(note) > 3:
        outdict['over'] = note.pop(3)

    overtone_parse(outdict, packages, 'over')
    freq_parse(note, 0)

    return note, outdict

def parse_trill_list(note: list, packages: dict) -> tuple:
    '''
    Parses a trill written as a list

    Args:
        note: list -> list representation of a trill obj
        packages: dict -> dictionary of packages used in this project
    Returns:
        note: list -> trill object with args popped and parsed
        outdict: dict -> kwargs popped from list
    I/O:
        None
    '''
    outdict = {}

    if len(note) > 5:
        outdict['start'] = note.pop(5)
    if len(note) > 5:
        outdict['wave'] = note.pop(5)
    if len(note) > 5:
        outdict['over'] = note.pop(5)

    overtone_parse(outdict, packages, 'over')
    freq_parse(note, 0)
    freq_parse(note, 1)

    return note, outdict

def pml_to_score(pml, packages: dict) -> PureMusic.Score:
    '''
    Converts pml (or .json) fileobj into PureMusic.Score object

    Args:
        pml: IO-readable -> pml readable file in json format
        packages: dict -> dictionary of packages used in this project
    Returns:
        score: PureMusic.Score -> score object loaded from pml
    I/O:
        loads json from pml fileobj
    '''
    loaded = json.load(pml)
    rate = loaded.get('rate') or 44100
    title = loaded.get('title') or 'untitled'
    score = PureMusic.Score(rate, title)

    if 'notes' in loaded:
        for note in loaded['notes']:
            if isinstance(note, list):
                args, kwargs = parse_note_list(note, packages)
                score.add(*args, **kwargs)

            elif isinstance(note, dict):
                freq_parse(note, 'freq')
                freq_parse(note, 'freq2')
                overtone_parse(note, packages, 'over')
                score.add(**note)

            else:
                raise PMLError('{} could not be understood'.format(note))

    if 'trills' in loaded:
        for trill in loaded['trills']:
            if isinstance(trill, list):
                args, kwargs = parse_trill_list(trill, packages)
                score.add_trill(*args, **kwargs)

            elif isinstance(trill, dict):
                freq_parse(trill, 'freq1')
                freq_parse(trill, 'freq2')
                overtone_parse(trill, packages, 'over')
                score.add_trill(**trill)

            else:
                raise PMLError('{} could not be understood'.format(trill))

    return score

def unpack_pkgs(pkg_paths: list) -> dict:
    '''
    Gets package info from json package files

    Args:
        pkg_paths: list -> list of paths to packages to be used in this file
    Returns:
        package: dict -> dictionary of filenames (minus ext) => loaded json
    I/O:
        reads from all package paths in list
    '''
    package = {}

    for path in pkg_paths:
        if not path.endswith(JSON_EXT):
            raise CLIArgumentError('Unsupported file format {}'.format(path))

        package_name = os.path.basename(path)[:-5]

        with open(path, 'r') as jobj:
            this_p = json.load(jobj)

        package[package_name] = this_p
    
    return package

def compile_(paths: list, output: str) -> None:
    '''
    Converts a pml (.pml or .json) into .pmusic json file

    Args:
        paths: list -> paths to pml, followed by json packages
        output: str -> path to output.pmusic
    Returns:
        None
    I/O:
        Reads all input files, writes using .save the pmusic file at output location
    '''
    if paths[0].endswith(PML_EXT) or paths[0].endswith(JSON_EXT):
        if len(paths) > 1:
            pkg = unpack_pkgs(paths[1:])
        else:
            pkg = {}
        with open(paths[0], 'r') as pml:
            score = pml_to_score(pml, pkg)

        score.save(output)

    else:
        raise CLIArgumentError('File {} of unsupported format'.format(paths[0]))

def wave_(paths: list, output: str) -> None:
    '''
    Exports pml or pmusic to .wav file

    Args:
        paths: list -> list of paths to pml followed by json packages or to pmusic file
        output: str -> output path to .wav
    Returns:
        None
    I/O:
        reads .pml, .json, .pmusic files, exports to output.wav
    '''
    if paths[0].endswith(PMUSIC_EXT):
        if len(paths) > 1:
            raise CLIArgumentError('Too many files provided')
        else:
            pmusic_wav(paths[0], output)

    elif paths[0].endswith(PML_EXT) or paths[0].endswith(JSON_EXT):
        if len(paths) > 1:
            pkg = unpack_pkgs(paths[1:])
        else:
            pkg = {}
        with open(paths[0], 'r') as pml:
            score = pml_to_score(pml, pkg)
        
        score.export(output)

    else:
        raise CLIArgumentError('File {} of unsupported format'.format(paths[0]))

def play_(paths: list, output: str) -> None:
    '''
    Reads .pml or .pmusic, and plays music to speakers

    Args:
        paths: list -> list of paths to .pml, .json packages or .pmusic
        output: str -> path to output, unused in this case (makes main easier to use)
    Returns:
        None
    I/O:
        Reads from all provided files, does not write output
    '''
    if paths[0].endswith(PMUSIC_EXT):
        if len(paths) > 1:
            raise CLIArgumentError('Too many files provided')
        else:
            pmusic_play(paths[0])

    elif paths[0].endswith(PML_EXT) or paths[0].endswith(JSON_EXT):
        if len(paths) > 1:
            pkg = unpack_pkgs(paths[1:])
        else:
            pkg = {}
        with open(paths[0], 'r') as pml:
            score = pml_to_score(pml, pkg)

        PureMusic.play(score)

    else:
        raise CLIArgumentError('File {} of unsupported format'.format(paths[0]))

def gen_(paths: list, output: str) -> None:
    '''
    Generates a starter project to get going

    Args:
        paths: list -> first used as title, second used as .pml .json switch
        output: str -> unused
    Returns:
        None
    I/O:
        writes starter file using json.dump
    '''
    STARTER = {
        'title': 'Untitled',
        'rate': 44100,
        'notes': [],
        'trills': [],
    }

    pth = 'a'
    ext = PML_EXT
    if len(paths) > 0:
        pth = paths[0]
        STARTER['title'] = pth

        if len(paths) > 1:
            if paths[1].lower() == 'json':
                ext = JSON_EXT

    with open(pth+ext, 'w') as pml:
            json.dump(STARTER, pml, indent=4)

def main():
    parser = argparse.ArgumentParser(description='PureMusicLanguage Compiler')

    parser.add_argument('-v',
                        '--version',
                        help='Get version information',
                        action='store_true')
    parser.add_argument('-w',
                        '--wave',
                        help='Export to .wav file\nSupported extensions: [.pml, .pmusic]',
                        action='store_true')
    parser.add_argument('-c',
                        '--compile',
                        help='Compiles PureMusicLanguage to PureMusic file\nSupported extensions: [.pml]',
                        action='store_true')
    parser.add_argument('-p',
                        '--play',
                        help='Play audio from file through speakers\nSupported extensions: [.pml, .pmusic]',
                        action='store_true')
    parser.add_argument('-g',
                        '--generate',
                        help='Generates new pml project in current directory',
                        action='store_true')
    parser.add_argument('paths',
                        help='Paths to accepted file types',
                        nargs='*')
    parser.add_argument('-o',
                        '--output',
                        help='Path of output file')

    if '-v' in sys.argv or '--version' in sys.argv:
        sys.exit(print(VERSION))
    args = parser.parse_args(sys.argv[1:])

    mode = compile_

    if any((args.wave, args.compile, args.play, args.generate)):
        if args.wave and not any((args.compile, args.play, args.generate)):
            mode = wave_
        elif args.play and not any((args.compile, args.wave, args.generate)):
            mode = play_
        elif args.compile and not any((args.play, args.wave, args.generate)):
            mode = compile_
        elif args.generate and not any((args.play, args.compile, args.wave)):
            mode = gen_
        else:
            raise CLIArgumentError('Cannot specify multiple modes')

    if len(args.paths) < 1 and mode != gen_:
        raise CLIArgumentError('No files provided')
    else:
        mode(args.paths, args.output)

if __name__ == '__main__':
    sys.exit(main())