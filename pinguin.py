# SPDX-FileCopyrightText: 2022 P Burgess for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Adafruit Pinguin -- an EAGLE silkscreen label generator for nicer fonts
with minimal intervention. Reads an EAGLE .brd file, looking for text
objects on specific layers, adds raster equivalents (in nicer fonts) on
different layers; include the latter with the normal silk output when
producing CAM files.

Forgive the mess, this is hastily-written muck and not Pythonic or
whatever, doesn't have error handling; like only three people will be
using it anyway.
"""

import argparse
import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageFont, ImageDraw

# GLOBAL CONFIGURABLES -----------------------------------------------------

TOP_IN = 21  #         Top labels input layer
BOTTOM_IN = 22  #      Bottom labels input layer
TOP_OUT = 170  #       Top silk output layer (will be added if not present)
BOTTOM_OUT = 171  #    Bottom silk output layer (")
TOP_BACKUP = 172  #    Top labels backup layer (")
BOTTOM_BACKUP = 173  # Bottom labels backup layer (")


label_num = 0  # Counter for labels, incremented as they're added to file

# CONFIGURE INPUT ----------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("filename", nargs="?", default="AHT20.brd")
parser.add_argument("-dpi", type=int, default=1200)
parser.add_argument("-vfont", type=str, default="fonts/GNU/FreeSans.ttf")
parser.add_argument("-pfont", type=str, default="fonts/Arimo/static/Arimo-Regular.ttf")
parser.add_argument("-ffont", type=str, default="fonts/GNU/FreeMono.ttf")
parser.add_argument("-vscale", type=float, default=4 / 3)
parser.add_argument("-pscale", type=float, default=2 ** 0.5)
parser.add_argument("-fscale", type=float, default=2 ** 0.5)
args = parser.parse_args()
infile = args.filename
path = os.path.split(args.filename)
idx = path[1].rfind(".brd")
if idx < 0:
    print("Input must be a .brd file")
    exit(0)
if len(path[0]):
    outfile = path[0] + "/" + path[1][:idx] + "_out.brd"
else:
    outfile = path[1][:idx] + "_out.brd"
font_spec = (
    (args.vfont, args.vscale),  # Font files and scale factors for
    (args.pfont, args.pscale),  # vector, proportional & fixed fonts.
    (args.ffont, args.fscale),
)  # DO NOT reorder list.
mm_to_px = args.dpi / 25.4  # For scaling text to pixel units
px_to_mm = 25.4 / args.dpi  # For scaling pixels back to document

# SOME FUNCTIONS TO DO SOME THINGS -----------------------------------------


def layer_find_add(parent, list, number, name, color, visible=True):
    """Search EAGLE tree for layer by number.
    If present, return it. If not, create new layer and return that.
    """
    num_str = str(number)
    for layer in list:
        if layer.get("number") == num_str:
            return layer  # Layer already present in file
    # Layer's not present in EAGLE file, add it
    return ET.SubElement(
        parent,
        "layer",
        number=num_str,
        name=name,
        color=str(color),
        fill="1",
        visible="yes" if visible else "no",
        active="yes",
    )


def rect(parent, layer, x1, x2, y, ax=0, ay=0):
    """Append a single-row rectangle to XML doc. Input units are pixels
    relative to anchor point (ax, ay), output is mm."""
    x1 = (x1 - ax) * px_to_mm
    x2 = (x2 - ax) * px_to_mm
    y2 = (y + 1 - ay) * px_to_mm
    y = (y - ay) * px_to_mm
    child = ET.SubElement(
        parent,
        "rectangle",
        x1="%3.2f" % x1,
        y1="%3.2f" % -y,
        x2="%3.2f" % x2,
        y2="%3.2f" % -y2,
        layer=layer,
    )


def rectify(parent, layer, image, anchor_x, anchor_y):
    """Convert a PIL image to a series of single-row rectangles."""
    for row in range(image.height):
        pixel_state = 0  # Presume 'off' pixels to start
        start_x = 0
        for column in range(image.width):
            pixel = image.getpixel((column, row))
            if pixel != pixel_state:
                pixel_state = pixel
                if pixel_state > 0:
                    start_x = column
                else:
                    rect(parent, layer, start_x, column, row, anchor_x, anchor_y)
        if pixel_state > 0:
            rect(parent, layer, start_x, image.width, row, anchor_x, anchor_y)


# Order of these lists is important, don't mess with (value returned by
# index() is used for subsequent operations).
align_list = [
    "bottom-left",
    "bottom-center",
    "bottom-right",
    "center-left",
    "center",
    "center-right",
    "top-left",
    "top-center",
    "top-right",
]
font_list = ["vector", "proportional", "fixed"]
font_align = ["left", "center", "right"]


# Need a small nonsense image for multiline text setup.
# Can't get multiline bounding box without a drawing context,
# but image for text isn't declared until bounding box is known!
ml_temp = Image.new("1", (1, 1), color=0)
ml_draw = ImageDraw.Draw(ml_temp)


def process_layer(
    in_texts, in_layer, out_elements, out_packages, out_layer, backup_layer
):
    """Process text elements in one layer of EAGLE file; convert fonts
    to raster library elements."""
    global label_num  # Icky, sorry
    in_str = str(in_layer)
    out_str = str(out_layer)
    backup_str = str(backup_layer)
    for text in in_texts:
        if text.get("layer") == in_str:
            # Found a text object on the input layer
            # Rasterize it and place in the library, add an
            # element to the .brd output layer referencing it.
            text_font = font_list.index(text.get("font", "proportional"))
            text_size = int(
                float(text.get("size")) * font_spec[text_font][1] * mm_to_px + 0.5
            )
            text_align = align_list.index(text.get("align", "bottom-left"))
            anchor_horiz = text_align % 3
            anchor_vert = text_align // 3
            font = ImageFont.truetype(font_spec[text_font][0], text_size)
            metrics = font.getmetrics()
            box = ml_draw.multiline_textbbox(
                (0, 0),
                text.text,
                font,
                anchor=None,
                align=font_align[anchor_horiz],
                direction=None,
                features=None,
                language=None,
                spacing=15,  # TO DO: figure out correct spacing
                stroke_width=0,
            )
            width = int(box[2] - box[0] + 1)
            height = int(box[3] - box[1] + 1)
            image = Image.new("1", (width, height), color=0)
            draw = ImageDraw.Draw(image)
            draw.multiline_text(
                (-box[0], -box[1]),
                text.text,
                font=font,
                align=font_align[anchor_horiz],
                spacing=15,  # TO DO: figure out correct spacing
                fill=1,
                features=None,
            )
            if anchor_horiz == 0:  # Left
                anchor_x = 0
            elif anchor_horiz == 1:  # Center
                anchor_x = width / 2
            else:  # Right
                anchor_x = width
            # TO DO: handle vertical anchor on multi-line text.
            extra_lines = text.text.count("\n")
            if anchor_vert == 0:  # Bottom
                anchor_y = metrics[0] - box[1]
                # Multiline kludge for now:
                anchor_y += (metrics[1] + metrics[0]) * extra_lines
            elif anchor_vert == 1:  # Center
                anchor_y = (metrics[0] - box[1]) * 0.5
                # Multiline kludge for now:
                anchor_y += (metrics[1] + metrics[0]) * extra_lines * 0.5
            else:  # Top
                anchor_y = 1
            # Add package in library
            name = "pLabel" + str(label_num)
            package = ET.SubElement(out_packages, "package", name=name)
            rectify(package, out_str, image, anchor_x, anchor_y)
            # Add element in .brd (referencing lbr package)
            rot = text.get("rot", "R0")
            if not "S" in rot:
                # If 'spin' isn't selected, can't handle angles >= 180
                table = {77: None, 82: None, 83: None}  # Strip M, R, S
                rot = ("MR" if "M" in rot else "R") + str(
                    float(rot.translate(table)) % 180
                )
            ET.SubElement(
                out_elements,
                "element",
                name=name,
                library="pinguin",
                package=name,
                x=text.get("x"),
                y=text.get("y"),
                smashed="yes",
                rot=rot,
            )
            label_num += 1
            text.set("layer", backup_str)  # Move from in_layer to backup_layer


# DO THE THING -------------------------------------------------------------

brd_tree = ET.parse(infile)
brd_root = brd_tree.getroot()
brd_layers = brd_root.findall("drawing/layers")[0]  # <layers> in .brd
layer_list = brd_layers.findall("layer")  #           List of <layer> elements

top_in = layer_find_add(brd_layers, layer_list, TOP_IN, "tPlace", 14)
top_out = layer_find_add(brd_layers, layer_list, TOP_OUT, "Pinguin_tPlace", 14)
top_backup = layer_find_add(
    brd_layers, layer_list, TOP_BACKUP, "Pinguin_tBackup", 14, False
)
bottom_in = layer_find_add(brd_layers, layer_list, BOTTOM_IN, "bPlace", 13)
bottom_out = layer_find_add(brd_layers, layer_list, BOTTOM_OUT, "Pinguin_bPlace", 13)
bottom_backup = layer_find_add(
    brd_layers, layer_list, BOTTOM_BACKUP, "Pinguin_bBackup", 13, False
)

# Sort .brd layers list so Pinguin-added items aren't at end in EAGLE menu
brd_layers[:] = sorted(brd_layers, key=lambda child: int(child.get("number")))

# Get list of text objects in the .brd file
brd_elements = brd_root.findall("drawing/board/elements")[0]  # <elements> in .brd
brd_plain = brd_root.findall("drawing/board/plain")[0]
brd_texts = brd_root.findall("drawing/board/plain/text")

# Check if pinguin library exists in the brd file
brd_library = None  # Assume it's not there to start
brd_libraries = brd_root.findall("drawing/board/libraries")[0]  # <libraries> in .brd
brd_library_list = brd_libraries.findall("library")  # List of <library> items
for lib in brd_library_list:  #         Iterate through list
    if lib.get("name") == "pinguin":  # If pinguin library,
        brd_library = lib  #            Found it!
if not brd_library:  # Not found, add pinguin library...
    brd_library = ET.SubElement(brd_libraries, "library", name="pinguin")
brd_packages = ET.SubElement(brd_library, "packages")

process_layer(brd_texts, TOP_IN, brd_elements, brd_packages, TOP_OUT, TOP_BACKUP)
process_layer(
    brd_texts, BOTTOM_IN, brd_elements, brd_packages, BOTTOM_OUT, BOTTOM_BACKUP
)

# WRITE RESULTS ------------------------------------------------------------

# ElementTree by default doesn't indent XML. There's an option in Python >= 3.9
# to do this, but it's not present in older versions (e.g. macOS at the moment).
# This is a "nice to have" during development & testing but is not crucial...so
# we try/except and just pass if it's a problem, no worries. xmllint, if
# available, can be invoked manually after the fact:
#     xmllint --format - <infile >outfile
try:
    ET.indent(brd_tree, space="  ")
except:
    pass
brd_tree.write(outfile, encoding="utf-8", xml_declaration=True)


# NOTES --------------------------------------------------------------------

# Stuff from eagle.dtd
# Default alignment (None) is lower left
# center alignment is centered on BOTH axes
# <!ENTITY % TextFont "(vector | proportional | fixed)">
# <!ENTITY % Align    "(bottom-left | bottom-center | bottom-right | center-left | center | center-right | top-left | top-center | top-right)">
# (is position of anchor relative to text)
# <!ATTLIST text
#           x             %Coord;        #REQUIRED
#           y             %Coord;        #REQUIRED
#           size          %Dimension;    #REQUIRED
#           layer         %Layer;        #REQUIRED
#           font          %TextFont;     "proportional"
#           ratio         %Int;          "8" <- stroke thickness
#           rot           %Rotation;     "R0" <- degrees
#           align         %Align;        "bottom-left"
#           distance      %Int;          "50" <- line distance
#           grouprefs     IDREFS         #IMPLIED
#           >
# Ratio is ignored on proportional font

# <!ATTLIST layer
#          number        %Layer;        #REQUIRED
#          name          %String;       #REQUIRED
#          color         %Int;          #REQUIRED
#          fill          %Int;          #REQUIRED
#          visible       %Bool;         "yes"
#          active        %Bool;         "yes"
#          >
