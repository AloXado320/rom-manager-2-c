# Rom Manger 2 C

Convert sm64 levels made with rom manager or SM64 Editor (not gauranteed to work with all versions) to sm64 decomp compliant C files.

Usage:
place rom in root, run RM2C.py with the following arguments:

RM2C.py, romname, editor (bool), levels (list, or 'all'), assets (list, or 'all')

Example input1 (all models in BoB plus BoB level model): python RM2C.py ASA.z64 True [9] range(0,255)

Example input2 (Export all Levels): python RM2C.py baserom.z64 True 'all' []

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