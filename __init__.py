"""
Highlight the specified animation channels across multiple objects by
toggling their visibility.
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
        "multiple objects by toggling their visibility.",
    "author": "Johnson Sun, Jenny Sun",
    "version": (0, 2, 0),
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
    ("Highlight X Location",       "X Location",       "Q"),
    ("Highlight Y Location",       "Y Location",       "W"),
    ("Highlight Z Location",       "Z Location",       "E"),
    ("Highlight X Euler Rotation", "X Euler Rotation", "A"),
    ("Highlight Y Euler Rotation", "Y Euler Rotation", "S"),
    ("Highlight Z Euler Rotation", "Z Euler Rotation", "D"),
    ("Highlight X Scale",          "X Scale",          "Z"),
    ("Highlight Y Scale",          "Y Scale",          "X"),
    ("Highlight Z Scale",          "Z Scale",          "C"),
    ("Clear Highlight",            "(Clear)",          "F"),
)

def highlight_channel(channel_name):
    def fc_match(fc, channel_name):
        """Check if the fcurve matches the channel name"""
        channel = CHANNELS[channel_name]
        return fc.data_path.endswith(channel[0]) and fc.array_index == channel[1] # endswith is required for bones
    fcurves = [
        fc
        for selected_object in bpy.context.selected_objects
        if selected_object.animation_data and (action := selected_object.animation_data.action)
        for fc in action.fcurves
    ]
    if channel_name == "(Clear)":
        # Case 1: Toggle highlight of all channels
        is_all_hidden = all(fc.hide for fc in fcurves)
        for fc in fcurves:
            fc.select = False
            fc.hide = not is_all_hidden
        return
    # Case 2: Toggle highlight of a specific channel
    is_some_targets_hidden = any(fc.hide and fc_match(fc, channel_name) for fc in fcurves)
    for fc in fcurves:
        if fc_match(fc, channel_name):
            fc.select = is_some_targets_hidden
            fc.hide = not is_some_targets_hidden

class HighlightOperator(bpy.types.Operator):
    bl_idname = "highlight_channels.highlight_channels"
    bl_label = "Highlight Channels"
    channel_name: bpy.props.StringProperty()

    def execute(self, context):
        highlight_channel(self.channel_name)
        return {"FINISHED"}

class HighlightMenu(bpy.types.Menu):
    bl_idname = "GRAPH_MT_highlight_channels"
    bl_label = "Highlight Channels"

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout
        for (text, channel_name, hotkey) in OPERATORS:
            op = layout.operator(
                HighlightOperator.bl_idname,
                text=text,
            )
            op.channel_name = channel_name

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
    for (text, channel_name, hotkey), (name, space_type) in \
        list(itertools.product(OPERATORS, name_and_space_types)):
        km = wm.keyconfigs.addon.keymaps.new(name=name, space_type=space_type)
        kmi = km.keymap_items.new(HighlightOperator.bl_idname, hotkey, "PRESS", alt=True)
        kmi.properties.channel_name = channel_name
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
