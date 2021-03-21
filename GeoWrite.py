import struct

def B2I(bytes):
	return int(bytes.hex(),16)

#X will be bytes object
#cmd,length,(optionals):action,var,'ext'
Cmds={
	0:(lambda x,y,s:['GEO_BRANCH_AND_LINK(%s)'%('Geo_'+y+hex(B2I(x[4:8]))),8,'PUSH',x[4:8],'ext']),
	1:(lambda x,y,s:['GEO_END()',4]),
	2:(lambda x,y,s:['GEO_BRANCH(%d,%s)'%(x[1],'Geo_'+y+hex(s.B2P(B2I(x[4:8])))),8,'PUSH',x[4:8],'ext']),
	3:(lambda x,y,s:['GEO_RETURN()',4,'POP',0,'ext']),
	4:(lambda x,y,s:['GEO_OPEN_NODE()',4]),
	5:(lambda x,y,s:['GEO_CLOSE_NODE()',4]),
	6:(lambda x,y,s:['GEO_ASSIGN_AS_VIEW(%d)'%((B2I(x[2:4]))),4]),
	7:(lambda x,y,s:['GEO_UPDATE_NODE_FLAGS(%d,%d)'%(x[1],(B2I(x[2:4]))),4]),
	8:(lambda x,y,s:['GEO_NODE_SCREEN_AREA(%d,%d,%d,%d,%d)'%(x[3],(B2I(x[4:6])),(B2I(x[6:8])),(B2I(x[8:10])),(B2I(x[10:12]))),12]),
	9:(lambda x,y,s:['GEO_NODE_ORTHO(%d)'%((B2I(x[2:4]))),4]),
	10:(lambda x,y,s:['GEO_CAMERA_FRUSTUM{}({},{},{}{}{})'
	.format("_WITH_FUNC" if x[1] else "",
	(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
	"," if x[1] else "",
	(B2I(x[8:12])) if x[1] else ""),
	(8+min(x[1]*4,4)),'CVASM',x[8:12],'ext']),
	11:(lambda x,y,s:['GEO_NODE_START()',4]),
	12:(lambda x,y,s:['GEO_ZBUFFER(%d)'%(x[1]),4]),
	13:(lambda x,y,s:['GEO_RENDER_RANGE(%d,%d)'%((B2I(x[4:6])),(B2I(x[6:8]))),8]),
	14:(lambda x,y,s:['GEO_SWITCH_CASE(%d,%d)'%(x[3],(B2I(x[4:8]))),8,'CVASM',x[4:8],'ext']),
	15:(lambda x,y,s:['GEO_CAMERA(%d,%d,%d,%d,%d,%d,%d,%d)'%((B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
	(B2I(x[8:10])),(B2I(x[10:12])),(B2I(x[12:14])),
	(B2I(x[14:16])),(B2I(x[16:20]))),20,'CVASM',x[16:20],'ext']),
	16:(lambda x,y,s:['GEO_TRANSLATE_ROTATE{}({},{},{},{},{},{},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),(B2I(x[8:10])),(B2I(x[10:12])),(B2I(x[12:14])),(B2I(x[14:16])),"," if x[1]>>4==8 else "",'DL_'+y+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),16+min(4,(x[1]>>4==8)*4)]),
	17:(lambda x,y,s:['GEO_TRANSLATE_NODE{}({},{},{},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",
	x[1]&0xF,(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
	"," if x[1]>>4==8 else "",'DL_'+y+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),
	8+min(4,(x[1]>>4==8)*4)]),
	18:(lambda x,y,s:['GEO_ROTATION_NODE{}({},{},{},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",
	x[1]&0xF,(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
	"," if x[1]>>4==8 else "",'DL_'+y+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),
	8+min(4,(x[1]>>4==8)*4)]),
	19:(lambda x,y,s:['GEO_ANIMATED_PART(%d,%d,%d,%d,%s)'%(x[1],(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),'DL_'+y+hex(B2I(x[8:12])) if B2I(x[8:12])>0 else '0'),12,'STOREDL',x[8:12],'ext']),
	20:(lambda x,y,s:['GEO_BILLBOARD_WITH_PARAMS{}({},{},{},{}{}{})'.format("_AND_DL" if x[1]>>4==8 else "",
	x[1]&0xF,(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),
	"," if x[1]>>4==8 else "",'DL_'+y+hex(B2I(x[8:12])) if x[1]>>4==8 else ""),
	8+min(4,(x[1]>>4==8)*4)]),
	21:(lambda x,y,s:['GEO_DISPLAY_LIST(%d,%s)'%(x[1],'DL_'+y+hex(B2I(x[4:8])) if B2I(x[4:8])>0 else '0'),8,'STOREDL',x[4:8],'ext']),
	22:(lambda x,y,s:['GEO_SHADOW(%d,%d,%d)'%(x[3],x[5],
	(B2I(x[6:8]))),8]),
	23:(lambda x,y,s:['GEO_RENDER_OBJ()',4]),
	24:(lambda x,y,s:['GEO_ASM(%d,%d)'%((B2I(x[2:4])),(B2I(x[4:8]))),8,'CVASM',x[4:8],'ext']),
	25:(lambda x,y,s:['GEO_BACKGROUND{}({}{}{})'.format("_COLOR" if not (B2I(x[4:8])) else "",(B2I(x[2:4])),"," if (B2I(x[4:8])) else "",
	(B2I(x[4:8])) if (B2I(x[4:8])) else ""),8,'CVASM',x[4:8],'ext']),
	26:(lambda x,y,s:['GEO_NOP_1A()',8]),
	0x1D:(lambda x,y,s:['GEO_SCALE{}({},{}{}{})'.format("_WITH_DL" if x[1]>>4==8 else "",
	x[1]&0xF,(B2I(x[4:8])),
	"," if x[1]>>4==8 else "",(B2I(x[8:12])) if x[1]>>4==8 else ""),
	8+min(4,(x[1]>>4==8)*4)]),
	28:(lambda x,y,s:['GEO_HELD_OBJECT(%d,%d,%d,%d,%d)'
	%(x[1],(B2I(x[2:4])),(B2I(x[4:6])),(B2I(x[6:8])),(B2I(x[8:12]))),12]),
	30:(lambda x,y,s:['GEO_NOP_1E()',8]),
	31:(lambda x,y,s:['GEO_NOP_1F()',16]),
	32:(lambda x,y,s:['GEO_CULLING_RADIUS(%d)'%(B2I(x[2:4])),4])
}

def TcH(bytes):
	a = struct.pack(">%dB"%len(bytes),*bytes)
	if len(bytes)==4:
		return struct.unpack(">L",a)[0]
	if len(bytes)==2:
		return struct.unpack(">H",a)[0]
	if len(bytes)==1:
		return struct.unpack(">B",a)[0]

def GetWaterData(rom,script,arg,area):
	#for editor water tables are at 0x19001800, but that might not be gauranteed
	type = arg&0xFF #0 for water, 1 for toxic mist, 2 for mist, all start with 0x50 for msb
	if script.editor:
		try:
			WT = script.B2P(0x19001800+0x50*type)
		except:
			return
	else:
	#for RM they are at 0x19006000
		try:
			WT = script.B2P(0x19006000+0x280*type+0x50*area)
		except:
			return
	UPW = (lambda x,y: struct.unpack(">L",x[y:y+4])[0])
	UPH = (lambda x,y: struct.unpack(">h",x[y:y+2])[0])
	#Because I don't really know how many water boxes there are as thats set by collision or something
	#I'm just going to detect a bad ptr and go off that
	ptrs = []
	x=0
	while(True):
		dat = UPW(rom,WT+4+x)
		try:
			if dat==0:
				break
			loc = script.B2P(dat)
			ptrs.append(loc)
		except:
			break
		x+=8
	#Now ptrs should be an array of my water data
	WB = []
	for p in ptrs:
		wb = []
		for i in range(0,0x20,2):
			wb.append(UPH(rom,i+p))
		WB.append(wb)
	return WB

def GeoParse(rom,start,script,segstart,id,cskybox,CBG,area):
	x=0
	g=[ [ [],start] ]
	start=[start]
	DLs=[]
	t=0
	WaterBoxes = []
	envfx = 0
	while(True):
		q=rom[start[-1]+x:start[-1]+x+24]
		C=Cmds[q[0]]
		F=C(q,id,script)
		if 'GEO_BACKGROUND' in F[0] and CBG:
			F[0] = 'GEO_BACKGROUND(%s+10, geo_skybox_main)'%(cskybox)
		if F[-1]=="ext":
			if F[2]=='CVASM':
				f=F[3].hex()
				r=TcH(F[3])
				if r!=0:
					label=script.GetLabel(f)
					if 'geo_movtex_draw_water_regions' in label:
						WaterBoxes.append(GetWaterData(rom,script,B2I(q[2:4]),area))
					if 'geo_envfx_main' in label and B2I(q[2:4])>0:
						envfx = 1
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
				g.append([[],b])
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
	return (g,DLs,WaterBoxes,envfx)

def GeoWrite(geo,name,id):
	f=open(name,'w')
	for k,g in enumerate(geo):
		f.write('#include "custom.model.inc.h"\nconst GeoLayout Geo_%s[]= {\n'%(id+hex(g[1])))
		for c in g[0]:
			f.write(c+',\n')
		f.write('};\n')
	f.close()

def GeoActWrite(geo,f):
	#actor geo layouts reuse DLs under different IDs
	geoSymbs = []
	geoRep = []
	for k,g in enumerate(geo):
		f.write('#include "custom.model.inc.h"\nconst GeoLayout %s[]= {\n'%g[1])
		for c in g[0]:
			addr = c.split('(')[-1].split('_')
			if len(addr)>1:
				addr=addr[-1]
				if addr in geoSymbs:
					c = geoRep[geoSymbs.index(addr)]
				else:
					geoSymbs.append(addr)
					geoRep.append(c)
			f.write(c+',\n')
		f.write('};\n')
	f.close()

def GeoActParse(rom,model):
	x=0
	g=[[[],model[1]]]
	start=[model[3]]
	script = model[5]
	id=model[1]+"_"
	DLs=[]
	t=0
	while(True):
		q=rom[start[-1]+x:start[-1]+x+24]
		C=Cmds[q[0]]
		F=C(q,id,script)
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
				g.append([[],'Geo_'+id+hex(b)])
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