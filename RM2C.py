import struct
import time
import GeoWrite as GW
import F3D
import ColParse
import sys
import os
from pathlib import Path

#skip ending for now because script inf loops or something idk
#needs investigation
Num2Name = {
    4:"ccm",
    5:'bbh',
    6:'castle_inside',
    7:'hmc',
    8:'ssl',
    9:'bob',
    10:'sl',
    11:'wdw',
    12:'jrb',
    13:'thi',
    14:'ttc',
    15:'rr',
    16:"castle_grounds",
    17:'bitdw',
    18:'vcutm',
    19:'bitfs',
    20:'sa',
    21:'bits',
    22:'lll',
    23:'ddd',
    24:'wf',
    # 25:'ending',
    26:'castle_courtyard',
    27:'pss',
    28:'cotmc',
    29:'totwc',
    30:'bowser_1',
    31:'wmotr',
    33:'bowser_2',
    34:'bowser_3',
    36:'ttm'
}

scriptHeader='''#include <ultra64.h>
#include "sm64.h"
#include "behavior_data.h"
#include "model_ids.h"
#include "seq_ids.h"
#include "dialog_ids.h"
#include "segment_symbols.h"
#include "level_commands.h"
#include "game/level_update.h"
#include "levels/scripts.h"
#include "actors/common1.h"
#include "make_const_nonconst.h"

'''

geocHeader='''#include <ultra64.h>
#include "sm64.h"
#include "geo_commands.h"
#include "game/level_geo.h"
#include "game/geo_misc.h"
#include "game/camera.h"
#include "game/moving_texture.h"
#include "game/screen_transition.h"
#include "game/paintings.h"
#include "make_const_nonconst.h"

'''

ldHeader='''#include <ultra64.h>
#include "sm64.h"
#include "surface_terrains.h"
#include "moving_texture_macros.h"
#include "level_misc_macros.h"
#include "macro_preset_names.h"
#include "special_preset_names.h"
#include "textures.h"
#include "dialog_ids.h"

#include "make_const_nonconst.h"

'''

class Script():
	def __init__(self,level):
		self.map = open('sm64.us.map','r')
		self.map=self.map.readlines()
		self.banks=[None for a in range(32)]
		self.asm=[[0x80400000,0x1200000,0x1220000]]
		self.models=[None for a in range(256)]
		self.Currlevel=level
		self.levels={}
		#stack is simply a stack of ptrs
		#base is the prev pos
		#top is the current pos
		self.Base=None
		self.Stack=[]
		self.Top=-1
		self.CurrArea=None
		self.header=[]
	def B2P(self,B):
		Bank=B>>24
		offset=B&0xFFFFFF
		seg = self.banks[Bank]
		if not seg:
			print(hex(B),hex(Bank),self.banks[Bank-2:Bank+3])
		return seg[0]+offset
	def L4B(self,T):
		x=0
		for i,b in enumerate(T):
			x+=b<<(8*(3-i))
		return x
	def GetArea(self):
		try:
			return self.levels[self.Currlevel][self.CurrArea]
		except:
			return None
	def GetLabel(self,addr):
		#behavior is in bank 0 and won't be in map ever
		if len(addr)==6:
			return '0x'+addr
		for l in self.map:
			if addr in l:
				q= l.rfind(" ")
				return l[q:-1]
		return addr
	def RME(self,num,rom):
		if eval(sys.argv[2]):
			return
		start=self.B2P(0x19005f00)
		start=TcH(rom[start+num*16:start+num*16+4])
		end=TcH(rom[start+4+num*16:start+num*16+8])
		self.banks[0x0e]=[start,end]
	def MakeDec(self,name):
		self.header.append(name)

class Area():
		def __init__(self):
			pass
		
#tuple convert to hex
def TcH(bytes):
	a = struct.pack(">%dB"%len(bytes),*bytes)
	if len(bytes)==4:
		return struct.unpack(">L",a)[0]
	if len(bytes)==2:
		return struct.unpack(">H",a)[0]
	if len(bytes)==1:
		return struct.unpack(">B",a)[0]

def U2S(half):
	return struct.unpack(">h",struct.pack(">H",half))[0]

def LoadRawJumpPush(rom,cmd,start,script):
	arg=cmd[2]
	bank=arg[0:2]
	begin = arg[2:6]
	end = arg[6:10]
	jump = arg[10:14]
	script.banks[TcH(bank)]=[TcH(begin),TcH(end)]
	script.Stack.append(start)
	script.Top+=1
	script.Stack.append(script.Base)
	script.Top+=1
	script.Base=script.Top
	return script.B2P(TcH(jump))

def LoadRawJump(rom,cmd,start,script):
	arg=cmd[2]
	bank=arg[0:2]
	begin = arg[2:6]
	end = arg[6:10]
	jump = arg[10:14]
	script.banks[TcH(bank)]=[TcH(begin),TcH(end)]
	script.Top=script.Base
	return script.B2P(TcH(jump))

def Exit(rom,cmd,start,script):
	script.Top=script.Base
	script.Base=script.Stack[script.Top]
	script.Stack.pop()
	script.Top-=1
	start=script.Stack[script.Top]
	script.Stack.pop()
	script.Top-=1
	return start
	
def JumpRaw(rom,cmd,start,script):
	arg=cmd[2]
	return script.B2P(TcH(arg[2:6]))
	
def JumpPush(rom,cmd,start,script):
	script.Top+=1
	script.Stack.append(start)
	arg=cmd[2]
	return script.B2P(TcH(arg[2:6]))
	
def Pop(rom,cmd,start,script):
	start=script.Stack[script.Top]
	script.Top-=1
	script.Stack.pop()
	return start
	
def CondPop(rom,cmd,start,script):
	#this is where the script loops
	#Ill assume no custom shit is done
	#meaning this will always signal end of level
	return None

def CondJump(rom,cmd,start,script):
	arg=cmd[2]
	level=arg[2:6]
	jump=arg[6:10]
	if script.Currlevel==TcH(level):
		return script.B2P(TcH(jump))
	else:
		return start
	
def SetLevel(rom,cmd,start,script):
	#gonna ignore this and take user input instead
	#script.Currlevel=TcH(cmd[2])
	if not script.levels.get("Currlevel"):
		script.levels[script.Currlevel]=[None for a in range(8)]
	return start
	
def LoadAsm(rom,cmd,start,script):
	arg=cmd[2]
	ram=arg[2:6]
	begin=arg[6:10]
	end=arg[10:14]
	Q=[TcH(ram),TcH(begin),TcH(end)]
	if Q not in script.asm:
		script.asm.append(Q)
	return start

def LoadData(rom,cmd,start,script):
	arg=cmd[2]
	bank=arg[1:2]
	begin = arg[2:6]
	end = arg[6:10]
	script.banks[TcH(bank)]=[TcH(begin),TcH(end)]
	return start

def LoadMio0(rom,cmd,start,script):
	pass
	
def LoadMio0Tex(rom,cmd,start,script):
	return LoadData(rom,cmd,start,script)

def StartArea(rom,cmd,start,script):
	arg=cmd[2]
	area=arg[0]
	script.CurrArea=area
	q=Area()
	q.geo=TcH(arg[2:6])
	q.objects=[]
	q.warps=[]
	script.levels[script.Currlevel][script.CurrArea]=q
	return start
	
def EndArea(rom,cmd,start,script):
	script.CurrArea=None
	return start
	
def LoadPolyF3d(rom,cmd,start,script):
	arg=cmd[2]
	id=arg[1:2]
	layer=TcH(arg[0:1])>>4
	f3d=TcH(arg[2:6])
	script.models[TcH(id)]=(f3d,'f3d',layer)
	return start
	
def LoadPolyGeo(rom,cmd,start,script):
	arg=cmd[2]
	id=arg[1:2]
	geo=TcH(arg[2:6])
	script.models[TcH(id)]=(geo,'geo')
	return start
	
def PlaceObject(rom,cmd,start,script):
	arg=cmd[2]
	mask=arg[0]
	id=arg[1]
	#efficiency
	x=U2S(TcH(arg[2:4]))
	y=U2S(TcH(arg[4:6]))
	z=U2S(TcH(arg[6:8]))
	rx=U2S(TcH(arg[8:10]))
	ry=U2S(TcH(arg[10:12]))
	rz=U2S(TcH(arg[12:14]))
	bparam=hex(TcH(arg[14:18]))
	bhv=script.GetLabel(hex(TcH(arg[18:22]))[2:])
	#print(bhv)
	PO=(id,x,y,z,rx,ry,rz,bparam,bhv,mask)
	A=script.GetArea()
	A.objects.append(PO)
	return start
	
def PlaceMario(rom,cmd,start,script):
	#do nothing
	return start

def ConnectWarp(rom,cmd,start,script):
	A=script.GetArea()
	arg=cmd[2]
	W=(arg[0],arg[1],arg[2],arg[3],arg[4])
	A.warps.append(W)
	return start
	
def PaintingWarp(rom,cmd,start,script):
	return start
	
def InstantWarp(rom,cmd,start,script):
	return start
	
def SetMarioDefault(rom,cmd,start,script):
	arg=cmd[2]
	script.mStart = [arg[0],U2S(TcH(arg[2:4])),U2S(TcH(arg[4:6])),U2S(TcH(arg[6:8])),U2S(TcH(arg[8:10]))]
	return start
	
def LoadCol(rom,cmd,start,script):
	arg=cmd[2]
	col=TcH(arg[2:6])
	A=script.GetArea()
	A.col=col
	return start
	
def LoadRoom(rom,cmd,start,script):
	return start

def SetDialog(rom,cmd,start,script):
	return start

def SetMusic(rom,cmd,start,script):
	A=script.GetArea()
	if A:
		arg=cmd[2]
		A.music=TcH(arg[1:2])
	return start

def SetMusic2(rom,cmd,start,script):
	A=script.GetArea()
	if A:
		arg=cmd[2]
		A.music=TcH(arg[3:4])
	return start
			
def SetTerrain(rom,cmd,start,script):
	A=script.GetArea()
	if A:
		arg=cmd[2]
		A.terrain=TcH(arg[1:2])
	return start


def ULC(rom,start):
	cmd = struct.unpack(">B",rom[start:start+1])[0]
	len = struct.unpack(">B",rom[start+1:start+2])[0]
	q=len-2
	args = struct.unpack(">%dB"%q,rom[start+2:start+len])
	return [cmd,len,args]

#iterates through script until a cmd is found that
#requires new action, then returns that cmd
def PLC(rom,start):
	(cmd,len,args) = ULC(rom,start)
	start+=len
	if cmd in jumps:
		return (cmd,len,args,start)
	return PLC(rom,start)

def WriteGeo(rom,s,num,name):
	(geo,dls)=GW.GeoParse(rom,s.B2P(s.models[num][0]),s,s.models[num][0],"actor_"+str(num)+"_")
	#write geo layout file
	GW.GeoWrite(geo,name/'geo.inc.c',"actor_"+str(num)+"_")
	return dls

def WriteModel(rom,dls,s,name,Hname,id):
	x=0
	ModelData=[]
	while(x<len(dls)):
		#check for bad ptr
		st=dls[x][0]
		first=TcH(rom[st:st+4])
		c=rom[st]
		if first==0x01010101 or not F3D.DecodeFmt.get(c):
			return
		(dl,verts,textures,amb,diff,jumps)=F3D.DecodeDL(rom,dls[x],s,id)
		ModelData.append((dls[x],dl,verts,textures,amb,diff))
		for jump in jumps:
			if jump not in dls:
				dls.append(jump)
		x+=1
	refs = F3D.ModelWrite(rom,ModelData,name,id)
	modelH = name/'model.inc.h'
	mh = open(modelH,'w')
	headgaurd="%s_HEADER_H"%(Hname)
	mh.write('#ifndef %s\n#define %s\n#include "types.h"\n'%(headgaurd,headgaurd))
	for r in refs:
		mh.write('extern '+r+';\n')
	mh.write("#endif")
	mh.close()
	return dls

def WriteLevelScript(name,Lnum,s,area,Anum):
	f = open(name,'w')
	f.write(scriptHeader)
	f.write('#include "levels/%s/header.h"\n'%Lnum)
	f.write('LevelScript level_%s_entry[] = {\n'%Lnum)
	#entry stuff
	f.write("INIT_LEVEL(),\nLOAD_MIO0(        /*seg*/ 0x08, _common0_mio0SegmentRomStart, _common0_mio0SegmentRomEnd),\nLOAD_RAW(         /*seg*/ 0x0F, _common0_geoSegmentRomStart,  _common0_geoSegmentRomEnd),\nALLOC_LEVEL_POOL(),\nMARIO(/*model*/ MODEL_MARIO, /*behParam*/ 0x00000001, /*beh*/ bhvMario),\nJUMP_LINK(script_func_global_1),\n")
	#a bearable amount of cringe
	for a in Anum:
		f.write('JUMP_LINK(local_area_%d),\n'%a)
	#end script
	f.write("FREE_LEVEL_POOL(),\n")
	f.write("MARIO_POS({},{},{},{},{}),\n".format(*s.mStart))
	f.write("CALL(/*arg*/ 0, /*func*/ lvl_init_or_update),\nCALL_LOOP(/*arg*/ 1, /*func*/ lvl_init_or_update),\nCLEAR_LEVEL(),\nSLEEP_BEFORE_EXIT(/*frames*/ 1),\nEXIT(),\n};\n")
	for a in Anum:
		id = Lnum+"_"+str(a)+"_"
		WriteArea(f,s,area,a,id)
	
def WriteArea(f,s,area,Anum,id):
	#begin area
	ascript = "LevelScript local_area_%d[]"%Anum
	f.write(ascript+' = {\n')
	s.MakeDec(ascript)
	Gptr='Geo_'+id+hex(area.geo)
	f.write("AREA(%d,%s),\n"%(Anum,Gptr))
	f.write("TERRAIN(%s),\n"%("col_"+id+hex(area.col)))
	f.write("SET_BACKGROUND_MUSIC(0,%d),\n"%area.music)
	f.write("TERRAIN_TYPE(%d),\n"%(area.terrain))
	f.write("JUMP_LINK(local_objects_%d),\nJUMP_LINK(local_warps_%d),\n"%(Anum,Anum))
	f.write("END_AREA(),\nRETURN()\n};\n")
	asobj = 'LevelScript local_objects_%d[]'%Anum
	f.write(asobj+' = {\n')
	s.MakeDec(asobj)
	#write objects
	for o in area.objects:
		f.write("OBJECT_WITH_ACTS({},{},{},{},{},{},{},{},{},{}),\n".format(*o))
	f.write("RETURN()\n};\n")
	aswarps = 'LevelScript local_warps_%d[]'%Anum
	f.write(aswarps+' = {\n')
	s.MakeDec(aswarps)
	#write warps
	for w in area.warps:
		f.write("WARP_NODE({},{},{},{},{}),\n".format(*w))
	f.write("RETURN()\n};\n")

def GrabOGDatH(q,rootdir,name):
	dir = rootdir/'originals'/name
	head = open(dir/'header.h','r')
	head = head.readlines()
	for l in head:
		if not l.startswith('extern'):
			continue
		if 'Gfx %s'%name in l or 'GeoLayout %s'%name in l or 'LevelScript' in l or 'collision_level' in l or 'Movtex' in l:
			continue
		q.write(l)
	return q

def GrabOGDatld(L,rootdir,name):
	dir = rootdir/'originals'/name
	ld = open(dir/'leveldata.c','r')
	ld = ld.readlines()
	for l in ld:
		if not l.startswith('#include "levels/%s/'%name):
			continue
		if ('/areas/' in l and '/model.inc.c' in l) or ('/areas/' in l and '/collision.inc.c' in l) or '/movtext.inc.c' in l:
			continue
		L.write(l)
	return L

def WriteLevel(rom,s,num,areas,rootdir):
	#create level directory
	name=Num2Name[num]
	level=Path(sys.path[0])/("%s"%name)
	level.mkdir(exist_ok=True)
	Areasdir = level/"areas"
	Areasdir.mkdir(exist_ok=True)
	#create area directory for each area
	for a in areas:
		#area dir
		adir = Areasdir/("%d"%a)
		adir.mkdir(exist_ok=True)
		area=s.levels[num][a]
		#get real bank 0x0e location
		s.RME(a,rom)
		id = name+"_"+str(a)+"_"
		(geo,dls)=GW.GeoParse(rom,s.B2P(area.geo),s,area.geo,id)
		GW.GeoWrite(geo,adir/"geo.inc.c",id)
		for g in geo:
			s.MakeDec("GeoLayout Geo_%s[]"%(id+hex(g[1])))
		dls = WriteModel(rom,dls,s,adir,"%s_%d"%(name.upper(),a),id)
		for d in dls:
			s.MakeDec("Gfx DL_%s[]"%(id+hex(d[1])))
		#write collision file
		ColParse.ColWrite(adir/"collision.inc.c",s,rom,area.col,id)
		s.MakeDec('Collision col_%s[]'%(id+hex(area.col)))
	#now write level script
	WriteLevelScript(level/"script.c",name,s,area,areas)
	s.MakeDec("LevelScript level_%s_entry[]"%name)
	#finally write header
	H=level/"header.h"
	q = open(H,'w')
	headgaurd="%s_HEADER_H"%(name.upper())
	q.write('#ifndef %s\n#define %s\n#include "types.h"\n'%(headgaurd,headgaurd))
	for h in s.header:
		q.write('extern '+h+';\n')
	#now include externs from stuff in original level
	q = GrabOGDatH(q,rootdir,name)
	q.write("#endif")
	q.close()
	#write geo.c
	G = level/"geo.c"
	g = open(G,'w')
	g.write(geocHeader)
	g.write('#include "levels/%s/header.h"\n'%name)
	for i,a in enumerate(areas):
		g.write('#include "levels/%s/areas/%d/geo.inc.c"\n'%(name,(i+1)))
	g.close
	
	#write leveldata.c
	LD = level/"leveldata.c"
	ld = open(LD,'w')
	ld.write(ldHeader)
	for i,a in enumerate(areas):
		ld.write('#include "levels/%s/areas/%d/model.inc.c"\n'%(name,(i+1)))
		ld.write('#include "levels/%s/areas/%d/collision.inc.c"\n'%(name,(i+1)))
	ld = GrabOGDatld(ld,rootdir,name)
	ld.close

#dictionary of actions to take based on script cmds
jumps = {
    0:LoadRawJumpPush,
    1:LoadRawJump,
    2:Exit,
    5:JumpRaw,
    6:JumpPush,
    7:Pop,
    11:CondPop,
    12:CondJump,
    0x13:SetLevel,
    0x16:LoadAsm,
    0x17:LoadData,
    0x18:LoadMio0,
    0x1a:LoadMio0Tex,
    0x1f:StartArea,
    0x20:EndArea,
    0x21:LoadPolyF3d,
    0x22:LoadPolyGeo,
    0x24:PlaceObject,
    0x25:PlaceMario,
    0x26:ConnectWarp,
    0x27:PaintingWarp,
    0x28:InstantWarp,
    0x2b:SetMarioDefault,
    0x2e:LoadCol,
    0x2f:LoadRoom,
    0x30:SetDialog,
    0x31:SetTerrain,
    0x36:SetMusic,
    0x37:SetMusic2
}
def ExportLevel(rom,level,assets):
	#choose level
	s = Script(level)
	entry = 0x108A10
	#get all level data from script
	while(True):
		#parse script until reaching special
		q=PLC(rom,entry)
		#execute special cmd
		entry = jumps[q[0]](rom,q,q[3],s)
		#check for end, then loop
		if not entry:
			break
	#this tool isn't for exporting vanilla levels
	#so I skip ones that don't have bank 0x19 loaded
	#aka custom levels.
	if not s.banks[0x19]:
		return
	#now area class should have data
	#along with pointers to all models
	rootdir = Path(sys.path[0])
	ass=Path("assets")
	ass=Path(sys.path[0])/ass
	ass.mkdir(exist_ok=True)
	#create subfolders for each model
	for i in assets:
		#skip error for now until seg 2 detect
		if s.models[i]:
			md = ass/("%d"%i)
			md.mkdir(exist_ok=True)
			print(i,"model")
			if s.models[i][1]=='geo':
				dls=WriteGeo(rom,s,i,md)
			else:
				dls=[[s.B2P(s.models[i][0]),s.models[i][0]]]
			WriteModel(rom,dls,s,md,"MODEL_%d"%i,"actor_"+str(i)+"_")
	#now do level
	WriteLevel(rom,s,level,[1],rootdir)

if __name__=='__main__':
	HelpMsg="""
	#arguments for RM2C are as follows:
	#RM2C.py, romname, editor (bool), levels (list, or 'all'), assets (list, or 'all')
	All arguments must be listed for proper use. Use space to separate args.
	Because assets are level specific, please define a single level when
	exporting specific assets. Assets sharing a model ID will overwrite
	previous assets if multiple levels are selected.
	
	Example input1 (all models in BoB): python RM2C.py ASA.z64 True [9] range(0,255)
	Example input2 (Export all Levels): python RM2C.py baserom.z64 True 'all' []
	"""
	if len(sys.argv)!=5:
		print(HelpMsg)
		raise 'bad arguments'
	rom=open(sys.argv[1],'rb')
	rom = rom.read()
	args = (eval(sys.argv[3]),eval(sys.argv[4]))
	if args[0]=='all':
		for k in Num2Name.keys():
			if args[1]=='all':
				ExportLevel(rom,k,range(1,255,1))
			else:
				ExportLevel(rom,k,args[1])
			print(Num2Name[k] + ' done')
	else:
		for k in args[0]:
			if args[1]=='all':
				ExportLevel(rom,k,range(1,255,1))
			else:
				ExportLevel(rom,k,args[1])
			print(Num2Name[k] + ' done')
	print('Export Completed')