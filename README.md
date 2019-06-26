# Qwiic_CCS811_Py
<p align="center">
   <img src="https://cdn.sparkfun.com/assets/custom_pages/2/7/2/qwiic-logo-registered.jpg"  width=200>
</p>

Python module for the qwiic ccs811 sensor, which is part of the [SparkFun Qwiic Environmental Combo Breakout](https://www.sparkfun.com/products/14348)

<p align="center">
   <img src="https://cdn.sparkfun.com//assets/parts/1/2/3/2/9/14348-01.jpg"  width=300 alt="SparkFun qwiic Environmental Combo">
</p>

This python package is a port of the existing [SparkFun CCS811 Arduino Library](https://github.com/sparkfun/SparkFun_CCS811_Arduino_Library)

## Dependencies 
This driver package depends on the qwii I2C driver: 
[Qwiic_I2C_Py](https://github.com/sparkfun/Qwiic_I2C_Py)

## Installation

### PyPi Installation
On systems that support PyPi installation via pip, this library is installed using the following commands

For all users (note: the user must have sudo privileges):
```
  sudo pip install sparkfun_qwiic_ccs811
```
For the current user:

```
  pip install sparkfun_qwiic_ccs811
```
To install, make sure the setuptools package is installed on the system.

Direct installation at the command line:
```
  $ python setup.py install
```

To build a package for use with pip:
```
  $ python setup.py sdist
 ```
A package file is built and placed in a subdirectory called dist. This package file can be installed using pip.
```
  cd dist
  pip install sparkfun_qwiic_ccs811-<version>.tar.gz
```

## Raspberry Pi Use
For this sensor to work on the Raspberry Pi, I2C clock stretching must be enabled. 

To do this:
- Login as root to the target Raspberry Pi
- Open the file /boot/config.txt in your favorite editor (vi, nano ...etc)
- Scroll down until the bloct that contains the following is found:
```
dtparam=i2c_arm=on
dtparam=i2s=on
dtparam=spi=on
```
- Add the following line:
```
# Enable I2C clock stretching
dtparam=i2c_arm_baudrate=10000
```
- Save the file
- Reboot the raspberry pi

 ## Example Use
See the examples directory for more detailed use examples.

```python
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

		print("CO2:\t%.3f" % mySensor.getCO2())

		print("tVOC:\t%.3f\n" % mySensor.getTVOC())	

		
		time.sleep(1)


if __name__ == '__main__':
	try:
		runExample()
	except (KeyboardInterrupt, SystemExit) as exErr:
		print("\nEnding Basic Example")
		sys.exit(0)

```
<p align="center">
<img src="https://cdn.sparkfun.com/assets/custom_pages/3/3/4/dark-logo-red-flame.png" alt="SparkFun - Start Something">
</p>
