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
    def __init__(self, *args):
        _init()
        args = (ctypes.c_char_p * len(args))(*args)
        self._as_parameter_ = _ensure(libvlc_new(len(args), args))

    def __del__(self):
        if hasattr(self, '_as_parameter_'):
            libvlc_release(self)


class Media:
    def __init__(self, instance, path):
        """
        :type instance: Vlc
        :type path: bytes
        """
        assert isinstance(path, bytes)
        self._as_parameter_ = _ensure(libvlc_media_new_path(instance, path))

    def __del__(self):
        if hasattr(self, '_as_parameter_'):
            libvlc_media_release(self)

    def get_state(self):
        """
        :rtype: State
        """
        return State(libvlc_media_get_state(self))


class MediaPlayer:
    def __init__(self, instance):
        """
        :type instance: Vlc
        """
        self._as_parameter_ = _ensure(libvlc_media_player_new(instance))

    def __del__(self):
        if hasattr(self, '_as_parameter_'):
            libvlc_media_player_release(self)

    def get_state(self):
        """
        :rtype: State
        """
        return State(libvlc_media_player_get_state(self))

    def get_time(self):
        """
        :return: Playback time, in milliseconds
        :rtype: int
        """
        return libvlc_media_player_get_time(self)

    def get_volume(self):
        return libvlc_audio_get_volume(self)

    def is_playing(self):
        return bool(libvlc_media_player_is_playing(self))

    def pause(self):
        libvlc_media_player_pause(self)

    def play(self):
        return libvlc_media_player_play(self)

    def set_media(self, media):
        """
        :type media: Media
        """
        libvlc_media_player_set_media(self, media)

    def set_pause(self, do_pause):
        """
        :type do_pause: bool
        """
        libvlc_media_player_set_pause(self, int(do_pause))

    def set_position(self, pos):
        """
        :type pos: float
        """
        libvlc_media_player_set_position(self, ctypes.c_float(pos))

    def set_time(self, time_ms):
        """
        :type time_ms: int
        """
        libvlc_media_player_set_time(self, ctypes.c_int64(time_ms))

    def set_volume(self, volume):
        """
        :type volume: int
        """
        assert isinstance(volume, int)
        libvlc_audio_set_volume(self, volume)

    def stop(self):
        libvlc_media_player_stop(self)


if __name__ == '__main__':
    import sys
    v = Vlc('--no-video')
    m = Media(v, sys.argv[1])
    p = MediaPlayer(v)
    p.set_media(m)
    p.play()
    import time
    time.sleep(5)
    p.stop()
