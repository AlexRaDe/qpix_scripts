import os
import sys
import time
import datetime
from commands.helper_functions import *

def sample_channel(c): #sample one channel
    timestamps = []
    counter = 0
    ch_wr_rst_busy, ch_almost_full, ch_full, ch_rd_rst_busy, ch_almost_empty, ch_empty = read_ch_status(c)
    while (ch_empty != 1):
        current_ts = read_ch_fifo(c)
        timestamps.append(current_ts)
        ch_wr_rst_busy, ch_almost_full, ch_full, ch_rd_rst_busy, ch_almost_empty, ch_empty = read_ch_status(c)
        counter += 1
    print('\tChannel ' + str(c) + ' counts are: ' + str(counter))
    return counter, timestamps

def sample_working_channels(): #for one trial, sample all working channels
    working_channels = get_channels_in_use()
    # index = channel number; fixed-length lists keep mapping consistent even if we loop in a different order
    trial_counts = [0]*16
    trial_timestamps = [[] for _ in range(16)] #timestamps for each channel in this trial ([channel][timestamp number])
    for c in range(15, -1, -1):  # sample from channel 15 down to 0
        if c in working_channels:
            count, timestamps = sample_channel(c)
            trial_counts[c] = count
            trial_timestamps[c] = timestamps
    return trial_counts, trial_timestamps

def sample_n_trials(trials_num, win_width=64e-6, win_wait=10e-6, reset_width=50e-6,\
                                rst_cal_gap=100e-9,external_clock=True, cal_pulse=False, sampling=False):
    set_win_width(win_width)
    set_win_wait(win_wait)
    set_reset_width(reset_width)
    set_rst_cal_gap(rst_cal_gap)

    all_counts = [] #2D list containing each trial's channel counts ([trial][channel])
    all_timestamps = [] #3D list containing each trial's timestamps ([trial][channel][[timestamp number])

    startup() # system reset: note this turns ext clock off.
    for j in range(trials_num): 
        if external_clock: set_ext_clock(1) #clock back on!!
        else: set_ext_clock(0)
        if cal_pulse: calibration_pulse() #if calibrating, assert calibration sequence
        if sampling: sample_pulse() #if sampling, assert sampling sequence
        print("\tTrial: " , j+1 , " of " , trials_num)
        trial_counts, trial_timestamps = sample_working_channels() #sample
        #initial_setting_hex = os.popen("peek 0x43c00000").read() #get initial setting of register, hex string
        #initial_setting_bin = bin(int(initial_setting_hex[2:],16))[2:] #convert to binary string
        #initial_setting_bin = '0'*(32-len(initial_setting_bin)) + initial_setting_bin #convert to 32-bit binary
        #new_setting_bin = initial_setting_bin[0:27] + '0' + initial_setting_bin[28:] #clear calibration bit 4
        #new_setting_int = int(new_setting_bin, 2) #convert new setting to int
        #new_setting_hex = f'0x{new_setting_int:08X}' #convert new setting to hex
        #os.system(f'poke 0x43c00000 {new_setting_hex}') #poke new setting
        all_counts.append(trial_counts)
        all_timestamps.append(trial_timestamps)
        startup() #important: this deasserts the calibration or sampling sequence
    return all_counts, all_timestamps
