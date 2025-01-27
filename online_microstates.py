#!/usr/bin/env python3
#coding:utf-8
"""
  Author:  Arnaud Desvachez --<arnaud.desvachez@gmail.com>
  Purpose: Online protocol for deep meditation state neurofeedback.
  Created: 14.10.2019
"""

import mne
import os
import sys
import time
import numpy as np
import multiprocessing as mp
from importlib import import_module

import neurodecode.utils.pycnbi_utils as pu

from neurodecode import logger
from neurodecode.utils import q_common as qc
from neurodecode.gui.streams import redirect_stdout_to_queue
from neurodecode.stream_receiver.stream_receiver import StreamReceiver

os.environ['OMP_NUM_THREADS'] = '1' # actually improves performance for multitaper
mne.set_log_level('ERROR')          # DEBUG, INFO, WARNING, ERROR, or CRITICAL


#----------------------------------------------------------------------
def check_config(cfg):
    """
    Ensure that the config file contains the parameters
    """ 
    critical_vars = {
        'COMMON': ['DATA_PATH']
        }

    optional_vars = {
        'AMP_NAME':None,
        'AMP_SERIAL':None,
        'GLOBAL_TIME': 1.0 * 60,
        'NJOBS': 1,
    }

    for key in critical_vars['COMMON']:
        if not hasattr(cfg, key):
            logger.error('%s is a required parameter' % key)
            raise RuntimeError

    for key in optional_vars:
        if not hasattr(cfg, key):
            setattr(cfg, key, optional_vars[key])
            logger.warning('Setting undefined parameter %s=%s' % (key, getattr(cfg, key)))


#----------------------------------------------------------------------
def find_lsl_stream(cfg, state):
    """
    Find the amplifier name and its serial number to connect to
    
    cfg = config file
    state = GUI sharing variable
    """
    if cfg.AMP_NAME is None and cfg.AMP_SERIAL is None:
        amp_name, amp_serial = pu.search_lsl(state, ignore_markers=True)
    else:
        amp_name = cfg.AMP_NAME
        amp_serial = cfg.AMP_SERIAL
        
    return amp_name, amp_serial
    
#----------------------------------------------------------------------
def connect_lsl_stream(cfg, amp_name, amp_serial):
    """
    Connect to the lsl stream corresponding to the provided amplifier
    name and serial number
    
    cfg = config file
    amp_name =  amplifier's name to connect to
    amp_serial = amplifier's serial number
    """
    sr = StreamReceiver(window_size=cfg.WINDOWSIZE, buffer_size=cfg.STREAMBUFFER, amp_serial=amp_serial, eeg_only=False, amp_name=amp_name)
    
    return sr

#----------------------------------------------------------------------
def run(cfg, state=mp.Value('i', 1), queue=None):
    """
    Online protocol for Alpha/Theta neurofeedback.
    """
    redirect_stdout_to_queue(logger, queue, 'INFO')
    
    # Wait the recording to start (GUI)
    while state.value == 2: # 0: stop, 1:start, 2:wait
        pass

    # Protocol runs if state equals to 1
    if not state.value:
        sys.exit(-1)
    
    #----------------------------------------------------------------------
    # LSL stream connection
    #----------------------------------------------------------------------
    # chooose amp   
    amp_name, amp_serial = find_lsl_stream(cfg, state)
    
    # Connect to lsl stream
    sr = connect_lsl_stream(cfg, amp_name, amp_serial)
    
    # Get sampling rate
    sfreq = sr.get_sample_rate()
    
    # Get trigger channel
    trg_ch = sr.get_trigger_channel()
    
   
    #----------------------------------------------------------------------
    # Main
    #----------------------------------------------------------------------
    global_timer = qc.Timer(autoreset=False)
    internal_timer = qc.Timer(autoreset=True)
    
    while state.value == 1 and global_timer.sec() < cfg.GLOBAL_TIME:
        
        #----------------------------------------------------------------------
        # Data acquisition
        #----------------------------------------------------------------------        
        sr.acquire()
        window, tslist = sr.get_window()    # window = [samples x channels]
        window = window.T                   # window = [channels x samples]
               
        # Check if proper real-time acquisition
        tsnew = np.where(np.array(tslist) > last_ts)[0]
        if len(tsnew) == 0:
            logger.warning('There seems to be delay in receiving data.')
            time.sleep(1)
            continue
    
        #----------------------------------------------------------------------
        # ADD YOUR CODE HERE
        #----------------------------------------------------------------------
        
    
        
        last_ts = tslist[-1]
        internal_timer.sleep_atleast(cfg.TIMER_SLEEP)

# ----------------------------------------------------------------------
def load_config(cfg_file):
    """
    Dynamic loading of a config file.
    Format the lib to fit the previous developed neurodecode code if subject specific file (not for the templates).
    cfg_file: tuple containing the path and the config file name.
    """
    cfg_file = os.path.split(cfg_file)
    sys.path.append(cfg_file[0])
    cfg_module = import_module(cfg_file[1].split('.')[0])

    return cfg_module

#----------------------------------------------------------------------
def batch_run(cfg_module):
    """
    For batch script
    """
    cfg = load_config(cfg_module)
    check_config(cfg)
    run(cfg)

#----------------------------------------------------------------------        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        cfg_module = input('Config module name? ')
    else:
        cfg_module = sys.argv[1]
    batch_run(cfg_module)
