def CALL():
	pass
def RETURN():
	pass
def GOTO():
	pass

#key=MSB, value=(len, name, arg bitstring formatter, which args to take, func)
BhvCmds = {
0:(4,'BEGIN','uint:8,uint:16',(0,),None),
1:(4,'DELAY','uint:8,uint:16',(1,),None),
2:(8,'CALL','uint:24,uint:32',(1,),CALL),
3:(4,'RETURN','uint:24',(),RETURN),
4:(8,'GOTO','uint:24,uint:32',(1,),GOTO),
5:(4,'BEGIN_REPEAT','uint:8,uint:16',(1,),None),
6:(4,'END_REPEAT','uint:24',(),None),
7:(4,'END_REPEAT_CONTINUE','uint:24',(),None),
8:(4,'BEGIN_LOOP','uint:24',(),None),
9:(4,'END_LOOP','uint:24',(),None),
10:(4,'BREAK','uint:24',(),None),
11:(4,'BREAK_UNUSED','uint:24',(),None),
12:(8,'CALL_NATIVE','uint:24,uint:32',(1,),None),
13:(4,'ADD_FLOAT','uint:8,uint:16',(0,1),None),
14:(4,'SET_FLOAT','uint:8,uint:16',(0,1),None),
15:(4,'ADD_INT','uint:8,uint:16',(0,1),None),
16:(4,'SET_INT','uint:8,uint:16',(0,1),None),
17:(4,'OR_INT','uint:8,uint:16',(0,1),None),
18:(4,'BIT_CLEAR','uint:8,uint:16',(0,1),None),
19:(8,'SET_INT_RAND_RSHIFT','uint:8,3*uint:16',(0,1,2),None),
20:(8,'SET_RANDOM_FLOAT','uint:8,3*uint:16',(0,1,2),None),
21:(8,'SET_RANDOM_INT','uint:8,3*uint:16',(0,1,2),None),
22:(8,'ADD_RANDOM_FLOAT','uint:8,3*uint:16',(0,1,2),None),
23:(8,'ADD_INT_RAND_RSHIFT','uint:8,3*uint:16',(0,1,2),None),
24:(4,'CMD_NOP_1','uint:24',(),None),
25:(4,'CMD_NOP_2','uint:24',(),None),
26:(4,'CMD_NOP_3','uint:24',(),None),
27:(4,'SET_MODEL','uint:8,uint:16',(1,),None),
28:(12,'SPAWN_CHILD','uint:24,2*uint:32',(1,2),None),
29:(4,'DEACTIVATE','uint:24',(),None),
30:(4,'DROP_TO_FLOOR','uint:24',(),None),
31:(4,'SUM_FLOAT','3*uint:8',(0,1,2),None),
32:(4,'SUM_INT','3*uint:8',(0,1,2),None),
33:(4,'BILLBOARD','uint:24',(),None),
34:(4,'HIDE','uint:24',(),None),
35:(8,'SET_HITBOX','uint:24,2*uint:16',(1,2),None),
36:(4,'CMD_NOP_4','uint:8,uint:16',(0,1),None),
37:(4,'DELAY_VAR','uint:8,uint:16',(0,),None),
38:(4,'BEGIN_REPEAT_UNUSED','uint:8,uint:16',(0,),None),
39:(8,'LOAD_ANIMATIONS','uint:8,uint:16,uint:32',(0,2),None),
40:(4,'ANIMATE','uint:8,uint:16',(0,),None),
41:(12,'SPAWN_CHILD_WITH_PARAM','uint:8,uint:16,2*uint:32',(1,2,3),None),
42:(8,'LOAD_COLLISION_DATA','uint:24,uint:32',(1,),None),
43:(12,'SET_HITBOX_WITH_OFFSET','uint:24,4*uint:16',(1,2,3),None),
44:(12,'SPAWN_OBJ','uint:24,2*uint:32',(1,2),None),
45:(4,'SET_HOME','uint:24',(),None),
46:(8,'SET_HURTBOX','uint:24,2*uint:16',(1,2),None),
47:(8,'SET_INTERACTION_TYPE','uint:24,uint:32',(1,),None),
48:(0x14,'SET_OBJ_PHYSICS','uint:24,8*uint:16',(1,2,3,4,5,6,7,8),None),
49:(8,'SET_INTERACTION_SUBTYPE','uint:24,uint:32',(1,),None),
50:(4,'SCALE','uint:8,uint:16',(0,1),None),
51:(8,'PARENT_BIT_CLEAR','uint:8,uint:16,uint:32',(0,2),None),
52:(4,'ANIMATE_TEXTURE','uint:8,uint:16',(0,1),None),
53:(4,'DISABLE_RENDERING','uint:24',(),None),
54:(8,'SET_INT_UNUSED','uint:8,3*uint:16',(0,2),None),
55:(8,'SPAWN_WATER_DROPLET','uint:24,uint:32',(1,),None),
}

class Behavior():
	def __init__(self,start,s):
		self.script=s
		self.start=start
		self.cmds = BhvCmds

if __name__=="__main__":
	bhv = Behavior(0x100,"s")
	print(bhv)