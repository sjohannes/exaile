# dbushelper - Helper to make D-Bus handling more Pythonic
# Copyright (C) 2015-2016, 2018  Johannes Sasongko <sasongko@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# The developers of the Exaile media player hereby grant permission
# for non-GPL compatible GStreamer and Exaile plugins to be used and
# distributed together with GStreamer and Exaile. This permission is
# above and beyond the permissions granted by the GPL license by which
# Exaile is covered. If you modify this code, you may extend this
# exception to your version of the code, but you are not obligated to
# do so. If you do not wish to do so, delete this exception statement
# from your version.


from gi.repository import Gio, GLib

Variant = GLib.Variant


class ServiceHelper:
    """Helper to make D-Bus handling more Pythonic.

    The `obj` argument of the constructor must be an instance of a class
    implementing the service's methods and properties in the following form:

        class MyObject:
            def MyMethod(self, arg1, arg2):
                return 'out1', 'out2'
            @property
            def MyProperty(self):
                return 0
            @MyProperty.setter
            def MyProperty(self, value):
                pass

    You can then use ServiceHelper's `method_call`, `get_property`, and
    `set_property` methods as the closures (last three arguments) in the
    `Gio.DBusConnection.register_object` call.
    This helper acts as a bridge between the closure callbacks and the service
    object, translating D-Bus calls and values between them.

    All arguments passed into methods and properties are normal Python objects.
    All return values from methods and properties must be normal Python objects
    as well, except for objects with the `v` signature (which must be
    GLib.Variant objects).

    Note that while one object can implement multiple interfaces, this helper
    cannot correctly handle duplicate method/property names.
    """

    def __init__(self, obj, iinfos):
        """
        :param obj: The service object. See the class documentation.
        :param iinfos: InterfaceInfos implemented by the service object
        :type iinfos: Union[Gio.DBusInterfaceInfo, List[Gio.DBusInterfaceInfo]]
        """
        self.object = obj
        self.method_sigs = method_sigs = {}
        self.property_sigs = property_sigs = {}
        if isinstance(iinfos, Gio.DBusInterfaceInfo):
            iinfos = [iinfos]
        for iinfo in iinfos:
            for meth in iinfo.methods:
                method_sigs[meth.name] = (
                    '(' + ''.join(arg.signature for arg in meth.in_args) + ')',
                    '(' + ''.join(arg.signature for arg in meth.out_args) + ')',
                )
            for prop in iinfo.properties:
                property_sigs[prop.name] = prop.signature

    def method_call(
        self, connection, sender, path, interface, method, args, invocation
    ):
        try:
            insig, outsig = self.method_sigs[method]
        except KeyError:
            raise AttributeError("Invalid method %r" % method)
        args_sig = args.get_type_string()
        if args_sig != insig:
            raise ValueError(
                "Invalid method %r input signature: expected %r, actual %r"
                % (method, insig, args_sig)
            )
        result = getattr(self.object, method)(*args)
        if result is None:
            result = Variant(outsig, None)
        elif isinstance(result, tuple):
            result = Variant(outsig, result)
        else:
            result = Variant(outsig, (result,))
        invocation.return_value(result)

    def get_property(self, connection, sender, path, interface, prop):
        try:
            sig = self.property_sigs[prop]
        except KeyError:
            raise AttributeError("Invalid property %r" % prop)
        return Variant(sig, getattr(self.object, prop))

    def set_property(self, connection, sender, path, interface, prop, value):
        try:
            sig = self.property_sig[prop]
        except KeyError:
            raise AttributeError("Invalid property %r" % prop)
        value_sig = value.get_type_string()
        if value_sig != sig:
            raise ValueError(
                "Invalid property %r signature: expected %r, actual %r"
                % (prop, sig, value_sig)
            )
        setattr(self.object, prop, value.unpack())
        return True
