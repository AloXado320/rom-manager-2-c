from bitstring import *

#key=MSB, value=(len, name, arg bitstring formatter, which args to take, func)
BhvCmds = {
	0:(4,'BEGIN','2*uint:8,uint:16',(1,),'list'),
	1:(4,'DELAY','uint:16,uint:16',(1,),None),
	2:(8,'CALL','uint:32,uint:32',(1,),'jump'),
	3:(4,'RETURN','uint:32',(),None),
	4:(8,'GOTO','uint:32,uint:32',(1,),'jump'),
	5:(4,'BEGIN_REPEAT','uint:16,uint:16',(1,),None),
	6:(4,'END_REPEAT','uint:32',(),None),
	7:(4,'END_REPEAT_CONTINUE','uint:32',(),None),
	8:(4,'BEGIN_LOOP','uint:32',(),None),
	9:(4,'END_LOOP','uint:32',(),None),
	10:(4,'BREAK','uint:32',(),None),
	11:(4,'BREAK_UNUSED','uint:32',(),None),
	12:(8,'CALL_NATIVE','uint:32,uint:32',(1,),'call'),
	13:(4,'ADD_FLOAT','2*uint:8,uint:16',(1,2),'field'),
	14:(4,'SET_FLOAT','2*uint:8,uint:16',(1,2),'field'),
	15:(4,'ADD_INT','2*uint:8,uint:16',(1,2),'field'),
	16:(4,'SET_INT','2*uint:8,uint:16',(1,2),'field'),
	17:(4,'OR_INT','2*uint:8,uint:16',(1,2),'field'),
	18:(4,'BIT_CLEAR','2*uint:8,uint:16',(1,2),'field'),
	19:(8,'SET_INT_RAND_RSHIFT','2*uint:8,3*uint:16',(1,2,3),'field'),
	20:(8,'SET_RANDOM_FLOAT','2*uint:8,3*uint:16',(1,2,3),'field'),
	21:(8,'SET_RANDOM_INT','2*uint:8,3*uint:16',(1,2,3),'field'),
	22:(8,'ADD_RANDOM_FLOAT','2*uint:8,3*uint:16',(1,2,3),'field'),
	23:(8,'ADD_INT_RAND_RSHIFT','2*uint:8,3*uint:16',(1,2,3),'field'),
	24:(4,'CMD_NOP_1','uint:32',(),None),
	25:(4,'CMD_NOP_2','uint:32',(),None),
	26:(4,'CMD_NOP_3','uint:32',(),None),
	27:(4,'SET_MODEL','2*uint:8,uint:16',(2,),None),
	28:(12,'SPAWN_CHILD','uint:32,2*uint:32',(1,2),None),
	29:(4,'DEACTIVATE','uint:32',(),None),
	30:(4,'DROP_TO_FLOOR','uint:32',(),None),
	31:(4,'SUM_FLOAT','4*uint:8',(1,2,3),'field3'),
	32:(4,'SUM_INT','4*uint:8',(1,2,3),'field3'),
	33:(4,'BILLBOARD','uint:32',(),None),
	34:(4,'HIDE','uint:32',(),None),
	35:(8,'SET_HITBOX','uint:32,2*uint:16',(1,2),None),
	36:(4,'CMD_NOP_4','2*uint:*,uint:16',(1,2),None),
	37:(4,'DELAY_VAR','2*uint:8,uint:16',(1,),'field'),
	38:(4,'BEGIN_REPEAT_UNUSED','2*uint:8,uint:16',(1,),None),
	39:(8,'LOAD_ANIMATIONS','uint:16,uint:16,uint:32',(0,2),'field'),
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
	51:(8,'PARENT_BIT_CLEAR','2*uint:8,uint:16,uint:32',(1,3),'field'),
	52:(4,'ANIMATE_TEXTURE','2*uint:8,uint:16',(1,2),'field'),
	53:(4,'DISABLE_RENDERING','uint:32',(),None),
	54:(8,'SET_INT_UNUSED','2*uint:8,3*uint:16',(1,3),'field'),
	55:(8,'SPAWN_WATER_DROPLET','uint:32,uint:32',(1,),None),
}

ObjectList = [
 'OBJ_LIST_PLAYER',
 'OBJ_LIST_UNUSED_1',
 'OBJ_LIST_DESTRUCTIVE',
 'OBJ_LIST_UNUSED_3',
 'OBJ_LIST_GENACTOR',
 'OBJ_LIST_PUSHABLE',
 'OBJ_LIST_LEVEL',
 'OBJ_LIST_UNUSED_7',
 'OBJ_LIST_DEFAULT',
 'OBJ_LIST_SURFACE',
 'OBJ_LIST_POLELIKE',
 'OBJ_LIST_SPAWNER',
 'OBJ_LIST_UNIMPORTANT',
 'NUM_OBJ_LISTS'
]
Fields={
	1:'oFlags',
	2:'oDialogResponse',
	2:'oDialogState',
	3:'oUnk94',
	5:'oIntangibleTimer',
	6:'oPosX',
	7:'oPosY',
	8:'oPosZ',
	9:'oVelX',
	10:'oVelY',
	11:'oVelZ',
	12:'oForwardVelS32',
	13:'oUnkBC',
	14:'oUnkC0',
	15:'oMoveAnglePitch',
	16:'oMoveAngleYaw',
	17:'oMoveAngleRoll',
	18:'oFaceAnglePitch',
	19:'oFaceAngleYaw',
	20:'oFaceAngleRoll',
	21:'oGraphYOffset',
	22:'oActiveParticleFlags',
	23:'oGravity',
	24:'oFloorHeight',
	25:'oMoveFlags',
	26:'oAnimState',
	35:'oAngleVelPitch',
	36:'oAngleVelYaw',
	37:'oAngleVelRoll',
	38:'oAnimations',
	39:'oHeldState',
	40:'oWallHitboxRadius',
	41:'oDragStrength',
	42:'oInteractType',
	43:'oInteractStatus',
	47:'oBhvParams2ndByte',
	49:'oAction',
	50:'oSubAction',
	51:'oTimer',
	52:'oBounciness',
	53:'oDistanceToMario',
	54:'oAngleToMario',
	55:'oHomeX',
	56:'oHomeY',
	57:'oHomeZ',
	58:'oFriction',
	59:'oBuoyancy',
	60:'oSoundStateID',
	61:'oOpacity',
	62:'oDamageOrCoinValue',
	63:'oHealth',
	64:'oBhvParams',
	65:'oPrevAction',
	66:'oInteractionSubtype',
	67:'oCollisionDistance',
	68:'oNumLootCoins',
	69:'oDrawingDistance',
	70:'oRoom',
	71:'oUnk1A4',
	72:'oUnk1A8',
	75:'oWallAngle',
	76:'oFloorType',
	76:'oFloorRoom',
	77:'oAngleToHome',
	78:'oFloor',
	79:'oDeathSound',
	29:'oYoshiChosenHome',
	30:'oYoshiTargetYaw',
	31:'oWoodenPostOffsetY',
	32:'oWigglerTimeUntilRandomTurn',
	33:'oWigglerTargetYaw',
	34:'oWigglerWalkAwayFromWallTimer',
	27:'oYoshiBlinkTimer',
	28:'oWoodenPostPrevAngleToMario',
	0:'oUkikiCageNextAction',
	74:'oUnagiUnk1B0',
	73:'oWigglerUnused',
	31:'oBowserUnk106',
	32:'oBowserHeldAnglePitch',
	33:'oBowserHeldAngleVelYaw',
	33:'oBowserUnk10E',
	34:'oBowserAngleToCentre',
	73:'oWigglerTextStatus',
	74:'oUnagiUnk1B2',
	27:'oUkikiTauntsToBeDone'
}

class Behavior():
	def __init__(self,start,s,name,model):
		self.script=s
		self.start=start
		self.name=name
		self.model=model
		self.Processes = {
		'list':self.List,
		'jump':self.Jump,
		'col':self.Col,
		'call':self.Call,
		'field':self.Field,
		'field3':self.Field3
		}
		self.col=None
		self.funcs=[]
	def Parse(self,rom,Bhvs):
		BhvScr = []
		x = 0
		while(True):
			buf = rom[self.start+x:self.start+x+0x14]
			c = buf[0]
			cmd = BhvCmds[c]
			c = BitArray(buf[0:cmd[0]])
			c = c.unpack(cmd[2])
			args = [str(a) for i,a in enumerate(c) if i in cmd[3]]
			args = self.ProcessBhvArgs(cmd,args)
			st = cmd[1]+'({})'.format(','.join(args))
			BhvScr.append(st)
			x+=cmd[0]
			if 'BREAK' in st or 'END' in st or 'RETURN' in st:
				break
			if 'GOTO' in st:
				if 'Custom' in args[0]:
					Bhvs.append([self.NexStart,self.script,args[0]])
				break
		return [BhvScr,self.col,self.funcs,Bhvs]
	def ProcessBhvArgs(self,cmd,args):
		if cmd[4]:
			return self.Processes[cmd[4]](args)
		else:
			return args
	def Jump(self,args):
		addr = "{:08x}".format(int(args[0]))
		self.NexStart=self.script.B2P(int(args[0])&0X7FFFFFFF)
		bhv = self.script.GetLabel(addr)
		if addr in bhv:
			bhv = " Bhv_Custom_0x{:08x}".format(int(args[0]))
		return [bhv]
	def List(self,args):
		return [ObjectList[int(args[0])]]
	def Field(self,args):
		a=Fields.get(int(args[0]))
		if a:
			args[0]=a
		return args
	def Field3(self,args):
		a=Fields.get(int(args[0]))
		b=Fields.get(int(args[1]))
		c=Fields.get(int(args[2]))
		if a:
			args[0]=a
		if b:
			args[1]=b
		if c:
			args[2]=c
		return args
	def Call(self,args):
		addr = "{:08x}".format(int(args[0]))
		Fname = self.script.GetLabel(addr)
		if addr in Fname:
			Fname = " Func_Custom_0x{:08x}".format(int(args[0]))
		self.funcs.append([args[0],self.name,Fname,self.script])
		return [Fname]
	def Col(self,args):
		self.col = args[0]
		if self.model:
			Cid = "col_{}_{}".format(self.model[0][1],hex(self.script.B2P(int(args[0])&0X7FFFFFFF)))
		else:
			Cid = "col_Unk_Collision_{}_{}".format(args[0],hex(self.script.B2P(int(args[0])&0X7FFFFFFF)))
		return [Cid]