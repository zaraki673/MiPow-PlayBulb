#		   Mipow Playbulb Plugin
#
#		   Author:	 zaraki673, 2017
#			source : https://github.com/papagei9/python-mipow
#					 https://github.com/Phhere/Playbulb
#
"""
<plugin key="MiPowCP" name="Mipow PlayBulb ColorPicker" author="zaraki673" version="1.0.0" wikilink="http://www.domoticz.com/wiki/Plugins/PlayBulb" externallink="http://www.playbulb.com">
	<params>
		<param field="Address" label="MAC Address" width="150px" required="true"/>
		<param field="Mode1" label="Model" width="100px">
			<options>
				<option label="Candle (fw:BTL300_v5)" value="1" default="true" />
				<option label="Garden (fw:BTL400m_1.9)" value="2"/>
				<option label="Rainbow (fw:BTL300_v5)" value="3"/>
				<option label="Color (fw:BTL100C_v6)" value="4"/>
				<option label="Comet (fw:)" value="5"/>
				<option label="Sphere/Smart" value="6"/>
				<option label="Spot (fw:BTL203M_V1.6)(" value="7"/>
				<option label="Candle (fw:BTL300_v6)" value="8"/>
			</options>
		</param>
		<param field="Mode3" label="Activate Status" width="75px">
			<options>
				<option label="False" value="0" default="true" />
				<option label="True" value="1"/>
			</options>
		</param>
		<param field="Mode2" label="BT hardware" width="100px" required="true" >
			<options>
				<option label="hci0" value="0" default="true" />
				<option label="hci1" value="1"/>
				<option label="hci2" value="2"/>
			</options>
		</param>
		<param field="Mode6" label="Debug" width="75px">
			<options>
				<option label="True" value="Debug"/>
				<option label="False" value="Normal"  default="true" />
			</options>
		</param>
	</params>
</plugin>
"""
import Domoticz
import time
import colorsys
import base64
import math
from bluepy import btle


class BasePlugin:
	enabled = False
	
	def __init__(self):
		return

	def onStart(self):
		global state
		global effects
		global handleColor
		global handleEffect
		global handleBattery
		global Sred
		global Sgreen
		global Sblue
		global Swhite
		global Smode
		global Sspeed
		global bulb
		global isConnect


		if Parameters["Mode6"] == "Debug":
			Domoticz.Debugging(1)
		#defini les switchs ds domoticz si il nexiste pas
		if (len(Devices) == 0):
			Domoticz.Device(Name="Status", Unit=1, Type=17, Switchtype=0).Create()
			Domoticz.Device(Name="Color", Unit=10, Type=241, Subtype=1, Switchtype=7).Create()
			#Options = "LevelActions:"+stringToBase64("||||")+";LevelNames:"+stringToBase64("Off|Flash|Pulse|Rainbow|Rainbow Fade|Candles")+";LevelOffHidden:ZmFsc2U=;SelectorStyle:MA=="
			Options = {"LevelActions": "||||","LevelNames": "Off|Flash|Pulse|Rainbow|Rainbow Fade|Candles","LevelOffHidden": "false","SelectorStyle": "0"}
			Domoticz.Device(Name="Effect",  Unit=2, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
			#Domoticz.Device(Name="Red",  Unit=3, Type=244, Subtype=73, Switchtype=7).Create()
			#Domoticz.Device(Name="Green",  Unit=4, Type=244, Subtype=73, Switchtype=7).Create()
			#Domoticz.Device(Name="Blue",  Unit=5, Type=244, Subtype=73, Switchtype=7).Create()
			#Domoticz.Device(Name="White",  Unit=6, Type=244, Subtype=73, Switchtype=7).Create()
			Domoticz.Device(Name="Speed",  Unit=7, Type=244, Subtype=73, Switchtype=7).Create()
			#Options = "LevelActions:"+stringToBase64("||||")+";LevelNames:"+stringToBase64("Off|Slowest|Slower|Faster|Fastest")+";LevelOffHidden:ZmFsc2U=;SelectorStyle:MA=="
			Options = {"LevelActions": "||||","LevelNames": "Slowest|Slower|Faster|Fastest","LevelOffHidden": "True","SelectorStyle": "0"}
			Domoticz.Device(Name="Speed",  Unit=8, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
			Smode = 0
			Sspeed = 0
			state = 0
			effects = 0 
			Swhite = 0
			Sred = 0
			Sgreen = 0
			Sblue = 0
			Domoticz.Log("Devices created.")
		# recupere le status de chaques switch
		else:
			if (1 in Devices): state = Devices[1].nValue
			if (2 in Devices): 
				if (int(Devices[2].nValue/10)) == 0:
					Smode = 0
				else:
					Smode = int((Devices[2].nValue/10)-1)
			#if (3 in Devices): Sred = Devices[3].LastLevel
			#if (4 in Devices): Sgreen = Devices[4].LastLevel
			#if (5 in Devices): Sblue = Devices[5].LastLevel
			#if (6 in Devices): Swhite = Devices[6].LastLevel
			if (7 in Devices): Sspeed = Devices[7].LastLevel
		# defini les handles en fonction du protocole utilisé
		if (Parameters["Mode1"]== '1') : # candles
			handleColor = 0x0016
			handleEffect = 0x0014
			handleBattery = 0x001f
			handleFW=0x0027
		if (Parameters["Mode1"]== '2') :  # garden
			handleColor = 0x0023
			handleEffect = 0x0021
			handleBattery = 0x002e
			handleFW=0x0027
		if (Parameters["Mode1"]== '3') :  # Rainbow
			handleColor = 0x0018
			handleEffect = 0x0016
			handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '4') :  # Color
			handleColor = 0x0018
			handleEffect = 0x0016
			handleBattery = 0
			handleFW=0x0029
		if (Parameters["Mode1"]== '5') :  # Comet
			handleColor = 0x0023
			handleEffect = 0x0021
			handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '6') :  # Sphere/Smart
			handleColor = 0x001B
			handleEffect = 0x0019
			handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '7') :  # Spot
			handleColor = 0x0025
			handleEffect = 0x0023
			handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '8') :  # Candle btl300_v6
			handleColor = 0x0019
			handleEffect = 0x0017
			handleBattery = 0
			handleFW=0x002A
		# renseigne le device avec l adresse mac et le numero de l interface BT 
		bulb = mipow(Parameters["Address"], Parameters["Mode2"])
		#se connecte au Candle / Rainbow / Garden
		bulb.connect()
		# present de base 
		DumpConfigToLog()
		Domoticz.Log("Plugin is started.")
		Domoticz.Heartbeat(60)

	# present de base 
	def onStop(self):
		#se deconnecte du Candle / Rainbow / Garden
		bulb.disconnect()
		Domoticz.Log("Plugin is stopping.")

	# present de base 
	def onConnect(self, Connection, Status, Description):
		return

	# present de base 
	def onMessage(self, Connection, Data, Status, Extra):
		return

	# present de base action executer qd une commande est passé a Domoticz
	def onCommand(self, Unit, Command, Level, Hue):
		global brightness
		global color
		global Sred
		global Sgreen
		global Sblue
		global Swhite
		global Smode
		global Sspeed
		global isConnect
		Domoticz.Debug ('DEBUG : white before command is set %s' % str(Swhite))
		Domoticz.Debug ('DEBUG : red before command is set %s' % str(Sred))
		Domoticz.Debug ('DEBUG : green before command is set %s' % str(Sgreen))
		Domoticz.Debug ('DEBUG : blue before command is set %s' % str(Sblue))
		Domoticz.Debug ('DEBUG : mode before command is set %s' % str(Smode))
		Domoticz.Debug ('DEBUG : speed before command is set %s' % str(Sspeed))
		#si debug activé affiche un message dans les logs de domoticz
		Domoticz.Debug("DEBUG : onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
		# present de base 
		Command = Command.strip()
		action, sep, params = Command.partition(' ')
		action = action.capitalize()
		
		# Si le switch ID 1 est actionner, l'ID est défini dans le onStart
		if (Unit == 10):
			#recupere l'état du switch
			# Si action = on
			if (action == 'On'):
				Sred = 255
				Sgreen = 255
				Sblue = 255
				Swhite = 255
				#Domoticz.Debug('DEBUG : Action set On' )
			if (action == 'Off'):
				Sred = 0
				Sgreen = 0
				Sblue = 0
				Swhite = 0
				#Domoticz.Debug('DEBUG : Action set Off' )
			if (Command == 'Set Level'):
				Swhite = int(Level/100*255)
				Domoticz.Debug ('DEBUG : White Color is set %s' % str(Swhite))
			if (Command == 'Set White'):
				Swhite = int(Level/100*255)
				Domoticz.Debug ('DEBUG : White Color is set %s' % str(Swhite))
			if (Command == 'Set Color') : #or (Command == 'Set White'):
				color = Level/255*360 #int(Level)/359*255)
				Domoticz.Debug ('DEBUG : Hue Color is set %s' % str(Level))
			if (Command == 'Set Brightness'):
				brightness = Level #int(Level)/100
				Domoticz.Debug ('DEBUG : brightness is set %s' % str(Level))   # brightness = l 
				#rgb = colorsys.hsv_to_rgb(color , brightness, 1)
				hue2rgb(color, brightness)
				#rgb = colorsys.hls_to_rgb(color, brightness, levelRGB) 
				Sred = int(outR*255/100) #int(rgb[0]*255)
				Sgreen = int(outG*255/100) #int(rgb[1]*255)
				Sblue = int(outB*255/100) # int(rgb[2]*255)
				#Sred = rgb[0]
				#Sgreen = rgb[1]
				#Sblue = rgb[2]
				Domoticz.Debug('DEBUG : Action set RGB' )
				Domoticz.Debug('DEBUG : red ' )
				Domoticz.Debug(str(Sred) )
				Domoticz.Debug('DEBUG : green ' )
				Domoticz.Debug(str(Sgreen) )
				Domoticz.Debug('DEBUG : blue ' )
				Domoticz.Debug(str(Sblue) )
			#try:
			#	if (isConnect == True):
			#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 1):
			#recupere l'état du switch
			# Si action = on
			if (action == 'On'):
				Sred = 255
				Sgreen = 255
				Sblue = 255
				Swhite = 255
				#Domoticz.Debug('DEBUG : Action set On' )
			if (action == 'Off'):
				Sred = 0
				Sgreen = 0
				Sblue = 0
				Swhite = 0
				if Smode != 0 :
					Smode = 0
					Sspeed = 0
				#Domoticz.Debug('DEBUG : Action set Off' )
			#try:
			#	if (isConnect == True):
			#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 2):
			if (Level == 0) :
				Domoticz.Debug("Set to Off")
				#CheckStatus()
				Smode=0
				Sspeed = 0
				#UpdateAllDevice()
				MajDevice(2,0, 'off')
			if (Level == 10) :
				Domoticz.Debug("Set to Flash")
				Smode=0
				if Sspeed == 0 :
					Sspeed = 100
				MajDevice(2,1, 10)
			if (Level == 20) :
				Domoticz.Debug("Set to Pusle")
				Smode=1
				if Sspeed == 0 :
					Sspeed = 100
				MajDevice(2,1, 20)
			if (Level == 30) :
				Domoticz.Debug("Set to Rainbow")
				Smode=2
				if Sspeed == 0 :
					Sspeed = 100
				MajDevice(2,1, 30)
			if (Level == 40) :
				Domoticz.Debug("Set to Fire")
				Smode=3
				if Sspeed == 0 :
					Sspeed = 100
				MajDevice(2,1, 40)
			if (Level == 50) :
				Domoticz.Debug("Set to Fire")
				Smode=4
				if Sspeed == 0 :
					Sspeed = 100
				MajDevice(2,1, 50)
			#try:
			#	if (isConnect == True):
			#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		#if (Unit == 3):
		#	if (action == 'On'):
		#		Sred = int((Devices[Unit].LastLevel)/100*255)
		#	if (action == 'Off'):
		#		Sred = 0
		#	if (Command == 'Set Level'):
		#		Sred = int(Level/100*255)
		#	Domoticz.Debug('DEBUG : Red Color is set %s' % str(Sred))
		#	try:
		#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
		#	except btle.BTLEException as err:
		#		Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		#if (Unit == 4):
		#	if (action == 'On'):
		#		Sgreen = int((Devices[Unit].LastLevel)/100*255)
		#	if (action == 'Off'):
		#		Sgreen = 0
		#	if (Command == 'Set Level'):
		#		Sgreen = int(Level/100*255)
		#	Domoticz.Debug('DEBUG : Green Color is set %s' % str(Sgreen))
		#	try:
		#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
		#	except btle.BTLEException as err:
		#		Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		#if (Unit == 5):
		#	if (action == 'On'):
		#		Sblue = int((Devices[Unit].LastLevel)/100*255)
		#	if (action == 'Off'):
		#		Sblue = 0
		#	if (Command == 'Set Level'):
		#		Sblue = int(Level/100*255)
		#	Domoticz.Debug('DEBUG : Blue Color is set %s' % str(Sblue))
		#	try:
		#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
		#	except btle.BTLEException as err:
		#		Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		#if (Unit == 6):
		#	if (action == 'On'):
		#		Swhite = int((Devices[Unit].LastLevel)/100*255)
		#	if (action == 'Off'):
		#		Swhite = 0
		#	if (Command == 'Set Level'):
		#		Swhite = int(Level/100*255)
		#	Domoticz.Debug('DEBUG : White Color is set %s' % str(Swhite))
		#	try:
		#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
		#	except btle.BTLEException as err:
		#		Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 7):
			if (action == 'On'):
				Sspeed = int((100-Devices[7].LastLevel)/100*255)
			if (action == 'Off'):
				Sspeed = 0
			if (Command == 'Set Level'):
				if Level == 100 :
					Sspeed =1
				else :
					Sspeed = int((100-Level)/100*255)
			Domoticz.Debug('DEBUG : speed is set %s' % str(Sspeed))
			#try:
			#	if (isConnect == True):
			#		bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 8):
			#if (Level == 0) :
			#	Domoticz.Debug("Set speed Off")
			#	Sspeed = 0
				#MajDevice(8,0, 'off')
			if (Level == 10) :
				Domoticz.Debug("Set speed Slowest")
				Sspeed = 250
				#MajDevice(8,1, 'on')
			if (Level == 20) :
				Domoticz.Debug("Set speed slower")
				Sspeed = Sspeed + 10
				if Sspeed >= 256 :
					Sspeed = 255
				#MajDevice(8,1, 'on')
			if (Level == 30) :
				Domoticz.Debug("Set speed faster")
				Sspeed = Sspeed - 10
				if Sspeed <= 0 :
					Sspeed = 1
				#MajDevice(8,1, 'on')
			if (Level == 40) :
				Domoticz.Debug("Set speed fastest")
				Sspeed = 5
				#MajDevice(8,1, 'on')

		try:
			if (isConnect == True):
				bulb.send_packet(Swhite, Sred, Sgreen, Sblue, Smode, Sspeed)
				CheckStatus()
				UpdateAllDevice()
			else :
				Domoticz.Log('Device not connect')
		except btle.BTLEException as err:
			Domoticz.Log('ERROR when setting plug %s with command %s color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))
		

		return True

	def onDisconnect(self, Connection):
		return

	def onHeartbeat(self):
		global bulbbattery
		if (isConnect == True) :
			if handleBattery !=0 :
				bulbbattery = bulb.get_state(handleBattery)
			else :
				bulbbattery = [0]
			if Parameters["Mode3"] == "1" and (int(bulbbattery[0]) != 0):
				CheckStatus()
				UpdateAllDevice()
		else :
			try :
				bulb.connect()
			except :
				Domoticz.Log ('no connection to device')
		return True

	def SetSocketSettings(self, power):
		return

	def GetSocketSettings(self):
		return

	def genericPOST(self, commandName):
		return
 

global _plugin
_plugin = BasePlugin()

def onStart():
	global _plugin
	_plugin.onStart()

def onStop():
	global _plugin
	_plugin.onStop()

def onConnect(Connection, Status, Description):
	global _plugin
	_plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status, Extra):
	global _plugin
	_plugin.onMessage(Connection, Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
	global _plugin
	_plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
	global _plugin
	_plugin.onDisconnect(Connection)

def onHeartbeat():
	global _plugin
	_plugin.onHeartbeat()

	# Generic helper functions
def DumpConfigToLog():
	for x in Parameters:
		if Parameters[x] != "":
			Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
	Domoticz.Debug("Device count: " + str(len(Devices)))
	for x in Devices:
		Domoticz.Debug("Device:		   " + str(x) + " - " + str(Devices[x]))
		Domoticz.Debug("Device ID:	   '" + str(Devices[x].ID) + "'")
		Domoticz.Debug("Device Name:	 '" + Devices[x].Name + "'")
		Domoticz.Debug("Device nValue:	" + str(Devices[x].nValue))
		Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
		Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
	return

def MajDevice(Unit, nValue, sValue):
	# Make sure that the Domoticz device still exists (they can be deleted) before updating it 
	#if (Unit in Devices):
	#	if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
	#		Devices[Unit].Update(nValue, str(sValue))
	#		Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
	if (len(bulbbattery)==2):
		InCharge=int(bulbbattery[1])
	else:
		InCharge=0
	
	UpdateDevice(Unit, nValue, sValue, Devices[Unit].Image, Devices[Unit].SignalLevel, int(bulbbattery[0]))
	return

def UpdateDevice(Unit, nValue, sValue, Image, SignalLevel, BatteryLevel):
	# Make sure that the Domoticz device still exists (they can be deleted) before updating it 
	if (Unit in Devices):
		if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].Image != Image) or (Devices[Unit].SignalLevel != SignalLevel) or (Devices[Unit].BatteryLevel != BatteryLevel) :
			Devices[Unit].Update(nValue, str(sValue),Image, SignalLevel, BatteryLevel)
			Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' SignalLevel:"+str(SignalLevel)+" batteryLevel:'"+str(BatteryLevel)+"%' ("+Devices[Unit].Name+")")
	return

def UpdateAllDevice():
	#if Sred == 0 :
	#	MajDevice(3,0, 'off')
	#else:
	#	MajDevice(3,1, str(int(Sred/255*100)))
	#if Sgreen == 0 :
	#	MajDevice(4,0, 'off')
	#else:
	#	MajDevice(4,1, str(int(Sgreen/255*100)))
	#if Sblue == 0 :
	#	MajDevice(5,0, 'off')
	#else:
	#	MajDevice(5,1, str(int(Sblue/255*100)))
	#if Swhite == 0 :
	#	MajDevice(6,0, 'off')
	#else:
	#	MajDevice(6,1, str(int(Swhite/255*100)))
	if Sspeed == 0 :
		MajDevice(7,0, 'off')
		MajDevice(8,0, 'off')
	else:
		MajDevice(7,1, str(int(100-(Sspeed/255*100))))
		MajDevice(8,1, 'on')
	
	if Smode == 0 :
		if Sspeed == 0 :
			MajDevice(2,0, 'off')
	else:
		MajDevice(2,1, str((Smode+1)*10))
	
	if (Sred != 0 ) or (Sgreen != 0) or (Sblue != 0) or (Swhite != 0) :
		MajDevice(10,1, 'on')
		MajDevice(1,1, 'on')
	elif (Sred == 0 ) and (Sgreen == 0) and (Sblue == 0) and (Swhite == 0):
		MajDevice(10,0, 'off')
		MajDevice(1,0, 'off')
		MajDevice(2,0, 'off')
		#MajDevice(3,0, 'off')
		#MajDevice(4,0, 'off')
		#MajDevice(5,0, 'off')
		#MajDevice(6,0, 'off')
		MajDevice(7,0, 'off')
		MajDevice(8,0, 'off')
	return

def CheckStatus():
	global Sred
	global Sgreen
	global Sblue
	global Swhite
	global Smode
	global Sspeed
	global bulb
	global handleColor
	global handleEffect
	global handleBattery
	try:
		#Domoticz.Debug ('DEBUG : white was %s' % str(Swhite))
		#Domoticz.Debug ('DEBUG : red was %s' % str(Sred))
		#Domoticz.Debug ('DEBUG : green was %s' % str(Sgreen))
		#Domoticz.Debug ('DEBUG : blue was %s' % str(Sblue))
		#Domoticz.Debug ('DEBUG : mode was %s' % str(Smode))
		#Domoticz.Debug ('DEBUG : speed was %s' % str(Sspeed))
		bulbstatusColor = bulb.get_state(handleColor)
		bulbstatusEffect = bulb.get_state(handleEffect)
		#Domoticz.Debug ("handles color :")
		#Domoticz.Debug (str(bulbstatusColor[0]))
		#Domoticz.Debug (str(bulbstatusColor[1]))
		#Domoticz.Debug (str(bulbstatusColor[2]))
		#Domoticz.Debug (str(bulbstatusColor[3]))
		#Domoticz.Debug ("handles effets :")
		#Domoticz.Debug (str(bulbstatusEffect[0]))
		#Domoticz.Debug (str(bulbstatusEffect[1]))
		#Domoticz.Debug (str(bulbstatusEffect[2]))
		#Domoticz.Debug (str(bulbstatusEffect[3]))
		#Domoticz.Debug (str(bulbstatusEffect[4]))
		#Domoticz.Debug (str(bulbstatusEffect[6]))

		if ((int(bulbstatusEffect[4])!=0) and (int(bulbstatusEffect[4])!=255)) or ((int(bulbstatusEffect[6])!=0) and (int(bulbstatusEffect[4])!=255)) or (int(bulbstatusEffect[0]) != 0) or (int(bulbstatusEffect[1]) != 0) or (int(bulbstatusEffect[2]) != 0) or (int(bulbstatusEffect[3]) != 0) :
			Sred=int(bulbstatusEffect[1])
			Sgreen=int(bulbstatusEffect[2])
			Sblue=int(bulbstatusEffect[3])
			Swhite=int(bulbstatusEffect[0])
			Sspeed=int(bulbstatusEffect[6])
			Smode=int(bulbstatusEffect[4])
			if Smode == 255 or Smode == -1:
				Smode = 0
				Sspeed = 0
			#Domoticz.Debug ('DEBUG : status from effects get')
		else :
			Sred=int(bulbstatusColor[1])
			Sgreen=int(bulbstatusColor[2])
			Sblue=int(bulbstatusColor[3])
			Swhite=int(bulbstatusColor[0])
			Sspeed=0
			Smode=0
			#Domoticz.Debug ('DEBUG : status from color get')
		#Domoticz.Debug ('DEBUG : white check is %s' % str(Swhite))
		#Domoticz.Debug ('DEBUG : red check is %s' % str(Sred))
		#Domoticz.Debug ('DEBUG : green check is %s' % str(Sgreen))
		#Domoticz.Debug ('DEBUG : blue check is %s' % str(Sblue))
		#Domoticz.Debug ('DEBUG : mode check is %s' % str(Smode))
		#Domoticz.Debug ('DEBUG : speed check is %s' % str(Sspeed))

	except btle.BTLEException as err:
		Domoticz.Log("error while get status")
		#bulb.connect()
		
	return
	
	
def stringToBase64(s):
	return base64.b64encode(s.encode('utf-8')).decode("utf-8")


class Delegate(btle.DefaultDelegate):
	"""Delegate Class."""

	def __init__(self, bulb):
		self.bulb = bulb
		btle.DefaultDelegate.__init__(self)



class mipow:
	def __init__(self, mac, BtHW):
		self.mac = mac
		self.BtHW = BtHW

	def connect(self):
		global isConnect
		try:
			self.device = btle.Peripheral(self.mac, addrType=btle.ADDR_TYPE_PUBLIC, iface=int(self.BtHW))
			self.device.setDelegate(Delegate(self))
			isConnect = True
		except:
			Domoticz.Log("Error connecting device - is it up ?")
			isConnect = False
		return

	def disconnect(self):
		self.device.disconnect()
		
	def send_packet(self, white, red, green, blue, mode, speed):
		if (Parameters["Mode1"]== '1') or (Parameters["Mode1"]== '6') : # Candles Sphere
			if (speed != 0) :
				data = bytearray([white, red, green, blue, mode, 0, speed, 0])
				handleId = handleEffect
			else :
				data = bytearray([white, red, green, blue])
				handleId = handleColor
		if (Parameters["Mode1"]== '2') or (Parameters["Mode1"]== '3') or (Parameters["Mode1"]== '4') or (Parameters["Mode1"]== '5'): # Garden color Rainbow Comet
			if (speed != 0) :
				data = bytearray([white, red, green, blue, mode, 0, speed, speed])
				handleId = handleEffect
			else :
				data = bytearray([white, red, green, blue])
				handleId = handleColor
		initial = time.time()
		while True:
			if time.time() - initial >= 10:
				return False
			try:
				Domoticz.Debug('handles send %s' % hex(handleId))
				Domoticz.Debug('Data send %s' % str(data))
				return self.device.writeCharacteristic(handleId, data)
			except:
				Domoticz.Log("Error sending BT command")
				self.connect()
				return
		return

	def get_state(self, handleId):
		# defini les handles en fonction du protocole utilisé
		try :
			status = self.device.readCharacteristic(handleId)
		except:
			Domoticz.Log("Error getting status")
			status = [0]
			self.connect()
			return status
		return status

def hue2rgb(hue, maxValue):
	global outR
	global outG
	global outB
	hh = hue;
	if (hh >= 360.0): 
		hh = 0.0
	else :
		hh /= 60
	i = math.floor(hh)
	ff = hh - i
	saturation = 1.0
	vlue = 1.0
	p = vlue * (1.0 - saturation)
	q = vlue * (1.0 - (saturation * ff))
	t = vlue * (1.0 - (saturation * (1.0 - ff)))

	outR = int(vlue*maxValue);
	outG = int(p*maxValue);
	outB = int(q*maxValue);
	
	if i== 0:
		outR = int(vlue*maxValue)
		outG = int(t*maxValue)
		outB = int(p*maxValue)
	if i== 1:
		outR = int(q*maxValue)
		outG = int(vlue*maxValue)
		outB = int(p*maxValue)
	if i== 2:
		outR = int(p*maxValue)
		outG = int(vlue*maxValue)
		outB = int(t*maxValue)
	if i== 3:
		outR = int(p*maxValue)
		outG = int(q*maxValue)
		outB = int(vlue*maxValue)
	if i== 4:
		outR = int(t*maxValue);
		outG = int(p*maxValue);
		outB = int(vlue*maxValue)
	return outR, outG, outB
