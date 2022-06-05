# Rom Manager 2 C

## Intro

Convert SM64 levels made with SM64 ROM Manager or SM64 Editor (not guaranteed to work with all versions) to SM64 decomp compliant C files.

### Model Importer

I have included a C to fast64 model importer with this repo. The file is called Import_Level.py. To use, open the scripting tab in blender, and link the file Import_Level.py and hit run. To import a level from RM2C, change the prefix to "custom." and the entry to "level_{}_custom_entry".
This importer currently only works with levels and does not perfectly match source content.

------------------------------------------------------------------

## Installation

### Repository

You must use my <a href="https://github.com/AloXado320/sm64ex-alo">sm64ex-alo</a> repository for RM2C and set RM2C in the makefile to 1</b>

### Dependencies

Install the following python3 dependencies using pip.

`pip install bitstring capstone pypng pillow pyhull`

### Originals folder

Create a new folder called `originals` in root.

Then on the `sm64ex-alo` repo, copy all the folders inside the `levels` folder and `sequences.json` inside `sound` over to the `originals` folder.

------------------------------------------------------------------

## Usage

Place ROM in root , run RM2C.py with the following arguments:

RM2C.py, rom="romname", editor=False, levels=[] , actors=[], Append=[(rom,areaoffset,editor),...] WaterOnly=0 ObjectOnly=0 MusicOnly=0 MusicExtend=0 Text=0 Misc=0 Textures=0 Inherit=0 Upscale=0 Title=0 Sound=0 Objects=0

 - Arguments with equals sign are shown in default state, do not put commas between args. All Arguments use python typing, this means you can generate lists or strings using defualt python functions.
 - Levels accept any list argument or only the string 'all'.
 - Actors will accept either a list of groups, a string for a group (see decomp group folders e.g. common0, group1 etc.) the string 'all' for all models, or the string 'new' for only models without a known label, or 'old' for only known original models.
 - Append is for when you want to combine multiple roms. The appended roms will act as if they are an extra area in the original rom, that is they will only export area specific data such as models, objects and music.
 - You must have at least one level to export actors because the script needs to read the model load cmds to find pointers to data.
 - The "Only" options are to only export certain things either to deal with specific updates or updates to RM2C itself. Only use one at a time. An only option will not maintain other data. Do not use Append with MusicOnly, it will have no effect.
 - Use ObjectOnly to export object hacks. If you are using a ToadsTool hack, set Misc=0 or it will hang.
 - MusicExtend is for when you want to add in your custom music on top of the original tracks. Set it to the amount you want to offset your tracks by (0x23 for vanilla). This is only useful when combined with append so the tracks don't overwrite each other.
 - Objects will export behaviors and object collision. Possible args are 'all' for all behaviors used, 'new' for ones without a known label, or you can pass a singular or list of regex matches e.g. ['[0-9]','koopa'].
 - Textures will export the equivalent of the /textures/ folder in decomp.
 - Inherit is a file management arg for when dealing with multiple roms. Normal behavior is to clear level and actor folder each time, inherit prevents this.
 - Title exports the title screen. This will also be exported if levels='all'
 - Sound will export instrument bank and sound sample data. It does not seem to work with custom samples well. (default is m64s only)
 - Upscale is an option to use ESRGAN ai upscaling to increase texture size. The upscaled textures will generate #ifdefs in each model file for non N64 targeting to compile them instead of the original textures. This feature is not currently implemented.

### Example Inputs


1. All models in BoB for editor rom
	* python RM2C.py rom="ASA.z64" editor=1 levels=[9] actors='all'

2. Export all Levels in a RM rom
	* python RM2C.py rom="baserom.z64" levels='all'

3. Export all BoB in a RM rom with a second area from another rom
	* python RM2C.py rom="baserom.z64" levels='all' Append=[('rom2.z64',1,True)]

4. Export text
	*python RM2C.py rom='sm74.z64' Text=1
	
4. Export title screen of one hack while keeping original data
	*python RM2C.py rom='SR1.z64' Title=1 Inerit=1


**NOTE: If you are on unix bash requires you to escape certain characters.
For this module, these are quotes and paranthesis. Add in a escape before each.**

* python3 RM2C.py rom=\'sm74.z64\' levels=[9] Append=[\(\'sm74EE.z64\',1,1\)] editor=1

### Expected results
Should extract all levels, scripts, and assets from the levels specified by arguments.

## Cleanup

After usage, folders that are generated can be deleted using `cleanup.bat` on Windows or `cleanup.sh` on Unix bash.

## Usage in Decomp
Drag and drop all exported folders into the root of your decomp repository.
You must manage scripts of individual levels so that custom objects/unknown objects
are properly commented or included in the repo. 

**NOTE:** Sequence numbers must be in numerical order.

***NOT GUARANTEED TO COMPILE DIRECTLY AFTER EXTRACTION***

### Necessary Manual Changes

1. Levels with fog made in editor need their setcombines changed.
	* Change the 2nd cycle value to "0, 0, 0, COMBINED, 0, 0, 0, COMBINED"
	* Import instructions will notify you of levels that have fog.

2. Appended roms may use different object banks which must be manually handled to prevent crashes.

3. Actors will need to be manually included to group files.

## Current issues

* Memory bloat because original data is still included.
