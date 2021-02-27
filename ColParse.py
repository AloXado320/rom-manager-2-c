import struct
from bitstring import *
from numpy import cross, linalg
from pyhull.delaunay import DelaunayTri
import os

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
	[b,x,rom,f,CD] = ColWriteGeneric(name,s,rom,start,id)
	ColWriteLevelSpecial(b,x,rom,f)

def ColWriteActor(name,s,rom,start,id):
	[b,x,rom,f,CD] = ColWriteGeneric(name,s,rom,start,id)
	f.write("COL_END(),\n};\n")
	L = f.tell()
	f.close()
	L2 = len(CD.verts)+len(CD.DPV)
	return [start,L,L2]

diff = (lambda x,y: [a-b for a,b in zip(x,y)])

def CheckNorm(verts,start,rom):
	[v1,v2,v3] = [Halfs(start+a*6,3,rom) for a in verts]
	CP = cross(diff(v2,v1),diff(v3,v1))
	if CP[1]>0:
		return verts
	else:
		return [verts[0],verts[2],verts[1]]

#This will just be a data storage class for formatter strings of collision data.
#Each attr will be an array that is one section of collision data structure
#Special data will just be wrote to the file as normal
class ColDat():
	def __init__(self,file):
		self.Vcount=0
		self.verts=[]
		self.Tris={} #key is type, value is list of tris
		self.file=file
		self.specials = [0xe,0x24,0x25,0x27,0x2c,0x2D]
	def initType(self,type):
		if self.Tris.get(type):
			return
		else:
			self.Tris[type] = []
	def writeCol(self):
		f = self.file
		self.SplitCrossQuadrant()
		f.write(self.Vcount.format(len(self.verts)+len(self.DPV)))
		[f.write("COL_VERTEX( {}, {}, {}),\n".format(*v)) for v in self.verts]
		[f.write("COL_VERTEX( {}, {}, {}),\n".format(*v)) for v in self.DPV]
		for k,v in self.Tris.items():
			f.write("COL_TRI_INIT( {}, {}),\n".format(k,len(v)))
			if k in self.specials:
				[f.write("COL_TRI_SPECIAL( {}, {}, {}, {}),\n".format(*t)) for t in v]
			else:
				[f.write("COL_TRI( {}, {}, {}),\n".format(*t)) for t in v]
		f.write("COL_TRI_STOP(),\n")
	def SplitCrossQuadrant(self):
		self.DPV = []
		if not self.Tris.get(10):
			return
		NewTri=[]
		offset=len(self.verts)
		#Only check death plane for now
		for tri in self.Tris[10]:
			#This is inefficient
			NewV=[]
			verts = [self.verts[t] for t in tri]
			area=self.TriArea(verts)
			#there are some hackers who have reasonably sized tris
			#don't split them up. This value is half the area of a death plane tri.
			if area<268419072:
				continue
			Edges = [[verts[0],verts[1]],[verts[1],verts[2]],[verts[2],verts[0]]] #yee
			CQ = (lambda e,d: max([a[d] for a in e])>0 and min([a[d] for a in e])<0)
			CondApp = (lambda arr,x: arr.append(x) if x not in arr else 0)
			for e in Edges:
				#Split X edge
				if CQ(e,0):
					for i,v in enumerate(e):
						one=e[(i+1)%2]
						if ((one[0]-v[0]))!=0:
							Lerp=int((v[2]*(one[0]-0)+one[2]*(0-v[0]))/((one[0]-v[0])))
						else:
							Lerp=0
						if v[0]>0:
							CondApp(NewV,v)
						else:
							CondApp(NewV,(0,v[1],Lerp))
						if v[0]<0:
							CondApp(NewV,v)
						else:
							CondApp(NewV,(0,v[1],Lerp))
				#Split Z edge
				if CQ(e,2):
					for i,v in enumerate(e):
						one=e[(i+1)%2]
						if ((one[2]-v[2]))!=0:
							Lerp=int((v[0]*(one[2]-0)+one[0]*(0-v[2]))/((one[2]-v[2])))
						else:
							Lerp=0
						if v[2]>0:
							CondApp(NewV,v)
						else:
							CondApp(NewV,(Lerp,v[1],0))
						if v[2]<0:
							CondApp(NewV,v)
						else:
							CondApp(NewV,(Lerp,v[1],0))
			if NewV:
				self.DPV.extend(NewV)
				NewTri.extend(self.MakeNewTris(NewV,offset))
				offset+=len(NewV)
			else:
				NewTri.append(tri)
		if NewTri:
			self.Tris[10] = NewTri
	#Checks to see if any point is inside the tri
	def TriInterior(self,verts,tri):
		dot = (lambda x,y: sum([a+b for a,b in zip(x,y)]))
		for v in verts:
			P1 = diff(tri[2],tri[0])
			P2 = diff(tri[1],tri[0])
			P3 = diff(v,tri[0])
			dot00=dot(P1,P1)
			dot01=dot(P1,P2)
			dot02=dot(P1,P3)
			dot11=dot(P2,P2)
			dot12=dot(P2,P3)
			inv = 1/(dot00*dot11 - dot01*dot01)
			u = (dot11 * dot02 - dot01 * dot12) * inv
			v = (dot00 * dot12 - dot01 * dot02) * inv
			if ((u >= 0) and (v >= 0) and (u + v < 1)):
				return True
		return False
	def TriArea(self,Tri):
		sides = [diff(Tri[i],Tri[(i+1)%3]) for i in range(3)]
		sides = [linalg.norm(s) for s in sides]
		s = sum(sides)/2
		area = (s*(s-sides[0])*(s-sides[1])*(s-sides[2]))**.5
		return area
	def MakeNewTris(self,NewV,offset):
		#use delaunay triangulation via module (would be faster than code I wrote anyway
		#because its written as a C dll)
		pts = [[v[0],v[2]] for v in NewV] #2d projection
		triD=DelaunayTri(pts,joggle=True)
		tris=[]
		add = (lambda x,y: [a+y for a in x])
		for tri in triD.vertices:
			[v1,v2,v3] = [NewV[i] for i in tri]
			CP = cross(diff(v2,v1),diff(v3,v1))
			if CP[1]>0:
				tris.append(add(tri,offset))
			else:
				tris.append(add([tri[0],tri[2],tri[1]],offset))
		return tris
	def VecAngle(self,Vec):
		x=Vec[0]
		z=Vec[2]
		if x!=0:
			ang=arctan(abs(z/x))
		else:
			ang=math.pi/2
		if x<0:
			ang=math.pi-ang
		if z<0:
			ang=2*math.pi-ang
		return math.degrees(ang)


def ColWriteGeneric(name,s,rom,start,id):
	if os.path.exists(name):
		f = open(name,'a')
	else:
		f = open(name,'w')
	f.write("const Collision col_%s[] = {\nCOL_INIT(),\n"%(id+hex(start)))
	b=s.B2P(start)
	vnum=HalfsU(b+2,1,rom)[0]
	CD = ColDat(f)
	CD.Vcount="COL_VERTEX_INIT({}),\n"
	b+=4
	for i in range(vnum):
		q=Halfs(b+i*6,3,rom)
		CD.verts.append(q)
	x=0
	b+=vnum*6
	specials = [0xe,0x24,0x25,0x27,0x2c,0x2D]
	while(True):
		Tritype=HalfsU(x+b,2,rom)
		if Tritype[0]==0x41 or x>132000:
			break
		CD.initType(Tritype[0])
		#special tri with param
		if Tritype[0] in specials:
			for j in range(Tritype[1]):
				verts=HalfsU(x+b+4+j*8,4,rom)
				CD.Tris[Tritype[0]].append(verts)
			x+=Tritype[1]*8+4
		else:
			for j in range(Tritype[1]):
				verts=HalfsU(x+b+4+j*6,3,rom)
				if Tritype[0]==10:
					#Normals for death planes aren't proper thanks editor
					verts=CheckNorm(verts,s.B2P(start)+4,rom)
				CD.Tris[Tritype[0]].append(verts)
			x+=Tritype[1]*6+4
	CD.writeCol()
	return [b,x,rom,f,CD]

def ColWriteLevelSpecial(b,x,rom,f):
	b+=x+2
	while(True):
		special=Halfs(b,2,rom)
		#end
		if special[0]==0x42:
			f.write("COL_END(),\n};\n")
			break
		#water
		elif special[0]==0x44:
			b+=4
			f.write("COL_WATER_BOX_INIT({}),\n".format(special[1]))
			for i in range(special[1]):
				water=Halfs(b,6,rom)
				f.write("COL_WATER_BOX({}, {}, {}, {}, {}, {}),\n".format(*water))
				b+=12
		#if its neither of these something is wrong, just exit
		else:
			f.write("COL_END(),\n};\n")
			break