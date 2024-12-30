#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#--  _______                             ________                                            ______
#--  __  __ \________ _____ _______      ___  __ \_____ _____________ ______ ___________________  /_
#--  _  / / /___  __ \_  _ \__  __ \     __  /_/ /_  _ \__  ___/_  _ \_  __ `/__  ___/_  ___/__  __ \
#--  / /_/ / __  /_/ //  __/_  / / /     _  _, _/ /  __/_(__  ) /  __// /_/ / _  /    / /__  _  / / /
#--  \____/  _  .___/ \___/ /_/ /_/      /_/ |_|  \___/ /____/  \___/ \__,_/  /_/     \___/  /_/ /_/
#--          /_/
#--                   ________                _____ _____ _____         _____
#--                   ____  _/_______ __________  /____(_)__  /_____  ____  /______
#--                    __  /  __  __ \__  ___/_  __/__  / _  __/_  / / /_  __/_  _ \
#--                   __/ /   _  / / /_(__  ) / /_  _  /  / /_  / /_/ / / /_  /  __/
#--                   /___/   /_/ /_/ /____/  \__/  /_/   \__/  \__,_/  \__/  \___/
#--
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#-- Copyright
#------------------------------------------------------------------------------------------------------
#--
#-- Copyright 2024 by M. Wishek <matthew@wishek.com>
#--
#------------------------------------------------------------------------------------------------------
#-- License
#------------------------------------------------------------------------------------------------------
#--
#-- This source describes Open Hardware and is licensed under the CERN-OHL-W v2.
#--
#-- You may redistribute and modify this source and make products using it under
#-- the terms of the CERN-OHL-W v2 (https://ohwr.org/cern_ohl_w_v2.txt).
#--
#-- This source is distributed WITHOUT ANY EXPRESS OR IMPLIED WARRANTY, INCLUDING
#-- OF MERCHANTABILITY, SATISFACTORY QUALITY AND FITNESS FOR A PARTICULAR PURPOSE.
#-- Please see the CERN-OHL-W v2 for applicable conditions.
#--
#-- Source location: TBD
#--
#-- As per CERN-OHL-W v2 section 4.1, should You produce hardware based on this
#-- source, You must maintain the Source Location visible on the external case of
#-- the products you make using this source.
#--
#------------------------------------------------------------------------------------------------------
#-- Description
#------------------------------------------------------------------------------------------------------
#--
#-- This file implements a Cocotb based Python testbench for testing the MSK Modem
#--
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------------------------
#         __   __   __  ___  __ 
# | |\/| |__) /  \ |__)  |  (_  
# | |  | |    \__/ | \   |  __) 
#                               
#------------------------------------------------------------------------------------------------------
import cocotb
from cocotb.triggers import Timer, RisingEdge
from cocotb.clock    import Clock
from cocotb.utils    import get_sim_time

import math
import random
import numpy as np 
import matplotlib.pyplot as plt
import sys
import inspect

#------------------------------------------------------------------------------------------------------
#  __       __  ___    __            __ ___    __        __ 
# |__) |   /  \  |    |_  /  \ |\ | /    |  | /  \ |\ | (_  
# |    |__ \__/  |    |   \__/ | \| \__  |  | \__/ | \| __) 
#                                                           
#------------------------------------------------------------------------------------------------------

def fftPlot(sig, dt=None, plot=True):
    # Here it's assumes analytic signal (real signal...) - so only half of the axis is required

    if dt is None:
        dt = 1
        t = np.arange(0, sig.shape[-1])
        xLabel = 'samples'
    else:
        t = np.arange(0, sig.shape[-1]) * dt
        xLabel = 'freq [Hz]'

    if sig.shape[0] % 2 != 0:
        warnings.warn("signal preferred to be even in size, autoFixing it...")
        t = t[0:-1]
        sig = sig[0:-1]

    sigFFT = np.fft.fft(sig) / t.shape[0]  # Divided by size t for coherent magnitude

    freq = np.fft.fftfreq(t.shape[0], d=dt)

    # Plot analytic signal - right half of frequence axis needed only...
    firstNegInd = np.argmax(freq < 0)
    freqAxisPos = freq[0:firstNegInd]
    sigFFTPos = 2 * sigFFT[0:firstNegInd]  # *2 because of magnitude of analytic signal

    if plot:
        plt.figure()
        plt.plot(freqAxisPos, np.abs(sigFFTPos))
        plt.xlabel(xLabel)
        plt.ylabel('mag')
        plt.title('Analytic FFT plot')
        plt.show()

    return sigFFTPos, freqAxisPos


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------

class sin_cos:

    def __init__(self, dut, sample_period, freq):

        self.dut = dut
        self.freq = freq
        self.sample_period = sample_period
        self.run = False

    async def sin_cos(self):

        self.dut._log.info("signal generator - waiting for start...")
        print(self.sample_period)

        t = 0
        self.dut.data_ena.value = 0

        while self.run == False:
            await RisingEdge(self.dut.clk)

        self.dut._log.info("signal generator - starting...")

        while self.run:

            await RisingEdge(self.dut.clk)

            I_sample = int(round(2047*np.cos(2*np.pi*self.freq/2*t/1e12)))
            Q_sample = int(round(2047*np.sin(2*np.pi*self.freq/2*t/1e12)))

            # print("%d %d" % (I_sample, Q_sample))
            # print(2*np.pi*self.freq/2*t/1e12)
            # print(t)
            # print(t/1e12)
            self.dut.data_I.value = I_sample
            self.dut.data_Q.value = Q_sample
            self.dut.data_ena.value = 1

            t += self.sample_period

        self.dut._log.info("...signal generator - done.")




#------------------------------------------------------------------------------------------------------
#       __                             ___          
# |\/| (_  |_/   |\/|  _   _|  _  _     |   _  _ |_ 
# |  | __) | \   |  | (_) (_| (- |||    |  (- _) |_ 
#                                                   
#------------------------------------------------------------------------------------------------------

@cocotb.test()
async def pwrdet_sin_cos_test(dut):

    plot = False

    run_time = 100000 # microseconds

    alpha = 0.1

    clock_freq = 1.25e6
    clock_per = int(round(1/(clock_freq)*1e9))

    rt_freq = 433000 

    dut.alpha.value = 1
    dut.init.value = 1
    dut.data_I.value = 0
    dut.data_Q.value = 0
    dut.data_ena.value = 0

    sig = sin_cos(dut, clock_per, rt_freq)

    await cocotb.start(Clock(dut.clk, clock_per, units="ns").start())
    await cocotb.start(sig.sin_cos())

    await RisingEdge(dut.clk)
    dut.init.value = 0
    await RisingEdge(dut.clk)

    sig.run = True

    await Timer(run_time, "us")

    await RisingEdge(dut.clk)

    sig.run = False

    # tx_time         = msksim.time

    # tx_samples_if_arr   = np.array(msksim.tx_samples_I_arr,  dtype=complex)
    # tx_samples_if_cmplx = np.array(msksim.tx_samples_I_arr,  dtype=complex) - 1j * np.array(msksim.tx_samples_Q_arr, dtype=complex)
    # tx_samples_fc_cmplx = np.array(ducsim.tx_samples_I_up,   dtype=complex) - 1j * np.array(ducsim.tx_samples_Q_up,  dtype=complex)
    # tx_samples_fc_real  = np.array(ducsim.tx_samples_IQ_mod, dtype=int)
    # rx_samples_rx_real  = np.array(ddcsim.rx_samples_I_dn,   dtype=int)
    # rx_samples_rx_cmplx = np.array(ddcsim.rx_samples_I_dn,   dtype=complex) - 1j * np.array(ddcsim.rx_samples_Q_dn,  dtype=complex)
    # rx_samples_rx_dec   = np.array(msksim.rx_samples_arr,    dtype=int)
    #tx_samples_2   = tx_samples_arr * tx_samples_arr

    # print("Ones: ", pn.ones_count)
    # print("Zeros: ", pn.zeros_count)

    # errs = await regs.read("msk_top_regs", "PRBS_Error_Count")
    # print("Bit errors: ", errs)
    # bits = await regs.read("msk_top_regs", "PRBS_Bit_Count")
    # print("Bit count:  ", bits)
    # print("BER:        ", (1.0*errs)/bits)

    # # print("Bit errors: ", pn.err_count)
    # # print("Bit count:  ", pn.data_count)
    # # print("BER:        ", pn.err_count/pn.data_count)

    if plot:
        blackman_window = np.blackman(len(tx_samples))
    
        fig = plt.figure(figsize=(10, 7), layout='constrained')
        axs = fig.subplot_mosaic([ #["signal", "signal"],
                                   #["magnitude", "log_magnitude"],
                                   ["psd_if_real", "psd_if_real"], 
                                   ["psd_if_cmplx", "psd_if_cmplx"],
                                   ["psd_fc_cmplx", "psd_fc_cmplx"],
                                   ["psd_fc_real", "psd_fc_real"],
                                   ["psd_rx_cmplx", "psd_rx_cmplx"],
                                   ["psd_rx_real", "psd_rx_real"],
                                   ["psd_rx_dec", "psd_rx_dec"]], sharex=True)
        
        # plot time signal:
        # axs["signal"].set_title("MSK Tx Samples")
        # axs["signal"].plot(tx_time, tx_samples_if_arr, color='C0')
        # axs["signal"].set_xlabel("Time (s)")
        # axs["signal"].set_ylabel("Amplitude")
        
        # plot different spectrum types:
        # axs["magnitude"].set_title("Magnitude Spectrum Squared")
        # axs["magnitude"].magnitude_spectrum(tx_samples_2, Fs=tx_sample_rate, window=blackman_window, color='C1')
        
        # axs["log_magnitude"].set_title("Log. Magnitude Spectrum Squared")
        # axs["log_magnitude"].magnitude_spectrum(tx_samples_2, Fs=tx_sample_rate, scale='dB', window=blackman_window, color='C1')
        
        axs["psd_if_real"].set_title("Power Spectral Density - IF - Real - I")
        axs["psd_if_real"].psd(tx_samples_if_arr, Fs=tx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')
  
        axs["psd_if_cmplx"].set_title("Power Spectral Density - IF - Complex - I + jQ")
        axs["psd_if_cmplx"].psd(tx_samples_if_cmplx, Fs=tx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')
          
        axs["psd_fc_cmplx"].set_title("Power Spectral Density - Fc - Complex - I + jQ")
        axs["psd_fc_cmplx"].psd(tx_samples_fc_cmplx, Fs=tx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')

        axs["psd_fc_real"].set_title("Power Spectral Density - Fc - Real - I + Q")
        axs["psd_fc_real"].psd(tx_samples_fc_real, Fs=tx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')

        axs["psd_rx_cmplx"].set_title("Power Spectral Density - Rx - Complex - I + jQ")
        axs["psd_rx_cmplx"].psd(rx_samples_rx_cmplx, Fs=tx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')

        axs["psd_rx_real"].set_title("Power Spectral Density - Rx - Real - I")
        axs["psd_rx_real"].psd(rx_samples_rx_real, Fs=tx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')

        axs["psd_rx_dec"].set_title("Power Spectral Density - Rx - Real - Sample Discard")
        axs["psd_rx_dec"].psd(rx_samples_rx_dec, Fs=rx_sample_rate, window=np.blackman(FFT), NFFT=FFT, color='C2', sides='twosided')

        plt.show()
    
        #fftPlot(np.asarray(tx_samples), dt=1/sample_rate)
