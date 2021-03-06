# -*- coding: utf-8 -*-
#
# Copyright (C) 2011,2012 Red Hat, Inc.
#
# Authors:
# Thomas Woerner <twoerner@redhat.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

import dbus
import pwd
import sys

PY2 = sys.version < '3'

def command_of_pid(pid):
    """ Get command for pid from /proc """
    try:
        with open("/proc/%d/cmdline" % pid, "r") as f:
            cmd = f.readlines()[0].replace('\0', " ").strip()
    except:
        return None
    return cmd

def pid_of_sender(bus, sender):
    """ Get pid from sender string using 
    org.freedesktop.DBus.GetConnectionUnixProcessID """

    dbus_obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    dbus_iface = dbus.Interface(dbus_obj, 'org.freedesktop.DBus')

    try:
        pid = int(dbus_iface.GetConnectionUnixProcessID(sender))
    except:
        return None
    return pid

def uid_of_sender(bus, sender):
    """ Get user id from sender string using 
    org.freedesktop.DBus.GetConnectionUnixUser """

    dbus_obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    dbus_iface = dbus.Interface(dbus_obj, 'org.freedesktop.DBus')

    try:
        uid = int(dbus_iface.GetConnectionUnixUser(sender))
    except:
        return None
    return uid

def user_of_uid(uid):
    """ Get user for uid from pwd """

    try:
        pws = pwd.getpwuid(uid)
    except Exception as msg:
        return None
    return pws[0]

def context_of_sender(bus, sender):
    """ Get SELinux context from sender string using 
    org.freedesktop.DBus.GetConnectionSELinuxSecurityContext """

    dbus_obj = bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    dbus_iface = dbus.Interface(dbus_obj, 'org.freedesktop.DBus')

    try:
        context =  dbus_iface.GetConnectionSELinuxSecurityContext(sender)
    except:
        return None

    return "".join(map(chr, dbus_to_python(context)))

def command_of_sender(bus, sender):
    """ Return command of D-Bus sender """

    return command_of_pid(pid_of_sender(bus, sender))

def user_of_sender(bus, sender):
    return user_of_uid(uid_of_sender(bus, sender))

def dbus_to_python(obj, expected_type=None):
    if obj is None:
        python_obj = obj
    elif isinstance(obj, dbus.Boolean):
        python_obj = bool(obj)
    elif isinstance(obj, dbus.String):
        python_obj = obj.encode('utf-8') if PY2 else str(obj)
    elif PY2 and isinstance(obj, dbus.UTF8String):  # Python3 has no UTF8String
        python_obj = str(obj)
    elif isinstance(obj, dbus.ObjectPath):
        python_obj = str(obj)
    elif isinstance(obj, dbus.Byte) or \
            isinstance(obj, dbus.Int16) or \
            isinstance(obj, dbus.Int32) or \
            isinstance(obj, dbus.Int64) or \
            isinstance(obj, dbus.UInt16) or \
            isinstance(obj, dbus.UInt32) or \
            isinstance(obj, dbus.UInt64):
        python_obj = int(obj)
    elif isinstance(obj, dbus.Double):
        python_obj = float(obj)
    elif isinstance(obj, dbus.Array):
        python_obj = [dbus_to_python(x) for x in obj]
    elif isinstance(obj, dbus.Struct):
        python_obj = tuple([dbus_to_python(x) for x in obj])
    elif isinstance(obj, dbus.Dictionary):
        python_obj = {dbus_to_python(k): dbus_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, bool) or \
         isinstance(obj, str) or isinstance(obj, bytes) or \
         isinstance(obj, int) or isinstance(obj, float) or \
         isinstance(obj, list) or isinstance(obj, tuple) or \
         isinstance(obj, dict):
        python_obj = obj
    else:
        raise TypeError("Unhandled %s" % obj)

    if expected_type is not None:
        if (expected_type == bool and not isinstance(python_obj, bool)) or \
           (expected_type == str and not isinstance(python_obj, str)) or \
           (expected_type == int and not isinstance(python_obj, int)) or \
           (expected_type == float and not isinstance(python_obj, float)) or \
           (expected_type == list and not isinstance(python_obj, list)) or \
           (expected_type == tuple and not isinstance(python_obj, tuple)) or \
           (expected_type == dict and not isinstance(python_obj, dict)):
            raise TypeError("%s is %s, expected %s" % (python_obj, type(python_obj), expected_type))

    return python_obj
