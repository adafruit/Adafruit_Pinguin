# Adafruit_Pinguin
An EAGLE silkscreen label generator written in Python (using PIL/Pillow)
allowing nicer fonts, because EAGLE's proportional font doesn't get output
in CAM data, and the new vector font isn't very attractive.

Ingests an EAGLE .brd file, looking for text elements on layers 20 and
21 (top, bottom) and produces raster equivalents on layers 170 and 171.
When producing CAM files, the raster output layers should then be included
along with the normal top and bottom silk layers. The original text elements
are moved to backup layers (172 and 173) if they need to be recovered later.
This is just for text; any other silk should go on the normal layers used
for such things, and are not rasterized by this tool.

Inspired a bit by SparkFun's "Buzzard" project, but wanting something more
automated.

Name is a cheesy portmanteau of "pin" (because that's mostly what's getting
labeled) and "penguin" (keeping with the bird naming motif; EAGLE, Buzzard,
etc.). I *detest* portmanteau software names but here we are.

"fonts" folder contains TrueType fonts: Google Arimo (EAGLE's proportional
font) and GNU FreeFont files as a starting point. THESE FONTS HAVE THEIR OWN
LICENSES INDEPENDENT FROM THE CODE, see notes in corresponding
subdirectories. If adding any font(s), CHECK for permissive license and
INCLUDE the license file; don't just add things wantonly! fonts.google.com
has some great-looking designs with a permissive license.

### Use

`python pinguin.py filename.brd`

Output will then go to `filename_out.brd`, where `filename` is taken from the
input file. File will be overwritten if present.

Any text labels in the tPlace (21) and bPlace (22) layers will be rasterized
into new layers Pinguin_tPlace (170) and Pinguin_bPlace (171). The original
text objects will be MOVED to the Pinguin_tBackup (172) and Pinguin_bBackup
(173) layers; these should NOT be part of the CAM output, but are kept in
case items need to be restored to the tPlace/bPlace layers for a do-over.

Optional args:

`-dpi N` Set output resolution (default = 1200)

`-vfont font.ttf` Override 'vector' font (default is GNU Free Sans)

`-pfont font.ttf` Override 'proportional' font (default is Arimo regular)

`-ffont font.ttf` Override 'fixed' font (default is GNU Free Mono)

`-vscale N` Change relative scale of 'vector' font (default = 1.33)

`-pscale N` Change relative scale of 'proportional' font (default = 1.41)

`-fscale N` Change relative scale of 'fixed' font (default = 1.41)

Rectangles in the tPlace (21) and bPlace (22) layers, when assigned a group
name matching an image filename in the `symbols` subdirectory, are replaced
by that bitmap (original rects are likewise preserved in 172/173). EAGLE
group names (and thus symbol filenames) MUST be all-caps, e.g. "DRAGON.PNG".


### To Do

- Multi-line text kinda works but spacing might need work.
- Would like a better match for vector font.
