# Copyright (c) 2015 Johannes Sasongko <sasongko@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


from __future__ import division, print_function, unicode_literals

import ctypes


__all__ = ('Error', 'Media', 'MediaPlayer', 'State', 'Vlc')

_initialized = False


def _init():
    global _initialized
    if _initialized:
        return
    import sys
    c = ctypes
    if sys.platform == 'win32':
        libvlc = c.windll.libvlc
    else:
        libvlc = c.CDLL('libvlc.so')
    g = globals()

    def func(name, ret, *params):
        g[name] = f = getattr(libvlc, name)
        f.restype = ret
        f.argtypes = params

    func('libvlc_new', c.c_void_p, c.c_int, c.POINTER(c.c_char_p))
    func('libvlc_release', None, c.c_void_p)

    func('libvlc_media_get_state', c.c_int, c.c_void_p)
    func('libvlc_media_new_path', c.c_void_p, c.c_void_p, c.c_char_p)
    func('libvlc_media_release', None, c.c_void_p)

    func('libvlc_media_player_get_length', c.c_int64, c.c_void_p)
    func('libvlc_media_player_get_media', c.c_void_p, c.c_void_p)
    func('libvlc_media_player_get_position', c.c_float, c.c_void_p)
    func('libvlc_media_player_get_state', c.c_int, c.c_void_p)
    func('libvlc_media_player_get_time', c.c_int64, c.c_void_p)
    func('libvlc_media_player_is_playing', c.c_int, c.c_void_p)
    func('libvlc_media_player_new', c.c_void_p, c.c_void_p)
    func('libvlc_media_player_new_from_media', c.c_void_p, c.c_void_p)
    func('libvlc_media_player_play', c.c_int, c.c_void_p)
    func('libvlc_media_player_pause', None, c.c_void_p)
    func('libvlc_media_player_release', None, c.c_void_p)
    func('libvlc_media_player_set_media', None, c.c_void_p, c.c_void_p)
    func('libvlc_media_player_set_pause', None, c.c_void_p, c.c_int)
    func('libvlc_media_player_set_position', None, c.c_void_p, c.c_float)
    func('libvlc_media_player_set_time', None, c.c_void_p, c.c_int64)
    func('libvlc_media_player_stop', None, c.c_void_p)

    func('libvlc_audio_get_volume', c.c_int, c.c_void_p)
    func('libvlc_audio_set_volume', c.c_int, c.c_void_p, c.c_int)

    _initialized = True


class Error(Exception):
    pass


def _ensure(x):
    if x:
        return x
    raise Error


class State(int):
    (
        NOTHING_SPECIAL,
        OPENING,
        BUFFERING,
        PLAYING,
        PAUSED,
        STOPPED,
        ENDED,
        ERROR,
    ) = range(8)


class Vlc:
    def __init__(self, *args, **kwargs):
        """
        :param video: Enable video (default: True)
        :type video: bool
        :param audio: Enable audio (default: True)
        :type audio: bool
        """
        _init()
        args = list(args)
        if not kwargs.get('video', True):
            args.append('--no-video')
        if not kwargs.get('audio', True):
            args.append('--no-audio')
        args = (ctypes.c_char_p * len(args))(*args)
        self._as_parameter_ = _ensure(libvlc_new(len(args), args))

    def __del__(self):
        if hasattr(self, '_as_parameter_'):
            libvlc_release(self)


class Media(object):
    def __init__(self, vlc=None, path=None, libvlc_media=None):
        """
        :type vlc: Vlc
        :type path: bytes
        """
        if vlc:
            assert isinstance(path, bytes)
            self._as_parameter_ = _ensure(libvlc_media_new_path(vlc, path))
        else:
            self._as_parameter_ = _ensure(libvlc_media)

    def __del__(self):
        if hasattr(self, '_as_parameter_'):
            libvlc_media_release(self)

    @property
    def state(self):
        """
        :rtype: State
        """
        return State(libvlc_media_get_state(self))


class MediaPlayer(object):
    def __init__(self, vlc):
        """
        :type vlc: Vlc
        """
        self._as_parameter_ = _ensure(libvlc_media_player_new(vlc))

    def __del__(self):
        if hasattr(self, '_as_parameter_'):
            libvlc_media_player_release(self)

    @property
    def is_paused(self):
        """
        :rtype: bool
        """
        return self.state == State.PAUSED

    @is_paused.setter
    def is_paused(self, paused):
        """
        :type paused: bool
        """
        libvlc_media_player_set_pause(self, int(paused))

    @property
    def is_playing(self):
        """
        :rtype: bool
        """
        return bool(libvlc_media_player_is_playing(self))

    @property
    def media(self):
        """
        :rtype: Media
        """
        return Media(libvlc_media=libvlc_media_player_get_media(self))

    @media.setter
    def media(self, media):
        """
        :type media: Media
        """
        libvlc_media_player_set_media(self, media)

    def play(self):
        return libvlc_media_player_play(self)

    @property
    def position(self):
        """
        :rtype: float
        """
        return libvlc_media_player_get_position(self)

    @position.setter
    def position(self, pos):
        """
        :type pos: float
        """
        libvlc_media_player_set_position(self, ctypes.c_float(pos))

    @property
    def state(self):
        """
        :rtype: State
        """
        return State(libvlc_media_player_get_state(self))

    def stop(self):
        libvlc_media_player_stop(self)

    @property
    def time(self):
        """
        :return: Playback time, in seconds
        :rtype: float
        """
        return libvlc_media_player_get_time(self) / 1000.0  # From ms

    @time.setter
    def time(self, time):
        """
        :type time: float
        """
        libvlc_media_player_set_time(self, ctypes.c_int64(int(time * 1000)))

    def toggle_pause(self):
        libvlc_media_player_pause(self)

    @property
    def volume(self):
        """Audio volume.

        The normal value range is between 0 and 1. Higher numbers are accepted,
        but may cause clipping.

        :rtype: float
        """
        return libvlc_audio_get_volume(self) / 100.0

    @volume.setter
    def volume(self, volume):
        """
        :type volume: float
        """
        libvlc_audio_set_volume(self, int(volume * 100))


if __name__ == '__main__':
    import sys
    v = Vlc(video=False)
    m = Media(v, sys.argv[1])
    p = MediaPlayer(v)
    p.media = m
    p.play()
    import time
    time.sleep(5)
    p.stop()
