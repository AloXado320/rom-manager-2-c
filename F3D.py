import re
from bitstring import *
import math
import time
import struct

#typedef struct {
#  unsigned char	col[3];		/* diffuse light value (rgba) */
#  char 		pad1;
#  unsigned char	colc[3];	/* copy of diffuse light value (rgba) */
#  char 		pad2;
#  signed char	dir[3];		/* direction of light (normalized) */
#  char 		pad3;
#} Light_t;

#typedef struct {
#  unsigned char	col[3];		/* ambient light value (rgba) */
#  char 		pad1;
#  unsigned char	colc[3];	/* copy of ambient light value (rgba) */
#  char 		pad2;
#} Ambient_t;

def TcH(bytes):
	a = struct.pack(">%dB"%len(bytes),*bytes)
	if len(bytes)==4:
		return struct.unpack(">L",a)[0]
	if len(bytes)==2:
		return struct.unpack(">H",a)[0]
	if len(bytes)==1:
		return struct.unpack(">B",a)[0]

def ModelWrite(rom,ModelData,name):
	#start,dl,verts,textureptrs,ambient lights, diffuse lights
	dl=[]
	vbs=[]
	txt=[]
	ambs=[]
	diffs=[]
	f = open(name,'w')
	for md in ModelData:
		#display lists
		f.write('Gfx DL_'+hex(md[0][1])+'[] = {')
		f.write('\n')
		for c in md[1]:
			f.write(c+',\n')
		f.write('};\n\n')
		#verts
		for vb in md[2]:
			if vb in vbs:
				continue
			vbs.append(vb)
			f.write('Vtx VB_%s[] = {\n'%hex(vb[0]))
			for i in range(vb[2]):
				V=rom[vb[1]+i*16:vb[1]+i*16+16]
				V=BitArray(V)
				q=V.unpack('3*int:16,uint:16,2*int:16,4*uint:8')
				#feel there should be a better way to do this
				pos=q[0:3]
				UV=q[4:6]
				rgba=q[6:10]
				V="{{{ %d, %d, %d }, 0, { %d, %d }, { %d, %d, %d, %d}}},"%(*pos,*UV,*rgba)
				f.write(V+'\n')
			f.write('};\n\n')
		#textures
		for t in md[3]:
			if t in txt:
				continue
			txt.append(t)
			f.write('u16 texture_%s[] = {\n'%hex(t[1]))
			for i in range(t[2]):
				h=rom[t[0]+i*2:t[0]+i*2+2]
				f.write("0x{:02X},".format(int(h.hex(),16)))
				if i%16==15:
					f.write('\n')
			f.write('};\n\n')
		#lights
		for a in md[5]:
			if a in diffs:
				continue
			diffs.append(a)
			f.write('Light_t Light_%s = {\n'%hex(a[1]))
			Amb=rom[a[0]:a[0]+16]
			col1=Amb[0:3]
			col2=Amb[4:7]
			dir1=Amb[8:11]
			f.write("{{ %d, %d, %d}, 0, { %d, %d, %d}, 0, { %d, %d, %d}, 0}\n};\n\n"%(*col1,*col2,*dir1))
		for a in md[4]:
			if a in ambs:
				continue
			ambs.append(a)
			f.write('Ambient_t Light_%s = {\n'%hex(a[1]))
			Amb=rom[a[0]:a[0]+8]
			col1=Amb[0:3]
			col2=Amb[4:7]
			f.write("{{%d, %d, %d}, 0, {%d, %d, %d}, 0}\n};\n\n"%(*col1,*col2))
	f.close()
		
#f3d binary start
#takes bin, and returns tuple with C macro

class F3D_decode():
	def __init__(self,cmd):
		self.fmt=DecodeFmt[cmd][0]
		self.func=DecodeFmt[cmd][1]
	def decode(self,cmd,*args):
		return [self.fmt,*args]

#give cmd as binary.
#should return cmd as string, and args as tuple
def Bin2C(cmd):
	cmd = BitArray(cmd)
	c = F3D_decode(cmd[0:8].uint)
	V= c.func(cmd[8:])
	q = c.decode(c.fmt,V)
	ags = repr(q[1])
	ags=ags.replace("'","")
	#hardcoded cringe thanks gbi
	if cmd[:8].uint==6:
		ags.replace(',','')
		if cmd[8:16].uint!=1:
			q[0]='gsSPBranchList'
	return (q[0]+ags,cmd)

def DecodeDL(rom,start,s):
	dl=[]
	#needs (ptr,length)
	verts=[]
	#needs (ptr,length)
	textureptrs=[]
	#needs ptr
	amb=[]
	#neess ptr
	diffuse=[]
	#jump dls
	jumps=[]
	x=0
	#print(hex(start[0]),hex(start[1]))
	start=start[0]
	#print(rom[start:start+8].hex())
	while(True):
		cmd=rom[start+x:start+x+8]
		cmd=Bin2C(cmd)
		#g dl
		if (cmd[1][:8].uint==6):
			ptr=cmd[1][32:64].uint
			x+=8
			jumps.append([s.B2P(ptr),ptr])
			if cmd[1][8:16].uint==1:
				break
		#end dl
		elif (cmd[1][:8].uint==0xb8):
			break
		else:
			x+=8
			dl.append(cmd[0])
		#adding stuff to data arrays
		if (cmd[1][:8].uint==0x4):
			ptr=cmd[1][32:64]
			length=cmd[1][8:12]
			Rptr=s.B2P(ptr.uint)
			verts.append((ptr.uint,Rptr,length.uint+1))
		elif(cmd[1][:8].uint==0xfd):
			ptr=cmd[1][32:64]
			bpp=4*2**(cmd[1][11:13].uint)
			textureptrs.append([s.B2P(ptr.uint),ptr.uint,bpp])
		elif (cmd[1][:8].uint==0xf3):
			if textureptrs:
				texels=cmd[1][40:52]
				bpp=textureptrs[-1][2]
				textureptrs[-1][2]=((texels.uint+1)*bpp)//16
		elif (cmd[1][:8].uint==3):
			ptr=cmd[1][32:64]
			if cmd[1][8:16].uint==0x88:
				#ambient
				amb.append([s.B2P(ptr.uint),ptr.uint])
			else:
				#diffuse
				diffuse.append([s.B2P(ptr.uint),ptr.uint])
	return (dl,verts,textureptrs,amb,diffuse,jumps)

#take argument bits and make tuple of args

def G_SNOOP_Decode(bin):
	return ()

def G_VTX_Decode(bin):
	num,start,len,segment=bin.unpack('uint:4,uint:4,uint:16,uint:32')
	return ('VB_%s'%hex(segment),num+1,start)

def G_TRI1_Decode(bin):
	pad,v1,v2,v3=bin.unpack('int:32,3*uint:8')
	return (int(v1/10),int(v2/10),int(v3/10),0)

def G_TEXTURE_Decode(bin):
	pad,mip,tile,state,Sscale,Tscale=bin.unpack('int:10,2*uint:3,uint:8,2*uint:16')
	return (Sscale,Tscale,mip,tile,state)

def G_POPMTX_Decode(bin):
	pad,num=bin.unpack('int:24,uint:32')
	return (int(num/64),)

def G_CLEARGEOMETRYMODE_Decode(bin):
	pad,set=bin.unpack('uint:24,uint:32')
	return (0,set)

def G_SETGEOMETRYMODE_Decode(bin):
	pad,set=bin.unpack('uint:24,uint:32')
	return (set,0)

def G_MTX_Decode(bin):
	pad,param,seg=bin.unpack('int:16,uint:8,uint:32')
	return (param,seg)

def G_MOVEWORD_Decode(bin):
	index,offset,value=bin.unpack('uint:8,uint:16,uint:32')
	indices={0:'G_MW_MATRIX',
	2:'G_MW_NUMLIGHT',
	4:'G_MW_CLIP',
	6:'G_MW_SEGMENT',
	8:'G_MW_FOG',
	10:'G_MV_LIGHTCOL',
	12:'G_MW_FORCEMTX',
	14:'G_MW_PERSPNORM'}
	try:
		index=indices[index]
	except:
		pass
	return (index,offset,value)
	
def G_MOVEMEM_Decode(bin):
	index,size,seg=bin.unpack('uint:8,uint:16,uint:32')
	fuckgbi=1
	if index==0x88:
		fuckgbi=2
	return ('Light_%s'%hex(seg),fuckgbi)

def G_LOAD_UCODE_Decode(bin):
	#idk yet
	return (data,size,text)
	
def G_DL_Decode(bin):
	store,pad,seg=bin.unpack('uint:8,int:16,uint:32')
	return (seg,)

def G_ENDDL_Decode(bin):
	return ()

def G_RDPHALF_1_Decode(bin):
	pad,bits=bin.unpack('int:24,uint:32')
	return (bits,)

def G_SETOTHERMODE_L_Decode(bin):
	pad,shift,bits,value=bin.unpack('3*uint:8,uint:32')
	return (0xb9,shift,bits,value)

def G_SETOTHERMODE_H_Decode(bin):
	pad,shift,bits,value=bin.unpack('3*uint:8,uint:32')
	return (0xba,shift,bits,value)

def G_TEXRECT_Decode(bin):
	Xstart,Ystart,pad,tile,Xend,Yend,pad1,Sstart,Tstart,pad2,dsdx,dtdy=bin.unpack('2*uint:12,2*int:4,2*uint:12,uint:32,2*uint:16,uint:32,2*uint:16')
	return (Xstart,Ystart,tile,Xend,Yend,Sstart,Tstart,dsdx,dtdy)

def G_SETKEYGB_Decode(bin):
	Gwidth,Bwidth,Gint,Grecip,Bint,Brecip=bin.unpack('2*uint:12,4*uint:8')
	return (Gwidth,Bwidth,Gint,Grecip,Bint,Brecip)

def G_SETKEYR_Decode(bin):
	pad,Rwidth,Rint,Rrecip=bin.unpack('int:28,uint:12,2*uint:8')
	return (Rwidth,Rint,Rrecip)

def G_SETCONVERT_Decode(bin):
	p,k0,k1,k2,k3,k4,k5=bin.unpack('int:2,6*int:9')
	return (k0,k1,k2,k3,k4,k5)
	
def G_SETSCISSOR_Decode(bin):
	Xstart,Ystart,pad,mode,Xend,Yend=bin.unpack('2*uint:12,2*uint:4,2*uint:12')
	try:
		modes={0:'G_SC_NON_INTERLACE',
		2:'G_SC_EVEN_INTERLACE',
		3:'G_SC_ODD_INTERLACE'}
		mode=modes[mode]
	except:
		mode='invalid mode'
	return (Xstart,Ystart,mode,Xend,Yend)

def G_SETPRIMDEPTH_Decode(bin):
	pad,zval,depth=bin.unpack('int:24,2*uint:16')
	return (zval,depth)

def G_RDPSETOTHERMODE_Decode(bin):
	hi,lo=bin.unpack('uint:24,uint:32')
	return (hi,lo)

def G_LOADTLUT_Decode(bin):
	pad,tile,color,pad1=bin.unpack('int:28,uint:4,2*uint:12')
	return (tile,(((color>>2)&0x3ff)+1))
	
def G_RDPHALF_2_Decode(bin):
	pad,bits=bin.unpack('int:24,uint:32')
	return (bits,)
	
def G_SETTILESIZE_Decode(bin):
	Sstart,Tstart,pad,tile,width,height=bin.unpack('2*uint:12,2*uint:4,2*uint:12')
	return (tile,Sstart,Tstart,width,height)

def G_LOADBLOCK_Decode(bin):
	Sstart,Tstart,pad,tile,texels,dxt=bin.unpack('2*uint:12,2*uint:4,2*uint:12')
	return (tile,Sstart,Tstart,texels,dxt)

def G_LOADTILE_Decode(bin):
	Sstart,Tstart,pad,tile,Send,Tend=bin.unpack('2*uint:12,2*uint:4,2*uint:12')
	return (tile,Sstart,Tstart,Send,Tend)

def G_SETTILE_Decode(bin):
	fmt,bitsize,pad,numrows,offset,pad1,tile,palette,Tflag,Tmask,Tshift,Sflag,Smask,Sshift=bin.unpack('uint:3,uint:2,int:1,2*uint:9,int:5,uint:3,uint:4,uint:2,2*uint:4,uint:2,2*uint:4')
	return (fmt,bitsize,numrows,offset,tile,palette,Tflag,Tmask,Tshift,Sflag,Smask,Sshift)

def G_FILLRECT_Decode(bin):
	Xstart,Ystart,pad,Xend,Yend=bin.unpack('2*uint:12,uint:8,2*uint:12')
	return (Xstart,Ystart,Xend,Yend)

#fog,env,blend,fill
def G_COLOR_Decode(bin):
	pad,r,g,b,a=bin.unpack('int:24,4*uint:8')
	return (r,g,b,a)

def G_SETPRIMCOLOR_Decode(bin):
	pad,min,fraction,r,g,b,a=bin.unpack('7*uint:8')
	return (min/256,fraction/256,r,g,b,a)

def G_SETCOMBINE_Decode(bin):
	a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p=bin.unpack('uint:4,uint:5,2*uint:3,uint:4,uint:5,2*uint:4,8*uint:3')
	Basic={
	1:'Texel 0',
	2:'Texel 1',
	3:'Primitive',
	4:'Shade',
	5:'Environment'
	}
	One={
	6:1
	}
	Combined={
	0:'Combined'
	}
	CombinedA={
	0:'Combined'
	}
	C={
	6:'Key: Scale',
	7:'Combined Alpha',
	8:'Texel0 Alpha',
	9:'Texel1 Alpha',
	10:'Primitive Alpha',
	11:'Shade Alpha',
	12:'Environment Alpha',
	13:'LOD fraction',
	14:'Primitive LOD fraction',
	15:'Convert K5'
	}
	Noise={
	7:'Noise'
	}
	Key={
	6:'Key: Center',
	7:'Key: 4'
	}
	BasicA={
	1:'Texel 0',
	2:'Texel 1',
	3:'Primitive',
	4:'Shade',
	5:'Environment'
	}
	LoD={
	0:'LoD Fraction'
	}
	#a color = basic+one+combined+7as noise
	#b color = basic+combined+6 as key center+7 as key4
	#c color = basic+combined+C
	#d color = basic+combined+one
	
	#a alpha = basicA+one+combined
	#b alpha = a alpha
	#c alpha = basic+one+0 asLoD fraction
	#d alpha = a alpha
	#zero will be default, aka out of range
	ACmode = {**Basic,**Noise,**Combined,**One}
	BCmode = {**Basic,**Key,**Combined}
	CCmode = {**Basic,**C,**Combined}
	DCmode = {**Basic,**One,**Combined}

	AAmode = {**BasicA,**CombinedA,**One}
	BAmode = {**BasicA,**One,**CombinedA}
	CAmode = {**BasicA,**LoD}
	DAmode = {**BasicA,**One,**CombinedA}

	Acolor = (a,e)
	Bcolor = (g,h)
	Ccolor = (b,f)
	Dcolor = (k,n)

	Aalpha = (c,i)
	Balpha = (l,o)
	Calpha = (d,j)
	Dalpha = (m,p)
	[a,e] = [ACmode.get(color,0) for color in Acolor]
	[g,h] = [BCmode.get(color,0) for color in Bcolor]
	[b,f] = [CCmode.get(color,0) for color in Ccolor]
	[k,n] = [DCmode.get(color,0) for color in Dcolor]

	[c,i] = [AAmode.get(color,0) for color in Aalpha]
	[l,o] = [BAmode.get(color,0) for color in Balpha]
	[d,j] = [CAmode.get(color,0) for color in Calpha]
	[m,p] = [DAmode.get(color,0) for color in Dalpha]
	return (a,g,b,k,c,l,d,m,e,h,f,n,i,o,j,p)

def G_SETTIMG_Decode(bin):
	fmt,bit,pad,seg=bin.unpack('uint:3,uint:2,uint:19,uint:32')
	return (fmt,bit,1,'Texture_%s'%hex(seg))

def G_SETZIMG_Decode(bin):
	pad,addr=bin.unpack('int:24,uint:32')
	return (addr,)

def G_SETCIMG_Decode(bin):
	fmt,bit,pad,width,addr=bin.unpack('uint:3,uint:2,int:7,uint:12,uint:32')
	return (fmt,bit,width,addr)

DecodeFmt={
0x0:('gsDPNoOp',G_SNOOP_Decode),
0x04:('gsSPVertex',G_VTX_Decode),
0xbf:('gsSP1Triangles',G_TRI1_Decode),
0xbb:('gsSPTexture',G_TEXTURE_Decode),
0xbd:('gsSPPopMatrix',G_POPMTX_Decode),
0xb6:('gsSPGeometryMode',G_CLEARGEOMETRYMODE_Decode),
0xb7:('gsSPGeometryMode',G_SETGEOMETRYMODE_Decode),
0x01:('gsSPMatrix',G_MTX_Decode),
0xbc:('gsMoveWd',G_MOVEWORD_Decode),
0x03:('gsSPLight',G_MOVEMEM_Decode),
0x06:('gsSPDisplayList',G_DL_Decode),
0xb8:('gsSPEndDisplayList',G_ENDDL_Decode),
0xc0:('gsDPNoOp',G_SNOOP_Decode),
0xb4:('G_RDPHALF_1',G_RDPHALF_1_Decode),
0xb9:('gsSPSetOtherMode',G_SETOTHERMODE_L_Decode),
0xba:('gsSPSetOtherMode',G_SETOTHERMODE_H_Decode),
0xe4:('G_TEXRECT',G_TEXRECT_Decode),
0xe5:('G_TEXRECTFLIP',G_TEXRECT_Decode),
0xe6:('gsDPLoadSync',G_SNOOP_Decode),
0xe7:('gsDPPipeSync',G_SNOOP_Decode),
0xe8:('gsDPTileSync',G_SNOOP_Decode),
0xe9:('gsDPFullSync',G_SNOOP_Decode),
0xea:('G_SETKEYGB',G_SETKEYGB_Decode),
0xeb:('G_SETKEYR',G_SETKEYR_Decode),
0xec:('G_SETCONVERT',G_SETCONVERT_Decode),
0xed:('G_SETSCISSOR',G_SETSCISSOR_Decode),
0xee:('gsDPSetPrimDepth',G_SETPRIMDEPTH_Decode),
0xef:('G_RDPSETOTHERMODE',G_RDPSETOTHERMODE_Decode),
0xf0:('gsDPLoadTLUTCmd',G_LOADTLUT_Decode),
0xb3:('G_RDPHALF_2',G_RDPHALF_2_Decode),
0xf2:('gsDPSetTileSize',G_SETTILESIZE_Decode),
0xf3:('gsDPLoadBlock',G_LOADBLOCK_Decode),
0xf4:('gsDPLoadTile',G_LOADTILE_Decode),
0xf5:('gsDPSetTile',G_SETTILE_Decode),
0xf6:('G_FILLRECT',G_FILLRECT_Decode),
0xf7:('gsDPSetFillColor',G_COLOR_Decode),
0xf8:('gsDPSetFogColor',G_COLOR_Decode),
0xf9:('gsDPSetBlendColor',G_COLOR_Decode),
0xfa:('gsDPSetPrimColor',G_SETPRIMCOLOR_Decode),
0xfb:('gsDPSetEnvColor',G_COLOR_Decode),
0xfc:('gsDPSetCombineLERP',G_SETCOMBINE_Decode),
0xfd:('gsDPSetTextureImage',G_SETTIMG_Decode),
0xfe:('gsDPSetDepthImage',G_SETZIMG_Decode),
0xff:('gsDPSetColorImage',G_SETCIMG_Decode)
}