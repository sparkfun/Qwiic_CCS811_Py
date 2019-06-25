# Qwiic_CCS811_Py

Python module for the qwiic ccs811 sensor

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
import qwiic_bme280
import time
import sys

# TODO
```
