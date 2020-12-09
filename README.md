# Rom Manger 2 C

## Intro

Convert sm64 levels made with rom manager or SM64 Editor (not gauranteed to work with all versions) to sm64 decomp compliant C files.

------------------------------------------------------------------

## Dependencies

bistring, capstone, pypng, ESRGAN (only for ai upscaling for PC port *Currently Testing*)

### Installation

* pip install bitstring
* pip install capstone
* pip install pypng

#### ESRGAN
Currently testing, installation method coming after optimal fork and model are found.

------------------------------------------------------------------

## Usage

place rom in root, run RM2C.py with the following arguments:

RM2C.py, rom="romname", editor=False, levels=[] (or levels='all'), assets=[] (or assets='all'), Append=[(rom,areaoffset,editor),...]

Arguments with equals sign are shown in default state, do not put commas between args.
Levels and assets accept any list argument or only the string 'all'. Append is for when you want to combine multiple roms. The appended roms will be use the levels of the original rom, but use the areas of the appended rom with an offset.


### Example Inputs

1. All models in BoB for editor rom
	* python RM2C.py rom="ASA.z64" editor=True levels=[9] assets=range(0,255)


2. Export all Levels in a RM rom
	* python RM2C.py rom="baserom.z64" levels='all'

3. Export all BoB in a RM rom with a second area from another rom
	* python RM2C.py rom="baserom.z64" levels='all' Append=[('rom2.z64',1,True)]

### Expected results
Should extract all levels, scripts, and assets from the levels specified by arguments.

## Usage in Decomp
Drag and drop all levels folders into /sm64/levels directory of your decomp repo.
You must manage scripts of individual levels so that it matches with your current
repo, and may need to comment out certain objects.

Water boxes must currently be commented out of geometry layout

***NOT GUARANTEED TO COMPILE DIRECTLY AFTER EXTRACTION***

## Successful results
Ultra Mario Course 1 ported from sm64 editor to SM64EX pc port:

![UltraMarioPC.png](https://gitlab.com/scuttlebugraiser/rom-manger-2-c/-/raw/master/UltraMarioPC.png)

Speed Star Adventure Course 1 ported from Rom Manager to SM64 decomp:

![SSAEmu.png](https://gitlab.com/scuttlebugraiser/rom-manger-2-c/-/raw/master/SSAEmu.png)

------------------------------------------------------------------

## Curret issues

* Memory bloat because original data is still included due to not hardcoding which data can be excluded safely vs what cannot

* End cake picture does not work sometimes

* original levels do not work

* water boxes do not export

* custom objects do not export with labels (plan to have custom map support)

## Image Upscaling

With porting to PC automatically a possiblity, so is the addition of auto upscaling textures for higher quality gameplay. Using ESRGAN and various models I have tested what the best models are for AI upscaling.

![ESRGAN Comparison.png](https://gitlab.com/scuttlebugraiser/rom-manger-2-c/-/raw/master/Extra_Resources/ESRGAN_Comparison.png)