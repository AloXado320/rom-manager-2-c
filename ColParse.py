import struct
from bitstring import *

def TcH(bytes):
	a = struct.pack(">%dB"%len(bytes),*bytes)
	if len(bytes)==4:
		return struct.unpack(">L",a)[0]
	if len(bytes)==2:
		return struct.unpack(">H",a)[0]
	if len(bytes)==1:
		return struct.unpack(">B",a)[0]

def Halfs(start,len,rom):
	return struct.unpack(">%dh"%len,rom[start:start+len*2])

def HalfsU(start,len,rom):
	return struct.unpack(">%dH"%len,rom[start:start+len*2])

def Bytes(start,len,rom):
	return struct.unpack(">%dB"%len,rom[start:start+len])

def ColWrite(name,s,rom,start,id):
	f = open(name,'w')
	f.write("const Collision col_%s[] = {\nCOL_INIT(),\n"%(id+hex(start)))
	b=s.B2P(start)
	vnum=HalfsU(b+2,1,rom)[0]
	f.write("COL_VERTEX_INIT({}),\n".format(vnum))
	b+=4
	for i in range(vnum):
		q=Halfs(b+i*6,3,rom)
		f.write("COL_VERTEX( {}, {}, {}),\n".format(*q))
	x=0
	b+=vnum*6
	while(True):
		Tritype=HalfsU(x+b,2,rom)
		if Tritype[0]==0x41 or x>132000:
			break
		f.write("COL_TRI_INIT( {}, {}),\n".format(*Tritype))
		for j in range(Tritype[1]):
			verts=HalfsU(x+b+4+j*6,3,rom)
			f.write("COL_TRI( {}, {}, {}),\n".format(*verts))
		x+=Tritype[1]*6+4
	f.write("COL_TRI_STOP(),\n")
	b+=x+2
	while(True):
		special=Halfs(b,2,rom)
		#end
		if special[0]==0x42:
			f.write("COL_END(),\n};\n")
			break
		#water
		if special[0]==0x44:
			b+=4
			f.write("COL_WATER_BOX_INIT({}),\n".format(special[1]))
			for i in range(special[1]):
				water=Halfs(b,6,rom)
				f.write("COL_WATER_BOX({}, {}, {}, {}, {}, {}),\n".format(*water))
				b+=12