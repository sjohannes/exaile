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

from xl.player.engine import ExaileEngine

from . import vlc


class VlcEngine(ExaileEngine):
    def initialize(self):
        self.vlc = vlc.Vlc(video=False)
        self.mplayer = vlc.MediaPlayer(self.vlc)
        self.track = None
        self.player.engine_load_volume()

    def destroy(self):
        del self.track
        self.mplayer.stop()
        del self.mplayer
        del self.vlc

    def get_current_track(self):
        return self.track

    def get_position(self):
        return self.mplayer.time * 1e9  # From s to ns

    def get_state(self):
        state = self.mplayer.state
        if state in (vlc.State.BUFFERING, vlc.State.OPENING, vlc.State.PLAYING):
            return b'playing'
        if state == vlc.State.PAUSED:
            return b'paused'
        if state in (vlc.State.ENDED, vlc.State.ERROR,
                vlc.State.NOTHING_SPECIAL, vlc.State.STOPPED):
            return b'stopped'
        assert False

    def get_volume(self):
        return self.mplayer.volume

    def on_track_stopoffset_changed(self, track):
        pass  # TODO

    def pause(self):
        self.mplayer.is_paused = True

    def play(self, track, start_at, paused):
        """
        :type track: xl.trax.Track|None
        :type start_at: float|None
        :type paused: bool
        """
        if not track:
            self.stop()
            return
        prior_track = self.track
        if prior_track:
            self.player.engine_notify_track_end(prior_track, False)
        self.track = track
        self.mplayer.media = vlc.Media(self.vlc, track.get_local_path())
        self.mplayer.play()
        if start_at:
            self.mplayer.time = start_at
        if paused:
            self.mplayer.toggle_pause()  # TODO: Doesn't work
        self.player.engine_notify_track_start(track)
        # TODO: Handle auto-advance

    def seek(self, value):
        self.mplayer.time = value

    def set_volume(self, volume):
        self.mplayer.volume = volume

    def stop(self):
        track = self.track
        self.mplayer.stop()
        self.track = None
        self.player.engine_notify_track_end(track, True)

    def unpause(self):
        self.mplayer.is_paused = False
