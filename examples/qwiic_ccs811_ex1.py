#!/usr/bin/env python
#-----------------------------------------------------------------------------
# qwiic_ccs811_ex1.py
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
# Example 1
#

from __future__ import print_function
import qwiic_ccs811
import time
import sys

def runExample():

	print("\nSparkFun CCS811 Sensor Basic Example \n")
	mySensor = qwiic_ccs811.QwiicCcs811()

	if mySensor.isConnected() == False:
		print("The Qwiic CCS811 device isn't connected to the system. Please check your connection", \
			file=sys.stderr)
		return

	mySensor.begin()

	while True:

		mySensor.readAlgorithmResults()

		print("CO2:\t%.3f" % mySensor.CO2)

		print("tVOC:\t%.3f\n" % mySensor.TVOC)	

		
		time.sleep(1)


if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Basic Example")
		sys.exit(0)


