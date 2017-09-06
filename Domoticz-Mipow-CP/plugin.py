#		   Mipow Playbulb Plugin
#
#		   Author:	 zaraki673, 2017
#			source : https://github.com/papagei9/python-mipow
#					 https://github.com/Phhere/Playbulb
#
#
#install bluepy first (https://github.com/IanHarvey/bluepy  - install it from source)
#then you should need to make a symlink : sudo ln -s /usr/local/lib/python3.5/dist-packages/bluepy /usr/lib/python3.5/
#
"""
<plugin key="MiPowCP" name="Mipow Playbulb colorPicker" author="zaraki673" version="1.0.1" wikilink="http://www.domoticz.com/wiki/Plugins/Playbulb" externallink="http://www.playbulb.com">
	<params>
		<param field="Address" label="MAC Address" width="150px" required="true"/>
		<param field="Mode1" label="Model" width="100px">
			<options>
				<option label="Candle (fw:BTL300_v5)" value="1" default="true" />
				<option label="Garden (fw:BTL400m_1.9)" value="2"/>
				<option label="Rainbow (fw:BTL300_v5)" value="3"/>
				<option label="self.color (fw:BTL100C_v6)" value="4"/>
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
		self.state = 0
		self.effects = 0
		self.handlecolor = 0
		self.handleEffect = 0
		self.handleBattery = 0
		self.isConnect = False
		self.Sred = 0
		self.Sgreen = 0
		self.Sblue = 0
		self.Swhite = 0
		self.Smode = 0
		self.Sspeed = 0
		self.brightness = 0
		self.color = 0
		bulbbattery = [0]
		return

	def onStart(self):

		if Parameters["Mode6"] == "Debug":
			Domoticz.Debugging(1)
		#defini les switchs ds domoticz si il nexiste pas
		if (len(Devices) == 0):
			Domoticz.Device(Name="Status", Unit=1, Type=17, Switchtype=0).Create()
			Domoticz.Device(Name="self.color", Unit=10, Type=241, Subtype=1, Switchtype=7).Create()
			Options = {"LevelActions": "||||","LevelNames": "Off|Flash|Pulse|Rainbow|Rainbow Fade|Candles","LevelOffHidden": "false","SelectorStyle": "0"}
			Domoticz.Device(Name="Effect",  Unit=2, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
			Domoticz.Device(Name="Speed",  Unit=7, Type=244, Subtype=73, Switchtype=7).Create()
			Options = {"LevelActions": "||||","LevelNames": "Slowest|Slower|Faster|Fastest","LevelOffHidden": "True","SelectorStyle": "0"}
			Domoticz.Device(Name="Speed",  Unit=8, TypeName="Selector Switch", Switchtype=18, Image=12, Options=Options).Create()
			self.Smode = 0
			self.Sspeed = 0
			self.state = 0
			self.effects = 0 
			self.Swhite = 0
			self.Sred = 0
			self.Sgreen = 0
			self.Sblue = 0
			bulbbattery=[0]
			Domoticz.Log("Devices created.")
		# recupere le status de chaques switch
		else:
			if (1 in Devices): self.state = Devices[1].nValue
			if (2 in Devices): 
				if (int(Devices[2].nValue/10)) == 0:
					self.Smode = 0
				else:
					self.Smode = int((Devices[2].nValue/10)-1)
			if (7 in Devices): self.Sspeed = Devices[7].LastLevel
		# defini les handles en fonction du protocole utilisé
		if (Parameters["Mode1"]== '1') : # candles
			self.handlecolor = 0x0016
			self.handleEffect = 0x0014
			self.handleBattery = 0x001f
			handleFW=0x0027
		if (Parameters["Mode1"]== '2') :  # garden
			self.handlecolor = 0x0023
			self.handleEffect = 0x0021
			self.handleBattery = 0x002e
			handleFW=0x0027
		if (Parameters["Mode1"]== '3') :  # Rainbow
			self.handlecolor = 0x0018
			self.handleEffect = 0x0016
			self.handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '4') :  # self.color
			self.handlecolor = 0x0018
			self.handleEffect = 0x0016
			self.handleBattery = 0
			handleFW=0x0029
		if (Parameters["Mode1"]== '5') :  # Comet
			self.handlecolor = 0x0023
			self.handleEffect = 0x0021
			self.handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '6') :  # Sphere/Smart
			self.handlecolor = 0x001B
			self.handleEffect = 0x0019
			self.handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '7') :  # Spot
			self.handlecolor = 0x0025
			self.handleEffect = 0x0023
			self.handleBattery = 0
			handleFW=0x0027
		if (Parameters["Mode1"]== '8') :  # Candle btl300_v6
			self.handlecolor = 0x0019
			self.handleEffect = 0x0017
			self.handleBattery = 0
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
		bulb.disConnect()
		Domoticz.Log("Plugin is stopping.")

	# present de base 
	def onConnect(self, Connection, Status, Description):
		return

	# present de base 
	def onMessage(self, Connection, Data):
		return

	# present de base action executer qd une commande est passé a Domoticz
	def onCommand(self, Unit, Command, Level, Hue):

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
				self.Sred = 255
				self.Sgreen = 255
				self.Sblue = 255
				self.Swhite = 255
				#Domoticz.Debug('DEBUG : Action set On' )
			if (action == 'Off'):
				self.Sred = 0
				self.Sgreen = 0
				self.Sblue = 0
				self.Swhite = 0
				#Domoticz.Debug('DEBUG : Action set Off' )
			if (Command == 'Set Level'):
				self.Swhite = int(Level/100*255)
				Domoticz.Debug ('DEBUG : White self.color is set %s' % str(self.Swhite))
			if (Command == 'Set White'):
				self.Swhite = int(Level/100*255)
				Domoticz.Debug ('DEBUG : White self.color is set %s' % str(self.Swhite))
			if (Command == 'Set self.color') : #or (Command == 'Set White'):
				self.color = Level/255*360 #int(Level)/359*255)
				Domoticz.Debug ('DEBUG : Hue self.color is set %s' % str(Level))
			if (Command == 'Set self.brightness'):
				self.brightness = Level #int(Level)/100
				Domoticz.Debug ('DEBUG : self.brightness is set %s' % str(Level))   # self.brightness = l 
				#rgb = self.colorsys.hsv_to_rgb(self.color , self.brightness, 1)
				hue2rgb(self.color, self.brightness)
				#rgb = self.colorsys.hls_to_rgb(self.color, self.brightness, levelRGB) 
				self.Sred = int(outR*255/100) #int(rgb[0]*255)
				self.Sgreen = int(outG*255/100) #int(rgb[1]*255)
				self.Sblue = int(outB*255/100) # int(rgb[2]*255)
				#self.Sred = rgb[0]
				#self.Sgreen = rgb[1]
				#self.Sblue = rgb[2]
				Domoticz.Debug('DEBUG : Action set RGB' )
				Domoticz.Debug('DEBUG : red ' )
				Domoticz.Debug(str(self.Sred) )
				Domoticz.Debug('DEBUG : green ' )
				Domoticz.Debug(str(self.Sgreen) )
				Domoticz.Debug('DEBUG : blue ' )
				Domoticz.Debug(str(self.Sblue) )
			#try:
			#	if (self.isConnect == True):
			#		bulb.send_packet(self.Swhite, self.Sred, self.Sgreen, self.Sblue, self.Smode, self.Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s self.color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 1):
			#recupere l'état du switch
			# Si action = on
			if (action == 'On'):
				self.Sred = 255
				self.Sgreen = 255
				self.Sblue = 255
				self.Swhite = 255
				#Domoticz.Debug('DEBUG : Action set On' )
			if (action == 'Off'):
				self.Sred = 0
				self.Sgreen = 0
				self.Sblue = 0
				self.Swhite = 0
				if self.Smode != 0 :
					self.Smode = 0
					self.Sspeed = 0
				#Domoticz.Debug('DEBUG : Action set Off' )
			#try:
			#	if (self.isConnect == True):
			#		bulb.send_packet(self.Swhite, self.Sred, self.Sgreen, self.Sblue, self.Smode, self.Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s self.color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 2):
			if (Level == 0) :
				Domoticz.Debug("Set to Off")
				#CheckStatus()
				self.Smode=0
				self.Sspeed = 0
				#UpdateAllDevice()
				MajDevice(self, 2,0, 'off')
			if (Level == 10) :
				Domoticz.Debug("Set to Flash")
				self.Smode=0
				if self.Sspeed == 0 :
					self.Sspeed = 100
				MajDevice(self, 2,1, 10)
			if (Level == 20) :
				Domoticz.Debug("Set to Pusle")
				self.Smode=1
				if self.Sspeed == 0 :
					self.Sspeed = 100
				MajDevice(self, 2,1, 20)
			if (Level == 30) :
				Domoticz.Debug("Set to Rainbow")
				self.Smode=2
				if self.Sspeed == 0 :
					self.Sspeed = 100
				MajDevice(self, 2,1, 30)
			if (Level == 40) :
				Domoticz.Debug("Set to Fire")
				self.Smode=3
				if self.Sspeed == 0 :
					self.Sspeed = 100
				MajDevice(self, 2,1, 40)
			if (Level == 50) :
				Domoticz.Debug("Set to Fire")
				self.Smode=4
				if self.Sspeed == 0 :
					self.Sspeed = 100
				MajDevice(self, 2,1, 50)


		if (Unit == 7):
			if (action == 'On'):
				self.Sspeed = int((100-Devices[7].LastLevel)/100*255)
			if (action == 'Off'):
				self.Sspeed = 0
			if (Command == 'Set Level'):
				if Level == 100 :
					self.Sspeed =1
				else :
					self.Sspeed = int((100-Level)/100*255)
			Domoticz.Debug('DEBUG : speed is set %s' % str(self.Sspeed))
			#try:
			#	if (self.isConnect == True):
			#		bulb.send_packet(self.Swhite, self.Sred, self.Sgreen, self.Sblue, self.Smode, self.Sspeed)
			#	else :
			#		Domoticz.Log('Device not connect')
			#except btle.BTLEException as err:
			#	Domoticz.Log('ERROR when setting plug %s with command %s self.color  %s (code %d)' % (Parameters["Address"], str(Command), str(Level) , err.code))

		if (Unit == 8):
			#if (Level == 0) :
			#	Domoticz.Debug("Set speed Off")
			#	self.Sspeed = 0
				#MajDevice(self, 8,0, 'off')
			if (Level == 10) :
				Domoticz.Debug("Set speed Slowest")
				self.Sspeed = 250
				#MajDevice(self, 8,1, 'on')
			if (Level == 20) :
				Domoticz.Debug("Set speed slower")
				self.Sspeed = self.Sspeed + 10
				if self.Sspeed >= 256 :
					self.Sspeed = 255
				#MajDevice(self, 8,1, 'on')
			if (Level == 30) :
				Domoticz.Debug("Set speed faster")
				self.Sspeed = self.Sspeed - 10
				if self.Sspeed <= 0 :
					self.Sspeed = 1
				#MajDevice(self, 8,1, 'on')
			if (Level == 40) :
				Domoticz.Debug("Set speed fastest")
				self.Sspeed = 5
				#MajDevice(self, 8,1, 'on')

		try:
			if (self.isConnect == True):
				bulb.send_packet(self.Swhite, self.Sred, self.Sgreen, self.Sblue, self.Smode, self.Sspeed)
				CheckStatus(self)
				UpdateAllDevice(self)
			else :
				Domoticz.Log('Device not connect')
		except btle.BTLEException as err:
			Domoticz.Log('ERROR when setting plug ' + Parameters["Address"] + ' , unable to connect')
		

		return True

	def onDisConnect(self, Connection):
		return

	def onHeartbeat(self):
		if (self.isConnect == True) :
			if self.handleBattery !=0 :
				bulbbattery = bulb.get_self.state(self.handleBattery)
			else :
				bulbbattery = [0]
			if Parameters["Mode3"] == "1" and (int(bulbbattery[0]) != 0):
				CheckStatus(self)
				UpdateAllDevice(self)
		else :
			try :
				bulb.connect()
			except :
				Domoticz.Log ('no connection to device')
		return True


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

def onMessage(Connection, Data):
	global _plugin
	_plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
	global _plugin
	_plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
	global _plugin
	_plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisConnect(Connection):
	global _plugin
	_plugin.onDisConnect(Connection)

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

def MajDevice(self, Unit, nValue, sValue):
	if (len(self.bulbbattery)==2):
		InCharge=int(self.bulbbattery[1])
	else:
		InCharge=0
	UpdateDevice(Unit, nValue, sValue, Devices[Unit].Image, Devices[Unit].SignalLevel, str(self.bulbbattery[0]))
	return

def UpdateDevice(Unit, nValue, sValue, Image, SignalLevel, BatteryLevel):
	# Make sure that the Domoticz device still exists (they can be deleted) before updating it 
	if (Unit in Devices):
		if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue) or (Devices[Unit].Image != Image) or (Devices[Unit].SignalLevel != SignalLevel) or (Devices[Unit].BatteryLevel != BatteryLevel) :
			Devices[Unit].Update(nValue, str(sValue),Image, SignalLevel, BatteryLevel)
			Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' SignalLevel:"+str(SignalLevel)+" batteryLevel:'"+str(BatteryLevel)+"%' ("+Devices[Unit].Name+")")
	return

def UpdateAllDevice(self):
	if self.Sspeed == 0 :
		MajDevice(self, 7,0, 'off')
		MajDevice(self, 8,0, 'off')
	else:
		MajDevice(self, 7,1, str(int(100-(self.Sspeed/255*100))))
		MajDevice(self, 8,1, 'on')
	
	if self.Smode == 0 :
		if self.Sspeed == 0 :
			MajDevice(self, 2,0, 'off')
	else:
		MajDevice(self, 2,1, str((self.Smode+1)*10))
	
	if (self.Sred != 0 ) or (self.Sgreen != 0) or (self.Sblue != 0) or (self.Swhite != 0) :
		MajDevice(self, 10,1, 'on')
		MajDevice(self, 1,1, 'on')
	elif (self.Sred == 0 ) and (self.Sgreen == 0) and (self.Sblue == 0) and (self.Swhite == 0):
		MajDevice(self, 10,0, 'off')
		MajDevice(self, 1,0, 'off')
		MajDevice(self, 2,0, 'off')
		MajDevice(self, 7,0, 'off')
		MajDevice(self, 8,0, 'off')
	return

def CheckStatus(self):

	try:
		bulbstatuscolor = bulb.get_state(self.handlecolor)
		bulbstatusEffect = bulb.get_state(self.handleEffect)

		if ((int(bulbstatusEffect[4])!=0) and (int(bulbstatusEffect[4])!=255)) or ((int(bulbstatusEffect[6])!=0) and (int(bulbstatusEffect[4])!=255)) or (int(bulbstatusEffect[0]) != 0) or (int(bulbstatusEffect[1]) != 0) or (int(bulbstatusEffect[2]) != 0) or (int(bulbstatusEffect[3]) != 0) :
			self.Sred=int(bulbstatusEffect[1])
			self.Sgreen=int(bulbstatusEffect[2])
			self.Sblue=int(bulbstatusEffect[3])
			self.Swhite=int(bulbstatusEffect[0])
			self.Sspeed=int(bulbstatusEffect[6])
			self.Smode=int(bulbstatusEffect[4])
			if self.Smode == 255 or self.Smode == -1:
				self.Smode = 0
				self.Sspeed = 0

		else :
			self.Sred=int(bulbstatusself.color[1])
			self.Sgreen=int(bulbstatusself.color[2])
			self.Sblue=int(bulbstatusself.color[3])
			self.Swhite=int(bulbstatusself.color[0])
			self.Sspeed=0
			self.Smode=0


	except btle.BTLEException as err:
		Domoticz.Log("error while get status")
		
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
		try:
			self.device = btle.Peripheral(self.mac, addrType=btle.ADDR_TYPE_PUBLIC, iface=int(self.BtHW))
			self.device.setDelegate(Delegate(self))
			
		except btle.BTLEException as err:
			Domoticz.Log('Error connecting device - is it up ? (btle error code : %d)' % (err.code) )
			return

	def disconnect(self):
		self.device.disconnect()
		
	def send_packet(self, white, red, green, blue, mode, speed):
		if (Parameters["Mode1"]== '1') or (Parameters["Mode1"]== '6') or (Parameters["Mode1"]== '7') or (Parameters["Mode1"]== '8'): # Candles Sphere  spot ?
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

	
