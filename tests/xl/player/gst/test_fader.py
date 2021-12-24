from enum import Enum
from typing import List, NamedTuple, Tuple, Optional
from unittest.mock import patch

from gi.repository import GLib
import pytest

from xl.player.track_fader import TrackFader, FadeState

NoFade = FadeState.NoFade
FadingIn = FadeState.FadingIn
Normal = FadeState.Normal
FadingOut = FadeState.FadingOut


class FakeStream:
    def __init__(self):
        self.reset()

    def reset(self):
        self.position = 0
        self.volume = 42
        self.fadeout_begin = False
        self.stopped = False

    def get_position(self):
        return self.position

    def set_volume(self, value):
        self.volume = int(value * 100)

    def stop(self):
        self.stopped = True

    def on_fade_out(self):
        self.fadeout_begin = True


class FakeTrack:
    def __init__(self, start_off, stop_off, tracklen):
        self.tags = {
            '__startoffset': start_off,
            '__stopoffset': stop_off,
            '__length': tracklen,
        }

    def get_tag_raw(self, t):
        return self.tags[t]


class Tm(Enum):
    """The function queued by the last GLib.timeout_add call"""

    St = TrackFader._on_fade_start
    Ex = TrackFader._execute_fade


class TestData(NamedTuple):
    position: float
    volume: float
    state: FadeState
    timeout_func: Optional[Tm]
    action: Optional[str] = None
    args: Tuple = ()


# fmt: off
tests: List[List[TestData]] = [
    # Test don't manage the volume
    [
        TestData(0, 100, NoFade, None, 'play', (None, None, None, None)),
        TestData(1, 100, NoFade, None, 'pause'),
        TestData(2, 100, NoFade, None, 'unpause'),
        TestData(3, 100, NoFade, None, 'seek', (4,)),
        TestData(4, 100, NoFade, None, 'stop'),
        TestData(5, 100, NoFade, None),
    ],

    # Test fading in
    [
        TestData(0, 0,  FadingIn, Tm.Ex, 'play', (0, 2, None, None)),
        TestData(1, 50, FadingIn, Tm.Ex, 'execute'),
        TestData(3, 100, NoFade,  None,  'execute'),
        TestData(4, 100, NoFade,  None),
        TestData(5, 100, NoFade,  None,  'stop'),
        TestData(6, 100, NoFade,  None),
    ],

    # Test fading in: pause in middle
    [
        TestData(0, 0,  FadingIn, Tm.Ex, 'play', (0, 2, None, None)),
        TestData(1, 50, FadingIn, Tm.Ex, 'execute'),
        TestData(1, 50, FadingIn, None,  'pause'),
        TestData(1, 50, FadingIn, Tm.Ex, 'unpause'),
        TestData(1, 50, FadingIn, Tm.Ex, 'execute'),
        TestData(3, 100, NoFade,  None,  'execute'),
        TestData(4, 100, NoFade,  None),
        TestData(5, 100, NoFade,  None,  'stop'),
        TestData(6, 100, NoFade,  None),
    ],

    # Test fading in past the fade point
    [
        TestData(3, 100, NoFade, None, 'play', (0, 2, None, None)),
        TestData(4, 100, NoFade, None),
        TestData(5, 100, NoFade, None, 'stop'),
        TestData(6, 100, NoFade, None),
    ],

    # Test fading out
    [
        TestData(3, 100, Normal,    Tm.St, 'play', (None, None, 4, 6)),
        TestData(4, 100, FadingOut, Tm.Ex, 'start'),
        TestData(5, 50,  FadingOut, Tm.Ex, 'execute'),
        TestData(6, 0,   FadingOut, Tm.Ex, 'execute'),
        TestData(6.1, 0, NoFade,    None,  'execute'),
        TestData(7,   0, NoFade,    None),
    ],

    # Test all of them
    [
        TestData(0, 0,  FadingIn,   Tm.Ex, 'play', (0, 2, 4, 6)),
        TestData(1, 50, FadingIn,   Tm.Ex, 'execute'),
        TestData(3, 100, Normal,    Tm.St, 'execute'),
        TestData(4, 100, FadingOut, Tm.Ex, 'start'),
        TestData(5, 50,  FadingOut, Tm.Ex, 'execute'),
        TestData(6, 0,   FadingOut, Tm.Ex, 'execute'),
        TestData(6.1, 0, NoFade,    None,  'execute'),
        TestData(7,   0, NoFade,    None),
    ],

    # Test fading in with startoffset
    # [
    #     TestData(0, 0,   FadingIn, Tm.Ex, 'play', (60, 62, 64, 66)),
    #     TestData(0, 0,   FadingIn, Tm.Ex, 'seek', (60,)),
    #     TestData(61, 50, FadingIn, Tm.Ex, 'execute'),
    # ],
]
# fmt: on


@pytest.mark.parametrize('test', tests)
def test_fader(test: List[TestData]):

    # Test fade_out_on_play

    # Test setup_track

    # Test setup_track is_update=True

    # Test unexpected fading out

    check_fader(test)


def check_fader(test: List[TestData]):
    stream = FakeStream()
    fader = TrackFader(stream, stream.on_fade_out, 'test')

    timeout_args: Tuple = ()

    def glib_timeout_add(_interval, function, *args):
        import types

        nonlocal timeout_args
        timeout_args = args
        # If the function is a method, unbind it
        return function.__func__ if type(function) is types.MethodType else function

    def glib_source_remove(_src_id):
        pass

    with patch.multiple(
        GLib, timeout_add=glib_timeout_add, source_remove=glib_source_remove
    ):
        for data in test:
            print(data)
            stream.position = int(data.position * TrackFader.SECOND)
            print(stream.position)

            if data.action is not None:
                action = data.action
                args = data.args
                if action == 'start':
                    action = '_on_fade_start'
                elif action == 'execute':
                    action = '_execute_fade'
                    args = timeout_args
                    fader.now = data.position - 0.010

                # Call the function
                getattr(fader, action)(*args)

            # Our GLib.timeout_add mock above returns the timeout function (instead of a
            # numeric ID). This function then gets assigned to TrackFader.timer_id.
            assert fader.timer_id is data.timeout_func

            assert fader.state == data.state
            assert stream.volume == data.volume


def atest_calculate_fades():
    fader = TrackFader(None, None, None)

    # fin, fout, start_off, stop_off, tracklen;
    # start, start+fade, end-fade, end
    calcs = [
        # fmt: off

        # one is zero/none
        (0, 4, 0, 0, 10,        0, 0, 6, 10),
        (None, 4, 0, 0, 10,     0, 0, 6, 10),

        # other is zero/none
        (4, 0, 0, 0, 10,        0, 4, 10, 10),
        (4, None, 0, 0, 10,     0, 4, 10, 10),

        # both are equal
        (4, 4, 0, 0, 10,        0, 4, 6, 10),

        # both are none
        (0, 0, 0, 0, 10,        0, 0, 10, 10),
        (None, None, 0, 0, 10,  0, 0, 10, 10),

        # Bigger than playlen: all three cases
        (0, 4, 0, 0, 2,         0, 0, 0, 2),
        (4, 0, 0, 0, 2,         0, 2, 2, 2),
        (4, 4, 0, 0, 2,         0, 1, 1, 2),

        # With start offset
        (4, 4, 1, 0, 10,        1, 5, 6, 10),

        # With stop offset
        (4, 4, 0, 9, 10,        0, 4, 5, 9),

        # With both
        (2, 2, 1, 9, 10,        1, 3, 7, 9),

        # With both, constrained
        (4, 4, 4, 8, 10,        4, 6, 6, 8),
        (2, 4, 4, 7, 10,        4, 5, 5, 7),
        (4, 2, 4, 7, 10,        4, 6, 6, 7),
        # fmt: on
    ]

    i = 0
    for fin, fout, start, stop, tlen, t0, t1, t2, t3 in calcs:
        print(
            '%2d: Fade In: %s; Fade Out: %s; start: %s; stop: %s; Len: %s'
            % (i, fin, fout, start, stop, tlen)
        )
        track = FakeTrack(start, stop, tlen)
        assert fader.calculate_fades(track, fin, fout) == (t0, t1, t2, t3)
        i += 1
