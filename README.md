# Adafruit_Pinguin
An EAGLE silkscreen label generator written in Python (using PIL/Pillow)
allowing nicer fonts, because EAGLE's proportional font doesn't get output
in CAM data, and the new vector font isn't very attractive.

Ingests am EAGLE .brd file, looking for text elements on layers 172 and
173 (top, bottom) and produces raster equivalents on layers 170 and 171.
When producing CAM files, the raster layers should be included with the top
and bottom silk, the former (input) layers should not. ANY other silk should
go on the normal layers used for such things! This is just for text.

Inspired a bit by SparkFun's "Buzzard" project, but wanting something more
automated.

Name is a cheesy portmanteau of "pin" (because that's mostly what's getting
labeled) and "penguin" (keeping with the bird naming motif; EAGLE, Buzzard,
etc.). I *detest* portmanteau software names but here we are.

"fonts" folder contains TrueType fonts: Google Arimo (EAGLE's proportional
font) and GNU FreeFont files as a starting point. THESE FONTS HAVE THEIR OWN
LICENSES INDEPENDENT FROM THE CODE, see notes in corresponding
subdirectories. If adding any font(s), CHECK for permissive license and
INCLUDE the license file; don't just add things wantonly!

### Use

`python pinguin.py filename.brd`

Output will go to `filename_out.brd` (file will be overwritten if present).

Contents of layers 170 and 171 (if any) will be overwritten. Please back up
board file first.

Optional args:

`-dpi N` Set output resolution (default = 1200)

`-vfont font.ttf` Override 'vector' font (default is GNU Free Sans)

`-pfont font.ttf` Override 'proportional' font (default is Arimo regular)

`-ffont font.ttf` Override 'fixed' font (default is GNU Free Mono)

`-vscale N` Change relative scale of 'vector' font (default = 1.33)

`-pscale N` Change relative scale of 'proportional' font (default = 1.41)

`-fscale N` Change relative scale of 'fixed' font (default = 1.41)

### To Do
- Multi-line text is not yet working.
- Would like a better match for the vector font.
- Maybe do the inverted text box idea.
