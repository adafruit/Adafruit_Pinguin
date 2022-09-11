# Ugly test code. This reads an EAGLE .brd file and looks for text objects.
# Rasterize these in a nicer font and place them on a different layer in
# the .brd file.

import os
import xml.etree.ElementTree as ET
from PIL import Image, ImageFont, ImageDraw

DPI = 1200
FONT_FILE = "Arimo/static/Arimo-Regular.ttf"
FONT_FEATURES=["-kern"]
FONT_FEATURES=None

# EAGLE layers we'll use for input and output
TOP_OUT = 170  #    Top silk output (will be added if not present)
BOTTOM_OUT = 171  # Bottom silk output (will be added if not present)
TOP_IN = 172  #     Top labels input
BOTTOM_IN = 173  #  Bottom labels input
# Additional layers might get added here for effects like inverted text
# in a box.


tree = ET.parse("AHT20.brd")
root = tree.getroot()
layers = root.findall("drawing/layers")[0]  # <layers> element in tree
layer_list = layers.findall("layer")  #       List of <layer> elements


def layer_find_add(parent, list, number, name, color):
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
        visible="yes",
        active="yes",
    )


top_out = layer_find_add(layers, layer_list, TOP_OUT, "Pinguin_tPlace", 14)
# delete any children of out layers, something like:
#for child in list(e):
#    e.remove(child)

bottom_out = layer_find_add(layers, layer_list, BOTTOM_OUT, "Pinguin_bPlace", 13)
top_in = layer_find_add(layers, layer_list, TOP_IN, "Pinguin_tIn", 10)
bottom_in = layer_find_add(layers, layer_list, BOTTOM_IN, "Pinguin_bIn", 1)



# <!ATTLIST layer
#          number        %Layer;        #REQUIRED
#          name          %String;       #REQUIRED
#          color         %Int;          #REQUIRED
#          fill          %Int;          #REQUIRED
#          visible       %Bool;         "yes"
#          active        %Bool;         "yes"
#          >

def rect(parent, x1, x2, y, ax=0, ay=0, xx=0, yy=0):
    scale = 25.4 / DPI
    x1 = (x1 - ax) * scale
    x2 = (x2 - ax) * scale
    y2 = (y + 1 - ay) * scale
    y = (y - ay) * scale
    child = ET.SubElement(parent, "rectangle", x1="%3.2f" % (xx + x1), y1="%3.2f" % (yy - y), x2="%3.2f" % (xx + x2), y2="%3.2f" % (yy - y2), layer=str(TOP_OUT))



def process(texts, in_layer, plain, out_layer):
    in_str = str(in_layer)
    out_str = str(out_layer)
    for t in texts:
        if t.get("layer") == in_str:
            # Found a text object on the input layer
            # Rasterize and place it in the output layer
            #font = ImageFont.truetype(FONT_FILE, int(float(t.get("size")) * 66.6))
            #font = ImageFont.truetype(FONT_FILE, 1 + int(float(t.get("size")) * 65))
            #font = ImageFont.truetype(FONT_FILE, int(float(t.get("size")) * 66 + 0.5))
            font = ImageFont.truetype(FONT_FILE, int(float(t.get("size")) * 66.6))
            metrics = font.getmetrics()
            box = font.getbbox(t.text, mode='', direction=None, features=FONT_FEATURES,
              language=None, stroke_width=0, anchor=None)
            width = box[2] - box[0] + 1
            height = box[3] - box[1] + 1
            image = Image.new('1', (width, height), color=0)
            draw = ImageDraw.Draw(image)
            draw.text((-box[0], -box[1]), t.text, font=font, fill=1, features=FONT_FEATURES)
            ax = width / 2  # TO DO: anchor alignment
            #ay = height / 2
            #ay = float(t.get("size")) * 24
            ay = (metrics[0] - metrics[1]) * 0.5
            xx = float(t.get("x"))
            yy = float(t.get("y"))
            for y in range(height):
                # Figure out X spans
                pixstate = 0  # Presume 'off' pixels to start
                startx = 0
                for x in range(width):
                    p = image.getpixel((x, y))
                    if p != pixstate:
                        pixstate = p
                        if p > 0:
                            startx = x
                        else:
                            rect(plain, startx, x, y, ax, ay, xx, yy)
                if pixstate > 0:
                    rect(plain, startx, width, y, ax, ay, xx, yy)



# TO DO: remove existing objects in the output layer
# parent.remove(child)

plain = root.findall("drawing/board/plain")[0]
#texts = root.findall("drawing/board/plain/text")
texts = plain.findall("text")
process(texts, TOP_IN, plain, TOP_OUT)
process(texts, BOTTOM_IN, plain, BOTTOM_OUT)

#    # First 4 are required, rest are optional and have defaults if not present
#    print(
#        t.get("x"),
#        t.get("y"),
#        t.get("size"),
#        t.get("layer"),
#        t.get("font", "proportional"),
#        t.get("ratio", "8"),
#        t.get("rot", "R0"),
#        t.get("align", "bottom-left"),
#        t.text,
#    )

# So...idea then...generate a library object for each label, then
# maybe modify the board file to reference individual items in lib.

# Default alignment (None) is lower left
# center alignment is centered on BOTH axes
# <!ENTITY % TextFont          "(vector | proportional | fixed)">
# <!ENTITY % Align             "(bottom-left | bottom-center | bottom-right | center-left | center | center-right | top-left | top-center | top-right)">
# (is position of anchor relative to text)
# <!ATTLIST text
#           x             %Coord;        #REQUIRED
#           y             %Coord;        #REQUIRED
#           size          %Dimension;    #REQUIRED
#           layer         %Layer;        #REQUIRED
#           font          %TextFont;     "proportional"
#           ratio         %Int;          "8" <- stroke thickness
#           rot           %Rotation;     "R0" <- degrees (not just 90 inc)
#           align         %Align;        "bottom-left"
#           distance      %Int;          "50" <- line distance
#           grouprefs     IDREFS         #IMPLIED
#           >
# Ratio is ignored on proportional font

# Idea: for rotated text, instead of trying to render an aligned bitmap
# with text at an angle, render a rotated bitmap with straight text.
# It'll all come out in the silk process anyway.
# In fact -- all text can be rendered that way, even the 90/180/270 stuff,
# no need for special handling. Just generate rect boxes with those angles,
# or maybe better, rotate the whole library part, easier.

# Sort layers list so Pinguin-added items aren't at end
layers[:] = sorted(layers, key=lambda child: int(child.get("number")))

# Unfortunately indent() is only avail in Python 3.9; we're on 3.7
# ET.indent(tree, space=" ")
tree.write("AHT20_out1.brd", encoding="utf-8", xml_declaration=True)
# So instead of indent(), reformat using command line tool...
os.system("xmllint --format - < AHT20_out1.brd > AHT20_out2.brd")
