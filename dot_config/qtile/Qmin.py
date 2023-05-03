import Qminconfig
from libqtile.command import lazy
from libqtile import hook
from fuzzywuzzy import fuzz, process
import configparser
import subprocess
import os
import tempfile
if not Qminconfig.show_ids:
    from collections import OrderedDict

# This is the zero-width joiner (U+200d), and it is an invisible character.
# It is used to encode information into strings without effecting the rofi prompt here.
ZWJ = "‍"


def check_validity_of_user_config():
    # Qminconfig could also have been a dictionary to avoid evaling, which is usually
    # a code smell, however I thought not to implement it that way as it could be
    # unintuitive, especially to newcomers to Python who just wanna use this script's
    # functionality and continue on with their day.

    def get_value(option):
        return eval(f"Qminconfig.{option}")

    config_options = {
        "show_ids": (True, False),
        "activate_on_unminimize": (True, False, "smart"),
    }

    for option, valids in config_options.items():
        for valid_value in valids:
            if get_value(option) is valid_value:
                break
        else:  # for-else denotes if for loop has not been broken by break
            print(f"Unrecognized option for Qminconfig.{option}: {get_value(option)}")
            raise ValueError

def get_window(qtile, id):
    return qtile.windows_map[id]

def query(qtile, id, property):
    return get_window(qtile, id).info()[property]


def get_window_ids(qtile):
    all_window_ids = qtile.items("window")[1][1:] # Disregard bar.
    window_ids = list()
    for id in all_window_ids:
        if query(qtile, id, "minimized"):
            window_ids.append(id)
    if not window_ids:
        print("No windows are minimized.")
        raise RuntimeError
    return window_ids


def get_wm_classes(qtile, window_ids):
    id_to_wm_class = dict()
    for id in window_ids:
        id_to_wm_class[id] = query(qtile, id, "wm_class")
    return id_to_wm_class


def get_all_icons():
    icons = list()
    config = configparser.ConfigParser(interpolation=None)
    for root, _, files in os.walk("/usr/share/applications"):
        for file in files:
            if not file.endswith(".desktop"):
                continue
            config.read(os.path.join(root, file))
            try:
                icon = config["Desktop Entry"]["Icon"]
            except KeyError:
                continue
            icons.append(icon)
    return icons


def get_id_to_icon(icons, id_to_wm_class):
    id_to_icon = dict()
    for id, wm_classes in id_to_wm_class.items():
        for wm_class in wm_classes:
            id_to_icon[id] = process.extractOne(wm_class, icons,
                                                scorer=fuzz.token_sort_ratio)[0]
            # Disregard match percentage that process.extractOne returns.
    return id_to_icon


def get_id_to_window_name(qtile, window_ids):
    if Qminconfig.show_ids:
        id_to_window_name = dict()
    else:
        # OrderedDict is necessary to ensure index can be used to retrieve id later.
        id_to_window_name = OrderedDict()
    for id in window_ids:
        window_name = query(qtile, id, "name")
        id_to_window_name[id] = window_name
    return id_to_window_name


def get_rofi_string(id_to_window_name, id_to_icon):
    rofi_string_list = list()
    if Qminconfig.show_ids:
        for id, window_name in id_to_window_name.items():	
            # Using zwj to differentiate from other windows that might have ' [' in their name.
            entry = f"{window_name} {ZWJ}[{id}]"
            rofi_string_list.append(f"  {entry}\\0icon\\x1f{id_to_icon[id]}")
    else:
        for index, (id, window_name) in enumerate(id_to_window_name.items()):
            # Using zwj to encode index information into rofi prompt so that the uniqueness 
            # is preserved and windows with the same name behave as expected.

            # Were this not to be done, if the user were to select a single window that shares its 
            # name with at least one other window, the window that would unminimize would always 
            # be the one with the bigger id, as that would have overwrote the other id during the 
            # initialization of id_to_window_name.
            entry = window_name + "".join([ZWJ * index])
            rofi_string_list.append(f"  {entry}\\0icon\\x1f{id_to_icon[id]}")
    return "\n".join(rofi_string_list)


def get_ids_to_unminimize(rofi_string, id_to_window_name):
    ids_to_unminimize = list()
    command = f"echo -en '{rofi_string}' | rofi -dmenu -multi-select -show-icons"

    # subprocess cannot handle null-bytes, which is necessary for rofi to accept icons,
    # thus we have to do our business externally.

    # We cannot use a context manager here, as the file is busy before the writing
    # closes the file pointer, and the tempfile gets destroyed as soon as fp.close()
    # is called. Thus, we use tempfile.mkstemp() instead, which is basically os.open() 
    # but in /tmp with a randomized name.

    fp, path = tempfile.mkstemp()

    # /bin/sh may point to /bin/dash on some systems, in which case this breaks,
    # so we have to invoke /bin/bash directly. I have no idea why this happens.

    shell_script = f"#!/bin/bash\n{command}"
    os.write(fp, bytes(shell_script, "utf-8"))
    os.system(f"chmod +x {path}")
    os.close(fp)
    try:
        result = subprocess.check_output(path).decode("utf-8")
    except subprocess.CalledProcessError:
        print("No windows selected to unminimize.")
        os.remove(path)
        raise RuntimeError

    for entry_name in result.rstrip("\n").split("\n"):
        if Qminconfig.show_ids:
            id_in_brackets = entry_name.split(f" {ZWJ}")[1]
            id = int(id_in_brackets.lstrip("[").rstrip("]"))
        else:
            _, *zwjs = entry_name.split(ZWJ)
            index = len(zwjs)
            id = list(id_to_window_name.keys())[index]
        ids_to_unminimize.append(id)
    return ids_to_unminimize

def focus_window(window):
    window.cmd_focus()
    hook.fire("focus_change")


def perform_unminimize(qtile, ids_to_unminimize):
    for id in ids_to_unminimize:
        window = get_window(qtile, id)
        window.toggle_minimize()
    if not Qminconfig.activate_on_unminimize:
        return
    elif Qminconfig.activate_on_unminimize is True: # guard against string being true
        focus_window(window)
    elif len(ids_to_unminimize) == 1:
        focus_window(window)


@lazy.function
def qmin(qtile):
    try:
        check_validity_of_user_config()
    except ValueError as e:
        return
    try:
        window_ids = get_window_ids(qtile)
    except RuntimeError:
        return
    id_to_wm_class = get_wm_classes(qtile, window_ids)
    icons = get_all_icons()
    id_to_icon = get_id_to_icon(icons, id_to_wm_class)
    id_to_window_name = get_id_to_window_name(qtile, window_ids)
    rofi_string = get_rofi_string(id_to_window_name, id_to_icon)
    try:
        ids_to_unminimize = get_ids_to_unminimize(rofi_string, id_to_window_name)
    except RuntimeError:
        return
    perform_unminimize(qtile, ids_to_unminimize)

