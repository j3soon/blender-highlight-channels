"""
Highlight the specified animation channels across multiple objects by
unselecting/hiding/locking all other channels.
"""

# This file is part of Blender Highlight Channels.
#
# Copyright (c) 2023 Johnson Sun
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

bl_info = {
    "name": "Highlight Channels",
    "description": "Highlight the specified animation channels across "
        "multiple objects by unselecting/hiding/locking all other channels.",
    "author": "Johnson Sun, Jenny Sun",
    "version": (0, 1, 0),
    "blender": (2, 80, 0), # Will not work in Blender 2.79 and earlier versions due to scripting API changes
    "location": "Graph Editor > Channel > Highlight Channels",
    "doc_url": "https://github.com/j3soon/blender-highlight-channels",
    "tracker_url": "https://github.com/j3soon/blender-highlight-channels/issues",
    "support": "COMMUNITY",
    "category": "Animation",
}

import itertools
import bpy

CHANNELS = {
    # channel_name: (data_path, array_index)
    "None":             ("", -1),
    "X Location":       ("location", 0),
    "Y Location":       ("location", 1),
    "Z Location":       ("location", 2),
    "X Euler Rotation": ("rotation_euler", 0),
    "Y Euler Rotation": ("rotation_euler", 1),
    "Z Euler Rotation": ("rotation_euler", 2),
    "X Scale":          ("scale", 0),
    "Y Scale":          ("scale", 1),
    "Z Scale":          ("scale", 2),
}

OPERATORS = (
    # (text, channel_name, hotkey)
    ("Clear Highlight",            "None",             "V"),
    ("Highlight X Location",       "X Location",       "Q"),
    ("Highlight Y Location",       "Y Location",       "W"),
    ("Highlight Z Location",       "Z Location",       "E"),
    ("Highlight X Euler Rotation", "X Euler Rotation", "A"),
    ("Highlight Y Euler Rotation", "Y Euler Rotation", "S"),
    ("Highlight Z Euler Rotation", "Z Euler Rotation", "D"),
    ("Highlight X Scale",          "X Scale",          "Z"),
    ("Highlight Y Scale",          "Y Scale",          "X"),
    ("Highlight Z Scale",          "Z Scale",          "C"),
)

def highlight_channel(channel_name, modifier):
    selected_objects = bpy.context.selected_objects
    for selected_object in selected_objects:
        action = selected_object.animation_data.action
        if not action:
            continue
        fcurves = action.fcurves
        for fc in fcurves:
            # Loop through all fcurves, select/lock/hide according to whether the channel name matches or not
            # Alternatively, loop through all groups and channels:
            # - for group in action.groups
            # - for channel in group.channels
            # - and then filter based on channel.data_path and channel.array_index
            channel = CHANNELS[channel_name]
            match = (fc.data_path.endswith(channel[0]) and (fc.array_index == channel[1])) # endswith is required for bones
            if channel_name == "None":
                fc.select = False
                fc.lock = fc.hide = modifier
                continue
            if modifier:
                if not match:
                    continue
                fc.select = not fc.select
                fc.lock = not fc.lock
                fc.hide = not fc.hide
            else:
                fc.select = match
                fc.lock = fc.hide = not match

class HighlightOperator(bpy.types.Operator):
    bl_idname = "highlight_channels.highlight_channels"
    bl_label = "Highlight Channels"
    channel_name: bpy.props.StringProperty()
    modifier: bpy.props.BoolProperty()

    def execute(self, context):
        highlight_channel(self.channel_name, self.modifier)
        return {"FINISHED"}

class HighlightMenu(bpy.types.Menu):
    bl_idname = "GRAPH_MT_highlight_channels"
    bl_label = "Highlight Channels"

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        for (text, channel_name, hotkey), modifier in \
            list(itertools.product(OPERATORS, [False, True])):
            op = layout.operator(
                HighlightOperator.bl_idname,
                text=text+(" (Extend)" if modifier else ""),
            )
            op.channel_name = channel_name
            op.modifier = modifier

def menu_func(self, context):
    layout: bpy.types.UILayout = self.layout
    layout.menu(HighlightMenu.bl_idname)

classes = (
    HighlightOperator,
    HighlightMenu,
)

# store keymaps here to access after registration
addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.GRAPH_MT_channel.append(menu_func)

    # handle the keymap
    wm = bpy.context.window_manager
    # Note that in background mode (no GUI available), keyconfigs are not available either,
    # so we have to check this to avoid nasty errors in background case.
    kc = wm.keyconfigs.addon
    if not kc:
        return
    # add custom hotkeys
    name_and_space_types = [
        ("Graph Editor Generic", "GRAPH_EDITOR"), # The entire graph editor
        # Below are necessary for Alt+A
        ("Animation Channels", "EMPTY"), # The right-hand side that displays all channels
        ("Graph Editor", "GRAPH_EDITOR"), # The middle section that displays the curves
    ]
    for (text, channel_name, hotkey), modifier, (name, space_type) in \
        list(itertools.product(OPERATORS, [False, True], name_and_space_types)):
        km = wm.keyconfigs.addon.keymaps.new(name=name, space_type=space_type)
        kmi = km.keymap_items.new(HighlightOperator.bl_idname, hotkey, "PRESS", shift=modifier, alt=True)
        kmi.properties.channel_name = channel_name
        kmi.properties.modifier = modifier
        addon_keymaps.append((km, kmi))

def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.GRAPH_MT_channel.remove(menu_func)

# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
