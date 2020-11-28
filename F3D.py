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

def ModelWrite(rom,ModelData,nameG,rootdir,root):
	#start,dl,verts,textureptrs,ambient lights, diffuse lights
	dl=[]
	vbs=[]
	txt=[]
	ambs=[]
	diffs=[]
	refs = []
	name = nameG/'model.inc.c'
	f = open(name,'w')
	wtf = root,nameG.relative_to(rootdir)/'model.inc.h'
	f.write('#include "%s"\n'%('model.inc.h'))
	for md in ModelData:
		#display lists
		DLn = 'Gfx DL_'+hex(md[0][1])+'[]'
		f.write(DLn+' = {')
		refs.append(DLn)
		f.write('\n')
		for c in md[1]:
			f.write(c+',\n')
		f.write('};\n\n')
		#verts
		for vb in md[2]:
			if vb in vbs:
				continue
			vbs.append(vb)
			VBn = 'Vtx VB_%s[]'%hex(vb[0])
			refs.append(VBn)
			f.write(VBn+' = {\n')
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
			texn = 'u16 texture_%s[]'%hex(t[1])
			refs.append(texn)
			f.write(texn+' = {\n')
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
			lig = 'Light_t Light_%s'%hex(a[1])
			refs.append(lig)
			f.write(lig+' = {\n')
			Amb=rom[a[0]:a[0]+16]
			col1=Amb[0:3]
			col2=Amb[4:7]
			dir1=Amb[8:11]
			f.write("{ %d, %d, %d}, 0, { %d, %d, %d}, 0, { %d, %d, %d}, 0\n};\n\n"%(*col1,*col2,*dir1))
		for a in md[4]:
			if a in ambs:
				continue
			ambs.append(a)
			lig = 'Ambient_t Light_%s'%hex(a[1])
			refs.append(lig)
			f.write(lig+' = {\n')
			Amb=rom[a[0]:a[0]+8]
			col1=Amb[0:3]
			col2=Amb[4:7]
			f.write("{%d, %d, %d}, 0, {%d, %d, %d}, 0\n};\n\n"%(*col1,*col2))
	f.close()
	return refs

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
	if len(q[1])<4 and (cmd[:8].uint==0xb9 or cmd[:8].uint==0xbA):
		q[0]=q[1][0]
		if q[1][0]=='gsDPSetRenderMode':
			q[1]=q[1][1:]
		else:
			q[1]=(q[1][-1],)
	ags = repr(q[1])
	ags=ags.replace("'","")
	#hardcoded cringe thanks gbi
	if len(q[1])==1:
		ags=ags.replace(',','')
	if cmd[:8].uint==6:
		if cmd[8:16].uint!=1:
			q[0]='gsSPBranchList'
	return [q[0]+ags,cmd]

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
			dl.append(cmd[0])
			if cmd[1][8:16].uint==1:
				break
		#end dl
		elif (cmd[1][:8].uint==0xb8):
			dl.append(cmd[0])
			break
		else:
			x+=8
			#concat 2 tri ones to a tri2
			q=1
			if dl:
				if dl[-1].startswith('gsSP1Triangle') and cmd[0].startswith('gsSP1Triangle'):
					old=dl[-1][14:-1]
					new=cmd[0][14:-1]
					dl[-1]="gsSP2Triangles("+old+','+new+')'
					q=0
			if q:
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

GeoMacros={
	8192:'G_CULL_BACK',
	12288:'G_CULL_BOTH',
	4096:'G_CULL_FRONT',
	65536:'G_FOG',
	131072:'G_LIGHTING',
	4:'G_SHADE',
	512:'G_SHADING_SMOOTH',
	262144:'G_TEXTURE_GEN',
	524288:'G_TEXTURE_GEN_LINEAR',
	1:'G_ZBUFFER'
}

def CheckGeoMacro(set):
	str=''
	for k,v in GeoMacros.items():
		if set&k==k:
			set=set^k
			str+=(v+"|")
	return str[:-1]

def G_CLEARGEOMETRYMODE_Decode(bin):
	pad,set=bin.unpack('uint:24,uint:32')
	if set==0:
		return (0,0)
	set=CheckGeoMacro(set)
	return (set,0)

def G_SETGEOMETRYMODE_Decode(bin):
	pad,set=bin.unpack('uint:24,uint:32')
	if set==0:
		return (0,0)
	set=CheckGeoMacro(set)
	return (0,set)

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
	return ('&Light_%s.col'%hex(seg),fuckgbi)

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
	enums={
		0:'gsDPSetAlphaCompare',
		2:'gsDPSetDepthSource',
		3:'gsDPSetRenderMode'
	}
	try:
		enum=enums[shift]
		if shift==3:
			return (enum,0,value)
		else:
			return (enum,value)
	except:
		pass
	return (0xb9,shift,bits,value)

def G_SETOTHERMODE_H_Decode(bin):
	pad,shift,bits,value=bin.unpack('3*uint:8,uint:32')
	enums={
		4:'gsDPSetAlphaDither',
		6:'gsDPSetColorDither',
		8:'gsDPSetCombineKey',
		9:'gsDPSetTextureConvert',
		12:'gsDPSetTextureFilter',
		14:'gsDPSetTextureLUT',
		16:'gsDPSetTextureLOD',
		17:'gsDPSetTextureDetail',
		19:'gsDPSetTexturePersp',
		20:'gsDPSetCycleType',
		22:'gsDPSetColorDither',
		23:'gsDPPipelineMode'
	}
	values4={
		48:'G_AD_DISABLE',
		32:'G_AD_NOISE',
		16:'G_AD_NOTPATTERN',
		0:'G_AD_PATTERN'
	}
	values6={
		64:'G_CD_BAYER',
		0:'G_CD_DISABLE',
		128:'G_CD_NOISE'
	}
	values8={
		256:'G_CK_KEY',
		0:'G_CK_NONE'
	}
	values20={
		0:'G_CYC_1CYCLE',
		1048576:'G_CYC_2CYCLE',
		2097152:'G_CYC_COPY',
		3145728:'G_CYC_FILL'
	}
	values23={
		8388608:'G_PM_1PRIMITIVE',
		0:'G_PM_NPRIMITIVE'
	}
	values9={
		0:'G_TC_CONV',
		3072:'G_TC_FILT',
		2560:'G_TC_FILTCONV'
	}
	values17={
		0:'G_TD_CLAMP',
		262144:'G_TD_DETAIL',
		131072:'G_TD_SHARPEN'
	}
	values12={
		12288:'G_TF_AVERAGE',
		8192:'G_TF_BILERP',
		0:'G_TF_POINT'
	}
	values16={
		65536:'G_TL_LOD',
		0:'G_TL_TILE'
	}
	values19={
		0:'G_TP_NONE',
		524288:'G_TP_PERSP'
	}
	values14={
		49152:'G_TT_IA16',
		0:'G_TT_NONE',
		32768:'G_TT_RGBA16'
	}
	try:
		enum=enums[shift]
		value = locals()['values'+str(shift)].get(value,value)
		return (enum,value)
	except:
		pass
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
	1:'TEXEL0',
	2:'TEXEL1',
	3:'PRIMITIVE',
	4:'SHADE',
	5:'ENVIRONMENT'
	}
	One={
	6:1
	}
	Combined={
	0:'COMBINED'
	}
	CombinedA={
	0:'COMBINED'
	}
	C={
	6:'SCALE',
	7:'Combined Alpha',
	8:'TEXEL0 ALPHA',
	9:'TEXEL1 ALPHA',
	10:'PRIMITIVE ALPHA',
	11:'SHADE ALPHA',
	12:'ENVIRONMENT ALPHA',
	13:'LOD FRACTION',
	14:'PRIM LOD FRACTION',
	15:'K5'
	}
	Noise={
	7:'Noise'
	}
	Key={
	6:'CENTER',
	7:'K4'
	}
	BasicA={
	1:'TEXEL0',
	2:'TEXEL1',
	3:'PRIMITIVE',
	4:'SHADE',
	5:'ENVIRONMENT'
	}
	LoD={
	0:'LOD FRACTION'
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
	return (fmt,bit,1,'texture_%s'%hex(seg))

def G_SETZIMG_Decode(bin):
	pad,addr=bin.unpack('int:24,uint:32')
	return (addr,)

def G_SETCIMG_Decode(bin):
	fmt,bit,pad,width,addr=bin.unpack('uint:3,uint:2,int:7,uint:12,uint:32')
	return (fmt,bit,width,addr)

DecodeFmt={
0x0:('gsDPNoOp',G_SNOOP_Decode),
0x04:('gsSPVertex',G_VTX_Decode),
0xbf:('gsSP1Triangle',G_TRI1_Decode),
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