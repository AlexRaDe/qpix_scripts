import sys
import os
import time
import math



def dac2_command(channel, vset, vref): 
    #vref = 1.137
    #vset = 0.800
    #vset = 0.750

    #dac_addr = "0x48"
    dac_addr = "0x49"

    # 12-bit DAC
    steps = vref/4096
    if (vset <= 0):
        counts = 0x000
        print ("Invalid voltage specified! Value should be 0 - " + str(vset) + " V")
    elif (vset >= vref):
        counts = 0xfff
        print ("Invalid voltage specified! Value should be 0 - " + str(vset) + " V")
    else:
        counts = math.floor(vset/steps)

    # Set all 8 channels
    counts_formatted = str.format('{:04X}', counts << 4)
    msn = counts_formatted[0:2] 
    lsn = counts_formatted[2:4]

    #for channel in range(0, 8):
    command = 'i2cset -y 1 ' + dac_addr + ' 0x0' + str(channel) + ' 0x' + msn + ' 0x' + lsn + ' i'
    print ("Sending command: " + command)
    i2c_raw = os.popen(command).read()
    return command


# Channel 15
command = dac2_command(7, 0.800, 1.137)
i2c_raw = os.popen(command).read()
# Channel 14
command = dac2_command(6, 0.800, 1.137)
i2c_raw = os.popen(command).read()
# Channel 13
command = dac2_command(5, 0.800, 1.137)
i2c_raw = os.popen(command).read()
# Channel 12
command = dac2_command(4, 0.800, 1.137)
i2c_raw = os.popen(command).read()
# Channel 11
command = dac2_command(3, 0.800, 1.137)
i2c_raw = os.popen(command).read()
# Channel 10
command = dac2_command(2, 0.800, 1.137)
i2c_raw = os.popen(command).read()


# Channel 9 -- PFET Cascode -- 0.500 default
command = dac2_command(1, 0.800, 1.137)
i2c_raw = os.popen(command).read()
# Channel 8 -- NFET Cascode -- 0.700 default
command = dac2_command(0, 0.800, 1.137)
i2c_raw = os.popen(command).read()

