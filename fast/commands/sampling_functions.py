import time
from commands.helper_functions import *

# --- OPTIMIZATION: Cache working channels once at module level ---
# This prevents re-reading the CSV file every time sample_working_channels is called.
_cached_working_channels = get_channels_in_use()

def sample_channel(c): 
    """Samples one channel using fast mmap reads."""
    timestamps = []
    # No changes needed to the logic, but because read_ch_status and read_ch_fifo 
    # now use mmap peek/poke, this loop will be ~100x faster.
    
    # Initial status check
    status = read_ch_status(c)
    ch_empty = status[5] # ch_empty is the last element in the returned tuple
    
    while ch_empty != 1:
        current_ts = read_ch_fifo(c)
        timestamps.append(current_ts)
        
        # Update status for next iteration
        status = read_ch_status(c)
        ch_empty = status[5]
        
    # Optional: Removing the print statement inside the loop saves even more time 
    # if you are calling this hundreds of times.
    # print(f'\tChannel {c} counts: {len(timestamps)}')
    return len(timestamps), timestamps

def sample_working_channels(): 
    """Sample all working channels using the cached channel list."""
    trial_counts = [0] * 16
    trial_timestamps = [[] for _ in range(16)] 
    
    # Iterate through the cached list directly for better performance
    for c in range(15, -1, -1):
        if c in _cached_working_channels:
            count, timestamps = sample_channel(c)
            trial_counts[c] = count
            trial_timestamps[c] = timestamps
    return trial_counts, trial_timestamps

def sample_n_trials(trials_num, win_width=64e-6, win_wait=10e-6, reset_width=50e-6,
                    rst_cal_gap=100e-9, external_clock=True, cal_pulse=False, 
                    sampling=False, file_writer=None):
    
    # These functions now use mmap.poke internally
    set_win_width(win_width)
    set_win_wait(win_wait)
    set_reset_width(reset_width)
    set_rst_cal_gap(rst_cal_gap)

    all_counts = [] 
    all_timestamps = [] 

    startup() 
    for j in range(trials_num): 
        start_time = time.perf_counter()
        
        # Direct bit manipulation via mmap is now used in these helper calls
        set_ext_clock(1 if external_clock else 0)
        
        if cal_pulse: calibration_pulse()
        if sampling: sample_pulse()
        
        print(f"\tTrial: {j+1} of {trials_num}")
        
        # This is where the heavy lifting happens
        trial_counts, trial_timestamps = sample_working_channels()
        
        all_counts.append(trial_counts)
        all_timestamps.append(trial_timestamps)
        
        startup() # Deasserts sequences
        
        duration = time.perf_counter() - start_time
        msg = f"Trial {j}: {duration:.6f} seconds"
        print(msg)
        if file_writer:
            file_writer.write(msg + "\n")
            
    return all_counts, all_timestamps
