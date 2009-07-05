# Copyright (C) 2008-2009 Adam Olsen 
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import locale, gettext

# set the locale to LANG, or the user's default
locale.setlocale(locale.LC_ALL, '')

# this installs _ into python's global namespace, so we don't have to
# explicitly import it elsewhere
gettext.install("exaile")


from xl import settings
settings._SETTINGSMANAGER = \
        settings.SettingsManager('.testtemp/test_exaile_settings.ini')
import logging
from xl import collection, event, common, xdg
import unittest, hashlib, time, imp, os
import sys


event._TESTING = True
common._TESTING = True
class BaseTestCase(unittest.TestCase):
    def setUp(self):
        gettext.install("exaile")
        self.loading = False
        self.setup_logging()
        self.temp_col_loc = '.testtemp/col%s.db' % \
            hashlib.md5(str(time.time())).hexdigest()
        self.collection = collection.Collection("TestCollection", 
            self.temp_col_loc)

        self.library1 = collection.Library("./tests/data")
        self.collection.add_library(self.library1)
        self.collection.rescan_libraries()

    def load_plugin(self, pluginname):
        path = 'plugins/' + pluginname
        if path is None:
            return False
        sys.path.insert(0, path)
        plugin = imp.load_source(pluginname, os.path.join(path,'__init__.py'))
        del sys.path[0]
        return plugin

    def setup_logging(self):
        console_format = "%(levelname)-8s: %(message)s"
        loglevel = logging.INFO
        logging.basicConfig(level=logging.INFO,
                format='%(asctime)s %(levelname)-8s: %(message)s (%(name)s)',
                datefmt="%m-%d %H:%M",
                filename=os.path.join(xdg.get_config_dir(), "exaile.log"),
                filemode="a")
        console = logging.StreamHandler()
        console.setLevel(loglevel)
        formatter = logging.Formatter(console_format)
        console.setFormatter(formatter)       
