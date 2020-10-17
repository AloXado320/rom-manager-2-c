import struct
import time

def B2I(bytes):
	return int(bytes.hex(),16)

#X will be bytes object
#cmd,length,(optionals):action,var,'ext'
Cmds={
0:(lambda x:['GEO_BRANCH_AND_LINK(%s)'%('Geo_'+hex(B2I(x[4:8]))),8,'PUSH',x[4:8],'ext']),
1:(lambda x:['GEO_END()',4]),
2:(lambda x:['GEO_BRANCH(%d,%s)'%(x[1],'Geo_'+hex(B2I(x[4:8]))),8,'PUSH',x[4:8],'ext']),
3:(lambda x:['GEO_RETURN()',4,'POP',0,'ext']),
4:(lambda x:['GEO_OPEN_NODE()',4]),
5:(lambda x:['GEO_CLOSE_NODE()',4]),
6:(lambda x:['GEO_ASSIGN_AS_VIEW(%d)'%((B2I(x[2:4]))),4]),
7:(lambda x:['GEO_UPDATE_NODE_FLAGS(%d,%d)'%(x[1],(B2I(x[2:4]))),4]),
8:(lambda x:['GEO_NODE_SCREEN_AREA(%d,%d,%d,%d,%d)'%(x[3],(B2I(x[4:6])),(B2I(x[6:8])),(B2I(x[8:10])),(B2I(x[10:12]))),12]),
9:(lambda x:['GEO_NODE_ORTHO(%d)'%((B2I(x[2:4]))),4]),
10:(lambda x:['GEO_CAMERA_FRUSTRUM{}({},{},{}{}{})'
.format("_WITH_FUNC" if x[1] else "",
(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
"," if x[1] else "",
(B2I(x[8:12])) if x[1] else ""),
(8+min(x[1]*4,4)),'CVASM',x[8:12],'ext']),
11:(lambda x:['GEO_NODE_START()',4]),
12:(lambda x:['GEO_ZBUFFER(%d)'%(x[1]),4]),
13:(lambda x:['GEO_RENDER_RANGE(%d,%d)'%((B2I(x[4:6])),(B2I(x[6:8]))),8]),
14:(lambda x:['GEO_SWITCH_CASE(%d,%d)'%(x[3],(B2I(x[4:8]))),8,'CVASM',x[4:8],'ext']),
15:(lambda x:['GEO_CAMERA(%d,%d,%d,%d,%d,%d,%d,%d)'%((B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
(B2I(x[8:10])),(B2I(x[10:12])),(B2I(x[12:14])),
(B2I(x[14:16])),(B2I(x[16:20]))),20,'CVASM',x[16:20],'ext']),
16:(lambda x:['GEO_TRANSLATE_ROTATE(%d,%d,%d,%d,%d,%d,%d)'%((B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),(B2I(x[8:10])),(B2I(x[10:12])),(B2I(x[12:14])),(B2I(x[14:16]))),16]),
17:(lambda x:['GEO_TRANSLATE_NODE{}({},{},{},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",
x[1]&0xF,(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
"," if x[1]>>4==8 else "",'DL_'+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),
8+min(4,(x[1]>>4==8)*4)]),
18:(lambda x:['GEO_ROTATION_NODE{}({},{},{},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",
x[1]&0xF,(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
"," if x[1]>>4==8 else "",'DL_'+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),
8+min(4,(x[1]>>4==8)*4)]),
19:(lambda x:['GEO_ANIMATED_PART(%d,%d,%d,%d,%s)'%(x[1],(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),'DL_'+hex(B2I(x[8:12]))),12,'STOREDL',x[8:12],'ext']),
20:(lambda x:['GEO_BILLBOARD_WITH_PARAMS{}({},{},{},{}{}{})'.format("_AND_DL" if x[1]>>4==8 else "",
x[1]&0xF,(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
"," if x[1]>>4==8 else "",'DL_'+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),
8+min(4,(x[1]>>4==8)*4)]),
21:(lambda x:['GEO_DISPLAY_LIST(%d,%s)'%(x[1],'DL_'+hex(B2I(x[4:8]))),8,'STOREDL',x[4:8],'ext']),
22:(lambda x:['GEO_SHADOW(%d,%d,%d)'%(x[3],x[5],
(B2I(x[6:8]))),8]),
23:(lambda x:['GEO_RENDER_OBJ()',4]),
24:(lambda x:['GEO_ASM(%d,%d)'%((B2I(x[2:4])),(B2I(x[4:8]))),8,'CVASM',x[4:8],'ext']),
25:(lambda x:['GEO_BACKGROUND{}({}{}{})'.format(
"_COLOR" if not (B2I(x[4:8])) else "",
(B2I(x[2:4])),
"," if (B2I(x[4:8])) else "",
(B2I(x[4:8])) if (B2I(x[4:8])) else ""),8,'CVASM',x[4:8],'ext']),
26:(lambda x:['GEO_NOP_1A()',8]),
0x1D:(lambda x:['GEO_SCALE{}({},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",
x[1]&0xF,(B2I(x[4:8])),
"," if x[1]>>4==8 else "",(B2I(x[8:12])) if x[1]>>4==8 else ""),
8+min(4,(x[1]>>4==8)*4)]),
28:(lambda x:['GEO_HELD_OBJECT(%d,%d,%d,%d,%d)'
%(x[1],(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),(B2I(x[8:12]))),12]),
30:(lambda x:['GEO_NOP_1E()',8]),
31:(lambda x:['GEO_NOP_1F()',16]),
32:(lambda x:['GEO_CULLING_RADIUS(%d)'%(B2I(x[2:4])),4])
}

def TcH(bytes):
	a = struct.pack(">%dB"%len(bytes),*bytes)
	if len(bytes)==4:
		return struct.unpack(">L",a)[0]
	if len(bytes)==2:
		return struct.unpack(">H",a)[0]
	if len(bytes)==1:
		return struct.unpack(">B",a)[0]

def GeoParse(rom,start,script,segstart):
	x=0
	g=[ [ [],segstart] ]
	start=[start]
	DLs=[]
	t=0
	while(True):
		q=rom[start[-1]+x:start[-1]+x+24]
		C=Cmds[q[0]]
		F=C(q)
		if F[-1]=="ext":
			if F[2]=='CVASM':
				f=F[3].hex()
				r=TcH(F[3])
				if r!=0:
					label=script.GetLabel(f)
					F[0]=F[0].replace(str(r),label)
			if F[2]=="STOREDL":
				b=[a for a in F[3]]
				if b!=[0,0,0,0]:
					q=TcH(b)
					b=script.B2P(TcH(b))
					DLs.append([b,q])
			if F[2]=='PUSH':
				g[t][0].append(F[0])
				b=[a for a in F[3]]
				b=script.B2P(TcH(b))
				start[-1]=start[-1]+x+F[1]
				start.append(b)
				g.append([[],script.L4B(F[3])])
				t=len(g)-1
				x=0
				continue
			if F[2]=='POP':
				g[t][0].append(F[0])
				start.pop()
				t=len(start)-1
				x=0
				continue
		x+=F[1]
		g[t][0].append(F[0])
		if F[0]=="GEO_END()":
			break
	return (g,DLs)

def GeoWrite(geo,name):
	f=open(name,'w')
	for g in geo:
		f.write('GeoLayout Geo_%s[]= {\n'%(hex(g[1])))
		for c in g[0]:
			f.write(c+',\n')
		f.write('};\n')
	f.close()