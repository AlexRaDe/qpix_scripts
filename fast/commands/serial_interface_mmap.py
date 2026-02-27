#### SERIAL INTERFACE ############################
# Authors: AN, ACG
# Usage: python3 serial_interface.py [1 or 2] [data in 32-bit hex]
# Notes: reset serial interfaces first
##################################################

import time
from commands.helper_functions import poke, peek

def send_serial_command(interface, data):
    """
    Direct mmap-based replacement for the serial_interface.py script.
    Writes data into the internal register of the QPix interface.
    """
    # Assuming the data_addr logic from your previous snippet
    # If 'interface' determines the address, adjust this mapping:
    # interface 1 -> 0x43c00008, interface 2 -> 0x43c0000c, etc.
    base_data_addr = 0x43c00008
    data_addr = base_data_addr + ((int(interface) - 1) * 8)

    # Convert hex string input to integer
    if isinstance(data, str):
        data_int = int(data, 16)
    else:
        data_int = data

    # Write data into internal reg
    poke(data_addr, data_int)
    time.sleep(0.5)

    base_ctrl_addr = 0x43c00004
    ctrl_addr = base_ctrl_addr + ((int(interface) - 1) * 8)

    # bit 1, loading data into FPGA shift register
    poke(ctrl_addr, 0x00000002)
    time.sleep(0.5)
    poke(ctrl_addr, 0x00000000)
    time.sleep(0.5)

    # bit 2, shift out to QPix with gated clock
    poke(ctrl_addr, 0x00000004)
    time.sleep(0.01)
 
    # bit 8, shift out to QPix with gated clock
    poke(ctrl_addr, 0x00000100)
    time.sleep(0.5)

    # de-assert bits 2 and 8
    poke(ctrl_addr, 0x00000000)

if __name__ == "__main__":
    # Allows the script to still be run from the command line if needed
    import sys
    if len(sys.argv) > 2:
        send_serial_command(sys.argv[1], sys.argv[2])
