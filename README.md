# Rom Manger 2 C

Convert sm64 levels made with rom manager or SM64 Editor (not gauranteed to work with all versions) to sm64 decomp compliant C files.

dependencies:

bistring, capstone, pypng.
installation:
pip install bitstring
pip install capstone
pip install pypng

Usage:
place rom in root, run RM2C.py with the following arguments:

RM2C.py, rom="romname", editor=False, levels=[] (or levels='all'), assets=[] (or assets='all')

Arguments with equals sign are shown in default state, do not put commas between args.
Levels and assets accept any list argument or only the string 'all'.

Example input1 (all models in BoB for editor rom):
python RM2C.py rom="ASA.z64" editor=True levels=[9] assets=range(0,255)

Example input2 (Export all Levels in a RM rom):
python RM2C.py rom="baserom.z64" levels='all'

Expected results:
Should extract all levels, scripts, and assets from the levels specified by arguments.

Successful results:
Ultra Mario Course 1 ported from sm64 editor to SM64EX pc port:

![UltraMarioPC.png](https://gitlab.com/scuttlebugraiser/rom-manger-2-c/-/raw/master/UltraMarioPC.png)

Speed Star Adventure Course 1 ported from Rom Manager to SM64 decomp:

![SSAEmu.png](https://gitlab.com/scuttlebugraiser/rom-manger-2-c/-/raw/master/SSAEmu.png)


Curret issues:

Memory bloat because original data is still included due to not hardcoding which data can be excluded safely vs what cannot
End cake picture does not work sometimes
original levels do not work
water boxes do not export
custom objects do not export with labels (plan to have custom map support)