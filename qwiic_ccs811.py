#-----------------------------------------------------------------------------
# qwiic_ccs811.py
#
# Python module for the SparkFun qwiic CCS811 sensor.
#
#
# This sensor is available on the SparkFun Environmental Combo Breakout board.
#	https://www.sparkfun.com/products/14348
#
#------------------------------------------------------------------------
#
# Written by  SparkFun Electronics, May 2019
# 
# This python library supports the SparkFun Electroncis qwiic 
# qwiic sensor/board ecosystem.
#
# More information on qwiic is at https:# www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#
#==================================================================================
# Copyright (c) 2019 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE.
#==================================================================================

"""
qwiic_ccs811
============
Python module for the qwiic ccs811 sensor, which is part of the [SparkFun Qwiic Environmental Combo Breakout](https://www.sparkfun.com/products/14348)

This python package is a port of the existing [SparkFun CCS811 Arduino Library](https://github.com/sparkfun/SparkFun_CCS811_Arduino_Library)

This package can be used in conjunction with the overall [SparkFun qwiic Python Package](https://github.com/sparkfun/Qwiic_Py)

New to qwiic? Take a look at the entire [SparkFun qwiic ecosystem](https://www.sparkfun.com/qwiic).

"""
from __future__ import print_function, division
import qwiic_i2c

import time
import math
import sys


#======================================================================
# NOTE: For Raspberry Pi
#======================================================================
# For this sensor to work on the Raspberry Pi, I2C clock stretching 
# must be enabled. 
#
# To do this:
#	- Login as root to the target Raspberry Pi
#	- Open the file /boot/config.txt in your favorite editor (vi, nano ...etc)
#	- Scroll down until the bloct that contains the following is found:
#			dtparam=i2c_arm=on
#			dtparam=i2s=on
#			dtparam=spi=on
# 	- Add the following line:
#			# Enable I2C clock stretching
#			dtparam=i2c_arm_baudrate=10000
#	
#	- Save the file
#	- Reboot the raspberry pi
#====================================================================== 
def __checkIsOnRPi():

	# Are we on a Pi? First Linux?

	if not sys.platform in ('linux', 'linux2'):
		return False

	# we can find out if we are on a RPI by looking at the contents
	# of /proc/device-tree/compatable

	try:
		with open('/proc/device-tree/compatible', 'r') as fCompat:

			systype = fCompat.read()

			return systype.find('raspberrypi') != -1
	except:
		return False

# check if stretching is set if on a rpi
# 
def _checkForRPiI2CClockStretch():

	#are we on a rpi?
	if not __checkIsOnRPi():
		return

	# read the boot config file and see if the clock stretch param is set
	try:
		with open('/boot/config.txt') as fConfig:

			strConfig = fConfig.read()
			for line in strConfig.split('\n'):
				if line.find('i2c_arm_baudrate') == -1:
					continue

				# start with a comment?
				if line.strip().startswith('#'):
					break

				# is the value less <= 10000
				params = line.split('=')
				if int(params[-1]) <= 10000:
					# Stretching is enabled and set correctly. 
					return

				break
	except:
		pass

	# if we are here, then we are on a Raspberry Pi and Clock Stretching isn't 
	# set correctly. 
	# Print out a message! 

	print("""
============================================================================
 NOTE:

 For the CCS811 sensor to work on the Raspberry Pi, I2C clock stretching 
 must be enabled. 

 The following line must be added to the file /boot/config.txt

	dtparam=i2c_arm_baudrate=10000

 For more information, see the note at:
          https://github.com/sparkfun/Qwiic_CCS811_Py
============================================================================
		""")


#====================================================================== 
# Define the device name and I2C addresses. These are set in the class defintion 
# as class variables, making them avilable without having to create a class instance.
#
#
# The name of this device - note this is private 
_DEFAULT_NAME = "Qwiic CCS811"

# Some devices have multiple available addresses - this is a list of these addresses.
# NOTE: The first address in this list is considered the default I2C address for the 
# device.
_AVAILABLE_I2C_ADDRESS = [0x5B, 0x5A]

_validChipIDs = [0x81]

# Register addresses
CSS811_STATUS = 0x00
CSS811_MEAS_MODE = 0x01
CSS811_ALG_RESULT_DATA = 0x02
CSS811_RAW_DATA = 0x03
CSS811_ENV_DATA = 0x05
CSS811_NTC = 0x06
CSS811_THRESHOLDS = 0x10
CSS811_BASELINE = 0x11
CSS811_HW_ID = 0x20
CSS811_HW_VERSION = 0x21
CSS811_FW_BOOT_VERSION = 0x23
CSS811_FW_APP_VERSION = 0x24
CSS811_ERROR_ID = 0xE0
CSS811_APP_START = 0xF4
CSS811_SW_RESET = 0xFF


class QwiicCcs811(object):
	"""
	QwiicCccs811

		:param address: The I2C address to use for the device. 
						If not provided, the default address is used.
		:param i2c_driver: An existing i2c driver object. If not provided 
						a driver object is created. 
		:return: The Ccs811 device object.
		:rtype: Object
	"""
	# Constructor
	device_name = _DEFAULT_NAME
	available_addresses = _AVAILABLE_I2C_ADDRESS

	# The Arduino lib for this sensor defines return/status codes
	# as an enum in the class. Mimicing this here using class variables
	SENSOR_SUCCESS 			= 0
	SENSOR_ID_ERROR			= 1
	SENSOR_I2C_ERROR		= 2
	SENSOR_INTERNAL_ERROR 	= 3
	SENSOR_GENERIC_ERROR  	= 4

	_RPiCheck = False

	def __init__(self, address=None, i2c_driver=None):


		# As noted above, to run this device on a Raspberry Pi, 
		# clock streching is needed. 
		# 
		# Lets check if it's enabled. This is done only once in 
		# the session
		if QwiicCcs811._RPiCheck == False:
			_checkForRPiI2CClockStretch()
			QwiicCcs811._RPiCheck = True



		# Did the user specify an I2C address?

		self.address = address if address != None else self.available_addresses[0]

		# load the I2C driver if one isn't provided

		if i2c_driver == None:
			self._i2c = qwiic_i2c.getI2CDriver()
			if self._i2c == None:
				print("Unable to load I2C driver for this platform.")
				return
		else:
			self._i2c = i2c_driver

		# qir quality values returned from the sensor
		self.refResistance = 10000.
		self._resistance = 0.0
		self._TVOC = 0
		self._CO2 = 0
		self.vrefCounts = 0
		self.ntcCounts = 0
		self._temperature =  0.0

	# ----------------------------------
	# isConnected()
	#
	# Is an actual board connected to our system?

	def isConnected(self):
		""" 
			Determine if a CCS811 device is conntected to the system..

			:return: True if the device is connected, otherwise False.
			:rtype: bool

		"""
		return qwiic_i2c.isDeviceConnected(self.address)

	# ----------------------------------
	# begin()
	#
	# Initialize the system/validate the board. 
	def begin(self):
		""" 
			Initialize the operation of the Ccs811 module

			:return: Returns SENSOR_SUCCESS on success, SENSOR_ID_ERROR on bad chip ID 
				or SENSOR_INTERNAL_ERROR.
			:rtype: integer

		"""

		# wait for sensor to come up...
		time.sleep(.1)

		# found it's best to reset the device the try to check chipid.
		# If the chip is in a bad state, the ID returns 0xFF and needs
		# a kick. 

		data= [0x11,0xE5,0x72,0x8A] # Reset key

		self._i2c.writeBlock(self.address, CSS811_SW_RESET, data)

		time.sleep(.5)

		# are we who we need to be?
		chipID = self._i2c.readByte(self.address, CSS811_HW_ID)
		if not chipID in _validChipIDs:
			print("Invalid Chip ID: 0x%.2X" % chipID)
			return self.SENSOR_ID_ERROR

		if self.checkForStatusError() or not self.appValid():
			return self.SENSOR_INTERNAL_ERROR

		self._i2c.writeCommand(self.address, CSS811_APP_START)

		return self.setDriveMode(1)  # read every second

	#****************************************************************************# 
	# 
	#   Sensor functions
	# 
	# ****************************************************************************# 
	# Updates the total voltatile organic compounds (TVOC) in parts per billion (PPB)
	# and the CO2 value
	# Returns nothing
	def readAlgorithmResults( self ):
		""" 
			Reads the resutls from the sensor and stores internally

			:return: SENSOR_SUCCESS
			:rtype: integer

		"""

		data = self._i2c.readBlock(self.address, CSS811_ALG_RESULT_DATA, 4)

		#  Data ordered:
		#  co2MSB, co2LSB, tvocMSB, tvocLSB
	
		self._CO2 = (data[0] << 8) | data[1]
		self._TVOC = (data[2] << 8) | data[3]
		return self.SENSOR_SUCCESS

	#----------------------------------------------------
	# Checks to see if error bit is set
	def checkForStatusError( self ):
		""" 
			Returns  if the Error bit on the sensor is set.

			:return: value of Error bit
			:rtype: integer

		"""
		# return the status bit
		value = self._i2c.readByte(self.address, CSS811_STATUS)

		return (value & 1 << 0)
	
	#----------------------------------------------------	
	# Checks to see if DATA_READ flag is set in the status register
	def dataAvailable( self ):
		""" 
			Returns True if data is available on the sensor

			:return: True if data is available.
			:rtype: bool

		"""

		try:
			value = self._i2c.readByte(self.address, CSS811_STATUS)
		except:
			value = 0  # This will return 0

		return (value & 1 << 3 != 0)

	#----------------------------------------------------
	# Checks to see if APP_VALID flag is set in the status register
	def appValid( self ):
		""" 
			Returns True if if the sensor APP_VALID bit is set in the status register

			:return: True if APP_VALID is set
			:rtype: bool

		"""

		try:
			value = self._i2c.readByte(self.address, CSS811_STATUS)
		except:
			value = 0  # This will return 0

		return (value & 1 << 4 != 0)

	def getErrorRegister( self ):

		""" 
			Returns the value of the sensors error Register

			:return: Error register
			:rtype: int

		"""
		try:
			value = self._i2c.readByte(self.address, CSS811_ERROR_ID)
		except:
			value = 0xFF

		return value  # Send all errors in the event of communication error

	# Returns the baseline value
	# Used for telling sensor what 'clean' air is
	# You must put the sensor in clean air and record this value
	def getBaseline( self ):
		""" 
			Returns the baseline value
			Used for telling sensor what 'clean' air is
			You must put the sensor in clean air and record this value

			:return: Baseline value for the sensor
			:rtype: integer

		"""
		try:
			value = self._i2c.readWord(self.address, CSS811_BASELINE)
		except:
			value = 0

		return value

	#----------------------------------------------------
	def setBaseline( self, input ):
		""" 
			Set the baseline value for the sensor

			:return: SENSOR_SUCCESS
			:rtype: integer
		"""

		data = bytearray(2)
		data[0] = (input >> 8) & 0x00FF
		data[1] = input & 0x00FF
		
		self._i2c.writeWord(self.address, CSS811_BASELINE, input)
		
		return self.SENSOR_SUCCESS

	#----------------------------------------------------	
	# Enable the nINT signal
	def enableInterrupts( self ):
		""" 
			Set the Interrupt bit in the sensor and enable Interrupts
			on the sensor

			:return: SENSOR_SUCCESS
			:rtype: integer

		"""
		value = self._i2c.readByte(self.address, CSS811_MEAS_MODE)
		value |= (1 << 3) #Set INTERRUPT bit

		self._i2c.writeByte(self.address, CSS811_MEAS_MODE, value)

		return self.SENSOR_SUCCESS

	#----------------------------------------------------
	# Disable the nINT signal
	def disableInterrupts( self ):
		""" 
			Clear the Interrupt bit in the sensor and disable Interrupts
			on the sensor

			:return: SENSOR_SUCCESS
			:rtype: integer

		"""
		value = self._i2c.readByte(self.address, CSS811_MEAS_MODE)
		value &= (~(1 << 3) ) & 0xFF  #Set INTERRUPT bit. Just want first Byte

		self._i2c.writeByte(self.address, CSS811_MEAS_MODE, value)

		return self.SENSOR_SUCCESS

	#----------------------------------------------------
	# Mode 0 = Idle
	# Mode 1 = read every 1s
	# Mode 2 = every 10s
	# Mode 3 = every 60s
	# Mode 4 = RAW mode
	def setDriveMode( self,  mode ):
		""" 
			Set the Drive mode for the sensor

			:param mode: Valid values are:
					0 = Idle, 1 = read every 1s, 2 = every 10s, 3 = every 60s, 4 = RAW mode

			:return: SENSOR_SUCCESS
			:rtype: integer

		"""

		if (mode > 4):
			mode = 4 # sanitize input
		
		value = self._i2c.readByte(self.address, CSS811_MEAS_MODE)	

		value &= (~(0b00000111 << 4)) & 0xFF  # Clear DRIVE_MODE bits. Just 1st byte
		value |= (mode << 4)  #Mask in mode

		self._i2c.writeByte(self.address, CSS811_MEAS_MODE, value)		

		return self.SENSOR_SUCCESS

	#----------------------------------------------------
	## Given a temp and humidity, write this data to the CSS811 for better compensation
	## This function expects the humidity and temp to come in as floats
	def setEnvironmentalData( self, relativeHumidity,  temperature ):
		""" 
			Given a temp and humidity, write this data to the CSS811 for better compensation
			This function expects the humidity and temp to come in as floats

			:param relativeHumidity: The relativity Humity for the sensor to use
			:param temperature: The temperature for the sensor to use			

			:return: one of the SENSOR_ return codes.
			:rtype: integer

		"""

		# Check for invalid temperatures
		if temperature < -25 or temperature > 50 : 
			return self.SENSOR_GENERIC_ERROR
		
		# Check for invalid humidity
		if relativeHumidity < 0 or relativeHumidity > 100 :
			return self.SENSOR_GENERIC_ERROR
		
		rH = int(relativeHumidity * 1000) # 42.348 becomes 42348
		temp = int(temperature * 1000) # 23.2 becomes 23200
	
		envData = bytearray(4)
	
		# Split value into 7-bit integer and 9-bit fractional
		
		# Incorrect way from datasheet.
		# envData[0] = ((rH % 1000) / 100) > 7 ? (rH / 1000 + 1) << 1 : (rH / 1000) << 1;
		# envData[1] = 0; # CCS811 only supports increments of 0.5 so bits 7-0 will always be zero
		# if (((rH % 1000) / 100) > 2 && (((rH % 1000) / 100) < 8))
		# {
		# 	envData[0] |= 1; # Set 9th bit of fractional to indicate 0.5%
		# }
		
		# Correct rounding. See issue 8: https:# github.com/sparkfun/Qwiic_BME280_CCS811_Combo/issues/8
		envData[0] = (rH + 250) // 500
		envData[1] = 0 # CCS811 only supports increments of 0.5 so bits 7-0 will always be zero
	
		temp += 25000 # Add the 25C offset
		# Split value into 7-bit integer and 9-bit fractional
		# envData[2] = ((temp % 1000) / 100) > 7 ? (temp / 1000 + 1) << 1 : (temp / 1000) << 1;
		# envData[3] = 0;
		# if (((temp % 1000) / 100) > 2 && (((temp % 1000) / 100) < 8))
		# {
		# 	envData[2] |= 1;  # Set 9th bit of fractional to indicate 0.5C
		# }
		
		# Correct rounding
		envData[2] = (temp + 250) // 500
		envData[3] = 0
		self._i2c.writeBlock(self.address, CSS811_ENV_DATA, envData)

		return self.SENSOR_SUCCESS

	#----------------------------------------------------
	def setRefResistance(self, input):
		""" 
			Set the sensors referance resistance

			:param input: The referance resistance to set in the sensor
			:return: No return value

		"""

		self.refResistance = input

	def getRefResistance(self):
		""" 
			Get the sensors referance resistance

			:return: The current reference resistance
			:rtype: integer

		"""
		return self.refResistance

	#----------------------------------------------------
	def readNTC( self ):
		""" 
			Read the NTC values from the sensor and store for future calications. 

			NOTE: The qwiic CCS811 doesn't support this function, but other CCS811 
			sparkfun boards do.

			:return: A SENSOR_ status code
			:rtype: integer

		"""
	
		data = self._i2c.readBlock(self.address, CSS811_NTC, 4)

		self.vrefCounts = (data[0] << 8) | data[1]

		self.ntcCounts = (data[2] << 8) | data[3]

		self._resistance = self.ntcCounts * self.refResistance / float(self.vrefCounts)
	
		
		# Code from Milan Malesevic and Zoran Stupic, 2011,
		# Modified by Max Mayfield,
		if self._resistance == 0:
			# we had an error of some sorts. Log 0 is not a happy value
			print("Error - Invalid recieved from sensor")
			return 1

		self._temperature = math.log(int(self._resistance))
		self._temperature = 1 / (0.001129148 + (0.000234125 * self._temperature) + \
			   (0.0000000876741 * self._temperature * self._temperature * self._temperature))
		self._temperature = self._temperature - 273.15  # Convert Kelvin to Celsius
	
		return self.SENSOR_SUCCESS

	#----------------------------------------------------
	# TVOC Value
	def getTVOC( self ):
		""" 
			Return the current TVOC value. 

			:return: The TVOC Value
			:rtype: float

		"""
		return self._TVOC
	
	TVOC = property(getTVOC)

	#----------------------------------------------------	
	# CO2 Value
	def getCO2( self ):
		""" 
			Return the current CO2 value. 

			:return: The CO2 Value
			:rtype: float

		"""
		return self._CO2

	CO2 = property(getCO2)
	#----------------------------------------------------
	# Resistance Value
	def getResistance( self ):
		""" 
			Return the current resistance value. 

			:return: The resistance value
			:rtype: float

		"""
		return self._resistance

	resistance = property(getResistance)
	#----------------------------------------------------	
	# Temperature Value
	def getTemperature( self ):
		""" 
			Return the current temperature value. 

			:return: The temperature Value
			:rtype: float

		"""
		return self._temperature

	temperature = property(getTemperature)
