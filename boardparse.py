# Ugly test code. This reads an EAGLE .brd file and looks for text objects.
# Idea would be to rasterize these in a nicer font and place those either in
# an accompanying library file, or perhaps insert right in the .brd if
# possible.
# Coordinate with Limor to see if there's certain layers we could work from
# and to; e.g. probably don't want to modify existing top/bottom silk layers.
# But we might assign a certain layer to "texts on layer X get rasterized and
# output to layer Y (overwriting any there)", for both top & bottom.

import xml.etree.ElementTree as ET

tree = ET.parse("AHT20.brd")
root = tree.getroot()
texts = root.findall("drawing/board/plain/text")

for t in texts:
    # First 4 are required, rest are optional and have defaults if not present
    print(t.get("x"), t.get("y"), t.get("size"), t.get("layer"),
          t.get("font", "proportional"), t.get("ratio", "8"),
          t.get("rot", "R0"), t.get("align", "bottom-left"), t.text)

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
