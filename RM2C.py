import struct
import time
import GeoWrite as GW
import F3D
import ColParse
import sys
import os
from pathlib import Path

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
		for l in self.map:
			if addr in l:
				q= l.rfind(" ")
				return l[q:-1]
		return addr
	def RME(self,num,rom):
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
	bhv=s.GetLabel(hex(TcH(arg[18:22]))[2:])
	PO=(id,x,y,z,rx,ry,rz,bparam,bhv,mask)
	A=script.GetArea()
	A.objects.append(PO)
	return start
	
def PlaceMario(rom,cmd,start,script):
	#A=script.GetArea()
	return start

def ConnectWarp(rom,cmd,start,script):
	A=script.GetArea()
	arg=cmd[2]
	W=(arg[0],arg[1],arg[2],arg[3],arg[4])
	A.warps.append(W)
	return start
	
def PaintingWarp(rom,cmd,start,script):
	pass
	
def InstantWarp(rom,cmd,start,script):
	pass
	
def SetMarioDefault(rom,cmd,start,script):
	#deal with later
	return start
	
def LoadCol(rom,cmd,start,script):
	arg=cmd[2]
	col=TcH(arg[2:6])
	A=script.GetArea()
	A.col=col
	return start
	
def LoadRoom(rom,cmd,start,script):
	pass
	
def SetDialog(rom,cmd,start,script):
	pass
	
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
scriptHeader='''
#include <ultra64.h>
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
	(geo,dls)=GW.GeoParse(rom,s.B2P(s.models[num][0]),s,s.models[num][0])
	#write geo layout file
	GW.GeoWrite(geo,name/'geo.inc.c')
	return dls

def WriteModel(rom,dls,s,name):
	x=0
	ModelData=[]
	while(x<len(dls)):
		#check for bad ptr
		st=dls[x][0]
		first=TcH(rom[st:st+4])
		c=rom[st]
		if first==0x01010101 or not F3D.DecodeFmt.get(c):
			return
		(dl,verts,textures,amb,diff,jumps)=F3D.DecodeDL(rom,dls[x],s)
		ModelData.append((dls[x],dl,verts,textures,amb,diff))
		for jump in jumps:
			if jump not in dls:
				dls.append(jump)
		x+=1
	F3D.ModelWrite(rom,ModelData,name/'model.inc.c')
	return dls

def WriteLevelScript(name,Lnum,s,area,Anum):
	f = open(name,'w')
	f.write(scriptHeader)
	f.write('#include "levels/%d/header.h\n"'%Lnum)
	f.write('level_%d_entry[] = {\n'%Lnum)
	#entry stuff
	f.write("INIT_LEVEL(),\nLOAD_MIO0(        /*seg*/ 0x08, _common0_mio0SegmentRomStart, _common0_mio0SegmentRomEnd),\nLOAD_RAW(         /*seg*/ 0x0F, _common0_geoSegmentRomStart,  _common0_geoSegmentRomEnd),\nALLOC_LEVEL_POOL(),\nMARIO(/*model*/ MODEL_MARIO, /*behParam*/ 0x00000001, /*beh*/ bhvMario),\nJUMP_LINK(script_func_global_1),\n")
	#a bearable amount of cringe
	for a in Anum:
		f.write('JUMP_LINK(local_area_%d),\n'%a)
	#end script
	f.write("FREE_LEVEL_POOL(),\nMARIO_POS(/*area*/ 1, /*yaw*/ 135, /*pos*/ -6558, 0, 6464),\nCALL(/*arg*/ 0, /*func*/ lvl_init_or_update),\nCALL_LOOP(/*arg*/ 1, /*func*/ lvl_init_or_update),\nCLEAR_LEVEL(),\nSLEEP_BEFORE_EXIT(/*frames*/ 1),\nEXIT(),\n};\n")
	for a in Anum:
		WriteArea(f,s,area,a)
	
def WriteArea(f,s,area,Anum):
	#begin area
	f.write("LevelScript local_area_%d[] = {\n"%Anum)
	Gptr='Geo_'+hex(area.geo)
	f.write("AREA(%d,%s),\n"%(Anum,Gptr))
	f.write("TERRAIN(%s),\n"%("col_"+hex(area.col)))
	f.write("SET_BACKGROUND_MUSIC(0,%d),\n"%area.music)
	f.write("TERRAIN_TYPE(%d),\n"%area.terrain)
	f.write("JUMP_LINK(local_objects_%d),\nJUMP_LINK(local_warps_%d),\n"%(Anum,Anum))
	f.write("END_AREA()\n};\n")
	
	f.write('LevelScript local_objects_%d[] = {\n'%Anum)
	#write objects
	for o in area.objects:
		f.write("OBJECT_WITH_ACTS({},{},{},{},{},{},{},{},{},{}),\n".format(*o))
	f.write("};\n")
	f.write('LevelScript local_warps_%d[] = {\n'%Anum)
	#write warps
	for w in area.warps:
		f.write("WARP_NODE({},{},{},{},{}),\n".format(*w))
	f.write("};\n")

def WriteLevel(rom,s,num,areas):
	#create level directory
	level=Path(sys.path[0])/("%d"%num)
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
		(geo,dls)=GW.GeoParse(rom,s.B2P(area.geo),s,area.geo)
		GW.GeoWrite(geo,adir/"geo.inc.c")
		for g in geo:
			s.MakeDec("GeoLayout Geo_%s[]"%hex(g[1]))
		dls = WriteModel(rom,dls,s,adir)
		for d in dls:
			s.MakeDec("Gfx DL_%s[]"%hex(d[1]))
		#write collision file
		ColParse.ColWrite(adir/"collision.inc.c",s,rom,area.col)
	#now write level script
	WriteLevelScript(level/"script.c",num,s,area,areas)
	#finally write header
	H=level/"header.h"
	q = open(H,'w')
	for h in s.header:
		q.write('extern '+h+';\n')


if __name__=='__main__':
	rom=open('baserom.z64','rb')
	rom = rom.read()
	#choose level
	s = Script(16)
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
	#now area class should have data
	#along with pointers to all models
	ass=Path("assets")
	ass=Path(sys.path[0])/ass
	ass.mkdir(exist_ok=True)
	#create subfolders for each model
	for i in range(0):
		#skip error for now until seg 2 detect
		if i==219:
			continue
		if s.models[i]:
			md = ass/("%d"%i)
			md.mkdir(exist_ok=True)
			print(i,"model")
			if s.models[i][1]=='geo':
				dls=WriteGeo(rom,s,i,md)
			else:
				dls=[[s.B2P(s.models[i][0]),s.models[i][0]]]
			WriteModel(rom,dls,s,md)
	
	#now do level
	WriteLevel(rom,s,16,[1])