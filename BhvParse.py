from bitstring import *

#key=MSB, value=(len, name, arg bitstring formatter, which args to take, func)
BhvCmds = {
0:(4,'BEGIN','2*uint:8,uint:16',(1,),None),
1:(4,'DELAY','uint:16,uint:16',(1,),None),
2:(8,'CALL','uint:32,uint:32',(1,),None),
3:(4,'RETURN','uint:32',(),None),
4:(8,'GOTO','uint:32,uint:32',(1,),None),
5:(4,'BEGIN_REPEAT','uint:16,uint:16',(1,),None),
6:(4,'END_REPEAT','uint:32',(),None),
7:(4,'END_REPEAT_CONTINUE','uint:32',(),None),
8:(4,'BEGIN_LOOP','uint:32',(),None),
9:(4,'END_LOOP','uint:32',(),None),
10:(4,'BREAK','uint:32',(),None),
11:(4,'BREAK_UNUSED','uint:32',(),None),
12:(8,'CALL_NATIVE','uint:32,uint:32',(1,),None),
13:(4,'ADD_FLOAT','2*uint:8,uint:16',(1,2),None),
14:(4,'SET_FLOAT','2*uint:8,uint:16',(1,2),None),
15:(4,'ADD_INT','2*uint:8,uint:16',(1,2),None),
16:(4,'SET_INT','2*uint:8,uint:16',(1,2),None),
17:(4,'OR_INT','2*uint:8,uint:16',(1,2),None),
18:(4,'BIT_CLEAR','2*uint:8,uint:16',(1,2),None),
19:(8,'SET_INT_RAND_RSHIFT','2*uint:8,3*uint:16',(1,2,3),None),
20:(8,'SET_RANDOM_FLOAT','2*uint:8,3*uint:16',(1,2,3),None),
21:(8,'SET_RANDOM_INT','2*uint:8,3*uint:16',(1,2,3),None),
22:(8,'ADD_RANDOM_FLOAT','2*uint:8,3*uint:16',(1,2,3),None),
23:(8,'ADD_INT_RAND_RSHIFT','2*uint:8,3*uint:16',(1,2,3),None),
24:(4,'CMD_NOP_1','uint:32',(),None),
25:(4,'CMD_NOP_2','uint:32',(),None),
26:(4,'CMD_NOP_3','uint:32',(),None),
27:(4,'SET_MODEL','2*uint:8,uint:16',(2,),None),
28:(12,'SPAWN_CHILD','uint:32,2*uint:32',(1,2),None),
29:(4,'DEACTIVATE','uint:32',(),None),
30:(4,'DROP_TO_FLOOR','uint:32',(),None),
31:(4,'SUM_FLOAT','4*uint:8',(1,2,3),None),
32:(4,'SUM_INT','4*uint:8',(1,2,3),None),
33:(4,'BILLBOARD','uint:32',(),None),
34:(4,'HIDE','uint:32',(),None),
35:(8,'SET_HITBOX','uint:32,2*uint:16',(1,2),None),
36:(4,'CMD_NOP_4','2*uint:*,uint:16',(1,2),None),
37:(4,'DELAY_VAR','2*uint:8,uint:16',(1,),None),
38:(4,'BEGIN_REPEAT_UNUSED','2*uint:8,uint:16',(1,),None),
39:(8,'LOAD_ANIMATIONS','uint:16,uint:16,uint:32',(0,2),None),
40:(4,'ANIMATE','2*uint:8,uint:16',(1,),None),
41:(12,'SPAWN_CHILD_WITH_PARAM','2*uint:8,uint:16,2*uint:32',(2,3,4),None),
42:(8,'LOAD_COLLISION_DATA','uint:32,uint:32',(1,),'col'),
43:(12,'SET_HITBOX_WITH_OFFSET','uint:32,4*uint:16',(1,2,3),None),
44:(12,'SPAWN_OBJ','uint:32,2*uint:32',(1,2),None),
45:(4,'SET_HOME','uint:32',(),None),
46:(8,'SET_HURTBOX','uint:32,2*uint:16',(1,2),None),
47:(8,'SET_INTERACT_TYPE','uint:32,uint:32',(1,),None),
48:(0x14,'SET_OBJ_PHYSICS','uint:32,8*uint:16',(1,2,3,4,5,6,7,8),None),
49:(8,'SET_INTERACTION_SUBTYPE','uint:32,uint:32',(1,),None),
50:(4,'SCALE','2*uint:8,uint:16',(1,2),None),
51:(8,'PARENT_BIT_CLEAR','2*uint:8,uint:16,uint:32',(1,3),None),
52:(4,'ANIMATE_TEXTURE','2*uint:8,uint:16',(1,2),None),
53:(4,'DISABLE_RENDERING','uint:32',(),None),
54:(8,'SET_INT_UNUSED','2*uint:8,3*uint:16',(1,3),None),
55:(8,'SPAWN_WATER_DROPLET','uint:32,uint:32',(1,),None),
}

class Behavior():
	def __init__(self,start,s,name):
		self.script=s
		self.start=start
		self.cmds = BhvCmds
		self.name=name
		self.Processes = {
		'col':self.Col,
		'call':self.Call,
		'field':self.Field
		}
		self.col=None
		self.funcs=None
	def Parse(self,rom):
		BhvScr = []
		x = 0
		while(True):
			buf = rom[self.start+x:self.start+x+0x14]
			c = buf[0]
			cmd = self.cmds[c]
			c = BitArray(buf[0:cmd[0]])
			c = c.unpack(cmd[2])
			args = [str(a) for i,a in enumerate(c) if i in cmd[3]]
			args = self.ProcessBhvArgs(cmd,args)
			st = cmd[1]+'({})'.format(','.join(args))
			BhvScr.append(st)
			x+=cmd[0]
			if 'BREAK' in st or 'END' in st:
				break
		return [BhvScr,self.col,self.funcs]
	def ProcessBhvArgs(self,cmd,args):
		if cmd[4]:
			return self.Processes[cmd[4]](args)
		else:
			return args
	def Field(self,args):
		return args
	def Call(self,args):
		self.funcs.append([args[0],self.name])
		return args
	def Col(self,args):
		self.col = args[0]
		return args