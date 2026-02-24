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
    base_interface_addr = 0x43c00008
    data_addr = base_interface_addr + ((int(interface) - 1) * 4)

    # Convert hex string input to integer
    if isinstance(data, str):
        data_int = int(data, 16)
    else:
        data_int = data

    # Perform the write using the existing mmap connection in helper_functions
    poke(data_addr, data_int)

    # Optional: Small sleep if the FPGA logic needs time to latch the serial data
    # time.sleep(0.01)

if __name__ == "__main__":
    # Allows the script to still be run from the command line if needed
    import sys
    if len(sys.argv) > 2:
        send_serial_command(sys.argv[1], sys.argv[2])
