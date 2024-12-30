# Makefile

# defaults
SIM ?= nvc
TOPLEVEL_LANG ?= vhdl
GUI = 1
SCRIPT_FILE =

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = power_detector

# MODULE is the basename of the Python test file
MODULE = pwrdet


ifeq ($(SIM),ghdl)
	COMPILE_ARGS = --std=08
	EXTRA_ARGS = --std=08
	SIM_ARGS = --wave=$(TOPLEVEL).ghw
endif

ifeq ($(SIM),nvc)
	SIM_ARGS = --wave=$(TOPLEVEL).ghw
endif

SRC = ../src
SRC_EMA = ../../lowpass_ema/src 

# use VHDL_SOURCES for VHDL files
VHDL_SOURCES += ../../lowpass_ema/src/lowpass_ema.vhd \
				$(SRC)/power_detector.vhd


# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
