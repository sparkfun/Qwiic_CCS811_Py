#!/usr/bin/env python
#-----------------------------------------------------------------------------
# qwiic_ccs811_ex7.py
#
# Simple Example for the Qwiic CCS811 Device
#------------------------------------------------------------------------
#
# Written by  SparkFun Electronics, May 2019
# 
#
# More information on qwiic is at https://www.sparkfun.com/qwiic
#
# Do you like this library? Help support SparkFun. Buy a board!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------
# Example 3
#

from __future__ import print_function
import qwiic_ccs811
import time
import sys
import random

# Define some error messages
_deviceErrors = { \
	1 << 5 : "HeaterSupply",  \
    1 << 4 : "HeaterFault", \
    1 << 3 : "MaxResistance", \
    1 << 2 : "MeasModeInvalid",  \
    1 << 1 : "ReadRegInvalid", \
    1 << 0 : "MsgInvalid" \
}

def runExample():

	print("\nSparkFun CCS811 Sensor Example 3 - NTC data to CCS811 for compensation. \n")
	mySensor = qwiic_ccs811.QwiicCcs811()

	if mySensor.isConnected() == False:
		print("The Qwiic CCS811 device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	mySensor.begin()


	while True:

		humidityVariable = random.randrange(0, 10000)/100   # 0 to 100%
		temperatureVariable = random.randrange(500, 7000) / 100 #5C to 70C

		print("New humidity and temperature:")
		print("  Humidity:    %.2f percent relative" % humidityVariable)
		print("  Temperature: %.2f degrees C" % temperatureVariable)

		mySensor.setEnvironmentalData(humidityVariable, temperatureVariable)
		if mySensor.dataAvailable():

			mySensor.readAlgorithmResults()

			print("  CO2:\t%.3f ppm" % mySensor.CO2)
			print("  tVOC:\t%.3f ppb\n" % mySensor.TVOC)	

		elif mySensor.checkForStatusError():

			error = mySensor.getErrorRegister();
			if error == 0xFF:   
				# communication error
				print("Failed to get Error ID register from sensor")
			else:
				strErr = "Unknown Error"
				for code in _deviceErrors.keys():
					if error & code:
						strErr = _deviceErrors[code]
						break
				print("Device Error: %s" % strErr)

		time.sleep(1)


if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Example")
		sys.exit(0)


