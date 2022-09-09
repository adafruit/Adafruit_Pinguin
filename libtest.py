# Ugly test code. This looks in a Buzzard-generated .lbr file for symbols.
# Idea would be to concatenate multiple single-raster .lbrs into one.
# Doesn't actually do that at present, just seeing what can be read.

import xml.etree.ElementTree as ET

tree = ET.parse("buzzard_labels.lbr")
root = tree.getroot()
library = root[0].findall("library")[0]
packages = library.findall("packages")[0]
for p in packages.findall("package"):
    print(p)
symbols = library.findall("symbols")[0]
for s in symbols.findall("symbol"):
    print(s)

tree.write("out.lbr")
