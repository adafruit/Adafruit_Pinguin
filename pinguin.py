# Ugly test code, this tries generating an EAGLE .lbr file containing
# rasters for pin labels.
# At present, just generates one, but does appear to work.

from PIL import Image, ImageFont, ImageDraw
import xml.etree.ElementTree as ET
import os

FONT_SIZE = 64
PAD = 12
DPI = 1200
FONT_FILE = "fonts/FreeMonoBold.ttf"

STRINGS = ["GND", "5V"]


font = ImageFont.truetype(FONT_FILE, FONT_SIZE)

# Get bounding box of string
box = font.getbbox("GND", mode='', direction=None, features=None, language=None, stroke_width=0, anchor=None)

height = box[3] - box[1] + PAD * 2
radius = height // 2
width = box[2] - box[0] + radius * 2
# Create image and draw context
image = Image.new('1', (width, height), color=0)
draw = ImageDraw.Draw(image)

# Draw box or oval
draw.rounded_rectangle([(0, 0), (width - 1, height - 1)], radius=radius, fill=1, outline=None)

# Draw text into it
draw.text((radius - box[0], PAD - box[1]), "GND", font=font, color=0)

# Save as a 1-bit 1200 DPI BMP
image.save("out.bmp", dpi=(1200, 1200))

# pass in anchor X,Y
def rect(parent, x1, x2, y, ax=0, ay=0):
    scale = 25.4 / DPI
    x1 = (x1 - ax) * scale
    x2 = (x2 - ax) * scale
    y2 = (y + 1 - ay) * scale
    y = (y - ay) * scale
    child = ET.SubElement(parent, "rectangle", x1="%3.2f" % x1, y1="%3.2f" % -y, x2="%3.2f" % x2, y2="%3.2f" % -y2, layer="21")

eagle = ET.Element("eagle", version="6.00")
drawing = ET.SubElement(eagle, "drawing")
settings = ET.SubElement(drawing, "settings")
grid = ET.SubElement(drawing, "grid", distance="1", unitdist="mm",
                         unit="mm", style="lines", multiple="1", display="no",
                         altdistance="0.1", altunitdist="mm", altunit="mm")
layers = ET.SubElement(drawing, "layers")
layer = ET.SubElement(layers, "layer", number="21", name="tPlace", color="7",
                      fill="1", visible="yes", active="yes")
library = ET.SubElement(drawing, "library")

packages = ET.SubElement(library, "packages")
package = ET.SubElement(packages, "package", name="GND")

symbols = ET.SubElement(library, "symbols")
symbol = ET.SubElement(symbols, "symbol", name="GND")
text = ET.SubElement(symbol, "text", size="1.0", layer="94")
text.text = "GND"

devicesets = ET.SubElement(library, "devicesets")
deviceset = ET.SubElement(devicesets, "deviceset", name="GND")
gates = ET.SubElement(deviceset, "gates")
gate = ET.SubElement(gates, "gate", name="G$1", symbol="GND", x="0", y="0")
devices = ET.SubElement(deviceset, "devices")
device = ET.SubElement(devices, "device", name="", package="GND")

ax = 0
ay = height / 2
for y in range(height):
    # Figure out X spans
    pixstate = 0  # Presume 'off' pixels to start
    startx = 0
    for x in range(width):
        p = image.getpixel((x, y))
        if p != pixstate:
            pixstate = p
            if pixstate > 0:
                startx = x
            else:
                rect(package, startx, x, y, ax, ay)
    if pixstate > 0:
        rect(package, startx, width, y, ax, ay)

tree = ET.ElementTree(eagle)
# Unfortunately indent() is only avail in Python 3.9; we're on 3.7
#ET.indent(tree, space=" ")
tree.write("foo.lbr", encoding="utf-8", xml_declaration=True)
# So instead of indent(), reformat using command line tool...
os.system("xmllint --format - < foo.lbr > foo2.lbr")
