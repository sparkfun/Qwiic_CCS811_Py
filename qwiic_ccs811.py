#-----------------------------------------------------------------------------
# exampledevice.py
#
# Simple Example device for qwiic
#------------------------------------------------------------------------
#
# Written by  SparkFun Electronics, May 2019
# 
# This python library supports the SparkFun Electroncis qwiic 
# qwiic sensor/board ecosystem on a Raspberry Pi (and compatable) single
# board computers. 
#
# More information on qwiic is at https:# www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http:# www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------

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
# Define the device name and I2C addresses. These are set in the class defintion 
# as class variables, making them avilable without having to create a class instance.
#
# The base class and associated support functions use these class varables to 
# allow users to easily identify connected devices as well as provide basic 
# device services.
#
# The name of this device - note this is private 
_DEFAULT_NAME = "Qwiic CCS811"

# Some devices have multiple availabel addresses - this is a list of these addresses.
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
# define the class that encapsulates the device being created. All information associated with this
# device is encapsulated by this class. The device class should be the only value exported 
# from this module.

class QwiicCcs811(object):

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

	def __init__(self, address=None):

		self.address = address if address != None else self.available_addresses[0]

		# load the I2C driver

		self._i2c = qwiic_i2c.getI2CDriver()
		if self._i2c == None:
			print("Unable to load I2C driver for this platform.")
			return

		# qir quality values returned from the sensor
		self.refResistance = 10000.
		self.resistance = 0.0
		self.tVOC = 0
		self.CO2 = 0
		self.vrefCounts = 0
		self.ntcCounts = 0
		self.temperature =  0.0

	def isConnected(self):
		return qwiic_i2c.isDeviceConnected(self.address)

	def begin(self):

		# wait for sensor to come up...
		time.sleep(.1)

		# found it's best to reset the device the try to check chipid.
		# If the chip is in a bad state, the ID returns 0xFF and needs
		# a kick. 

		data= [0x11,0xE5,0x72,0x8A] # Reset key

		self._i2c.writeBlock(self.address, CSS811_SW_RESET, data)

		time.sleep(.2)

		# are we who we need to be?
		chipID = self._i2c.readByte(self.address, CSS811_HW_ID)
		if not chipID in _validChipIDs:
			print("Invalid Chip ID: 0x%.2X" % chipID, file=sys.stderr)
			return self.SENSOR_ID_ERROR

		if self.checkForStatusError() or not self.appValid():
			return self.SENSOR_INTERNAL_ERROR

		self.writeCommand(CSS811_APP_START)

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

		data = self._i2c.readBlock(self.address, CSS811_ALG_RESULT_DATA, 4)

		#  Data ordered:
		#  co2MSB, co2LSB, tvocMSB, tvocLSB
	
		self.CO2 = (data[0] << 8) | data[1]
		self.tVOC = (data[2] << 8) | data[3]
		return self.SENSOR_SUCCESS

	# Checks to see if error bit is set
	def checkForStatusError( self ):

		# return the status bit
		value = self._i2c.readByte(self.address, CSS811_STATUS)

		return (value & 1 << 0)
	
	# Checks to see if DATA_READ flag is set in the status register
	def dataAvailable( self ):

		try:
			value = self._i2c.readByte(self.address, CSS811_STATUS)
		except:
			value = 0  # This will return 0

		return (value & 1 << 3 != 0)

	# Checks to see if APP_VALID flag is set in the status register
	def appValid( self ):

		try:
			value = self._i2c.readByte(self.address, CSS811_STATUS)
		except:
			value = 0  # This will return 0

		return (value & 1 << 4 != 0)

	def getErrorRegister( self ):

		try:
			value = self._i2c.readByte(self.address, CSS811_ERROR_ID)
		except:
			value = 0xFF

		return value  # Send all errors in the event of communication error

	# Returns the baseline value
	# Used for telling sensor what 'clean' air is
	# You must put the sensor in clean air and record this value
	def getBaseline( self ):
	
		try:
			value = self._i2c.readWord(self.address, CSS811_BASELINE)
		except:
			value = 0

		return value


	def setBaseline( self, input ):

		data = bytearray(2)
		data[0] = (input >> 8) & 0x00FF
		data[1] = input & 0x00FF
		
		self._i2c.writeWord(self.address, CSS811_BASELINE, input)
		
		return self.SENSOR_SUCCESS

	# Enable the nINT signal
	def enableInterrupts( self ):
	
		value = self._i2c.readByte(self.address, CSS811_MEAS_MODE)
		value |= (1 << 3) #Set INTERRUPT bit

		self._i2c.writeByte(self.address, CSS811_MEAS_MODE, value)

		return self.SENSOR_SUCCESS

	# Disable the nINT signal
	def disableInterrupts( self ):
		value = self._i2c.readByte(self.address, CSS811_MEAS_MODE)
		value &= (~(1 << 3) ) & 0xFF  #Set INTERRUPT bit. Just want first Byte

		self._i2c.writeByte(self.address, CSS811_MEAS_MODE, value)

		return self.SENSOR_SUCCESS

	# Mode 0 = Idle
	# Mode 1 = read every 1s
	# Mode 2 = every 10s
	# Mode 3 = every 60s
	# Mode 4 = RAW mode
	def setDriveMode( self,  mode ):

		if (mode > 4):
			mode = 4 # sanitize input
		
		value = self._i2c.readByte(self.address, CSS811_MEAS_MODE)	

		value &= (~(0b00000111 << 4)) & 0xFF  # Clear DRIVE_MODE bits. Just 1st byte
		value |= (mode << 4)  #Mask in mode

		self._i2c.writeByte(self.address, CSS811_MEAS_MODE, value)		

		return self.SENSOR_SUCCESS


	## Given a temp and humidity, write this data to the CSS811 for better compensation
	#$ This function expects the humidity and temp to come in as floats
	def setEnvironmentalData( self, relativeHumidity,  temperature ):

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
		envData[0] = (rH + 250) / 500
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
		envData[2] = (temp + 250) / 500
		envData[3] = 0
		self._i2c.writeBlock(self.address, CSS811_ENV_DATA, envData)

		return self.SENSOR_SUCCESS

	def setRefResistance(self, input):
		self.refResistance = input

	def readNTC( self ):
	
		data = self._i2c.readBlock(self.address, CSS811_NTC, 4)

		self.vrefCounts = (data[0] << 8) | data[1]

		self.ntcCounts = (data[2] << 8) | data[3]

		self.resistance = self.ntcCounts * self.refResistance / float(self.vrefCounts)
	
		
		# Code from Milan Malesevic and Zoran Stupic, 2011,
		# Modified by Max Mayfield,
		self.temperature = math.log(int(self.resistance))
		self.temperature = 1 / (0.001129148 + (0.000234125 * self.temperature) + \
			   (0.0000000876741 * self.temperature * self.temperature * self.temperature))
		self.temperature = self.temperature - 273.15  # Convert Kelvin to Celsius
	
		return self.SENSOR_SUCCESS


	def getTVOC( self ):
		return self.tVOC
	
	def getCO2( self ):
		return self.CO2

	
	def getResistance( self ):
		return self.resistance
	
	def getTemperature( self ):
		return self.temperature