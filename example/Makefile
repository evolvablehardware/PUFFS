# set up device specific params
DEVICE ?= up5k
BRAM   ?= implicit
PICO   ?= 1
ifeq ($(DEVICE), hx1k)
NUM_BLOCKS := 16
PNR_PARAMS := --hx1k --package tq144
CLOCK_SPEED := 5_000_000
PCF_FILE := constraints/hx1k.pcf
else ifeq ($(DEVICE), up5k)
NUM_BLOCKS := 30
PNR_PARAMS := --up5k --package sg48
CLOCK_SPEED := 5_000_000
USE_SPRAM := -D USE_SPRAM
ifeq ($(PICO), 1)
PCF_FILE := constraints/up5k_pico_ice.pcf
UF2_ARG := -DPICO_BOARD=pico_ice -DPICO_PLATFORM=rp2040
else ifeq ($(PICO), 2)
PCF_FILE := constraints/up5k_pico2_ice.pcf
UF2_ARG := -DPICO_BOARD=pico2_ice -DPICO_PLATFORM=rp2350
else
$(error Pico not supported. Use 1 or 2)
endif
else
$(error Device not supported. Use hx1k or up5k)
endif

# -------- Repo layout --------
GIT_ROOT := $(shell git rev-parse --show-toplevel)

BUILD_DIR  := $(GIT_ROOT)/src/intg/lattice/build

INTERNAL_RTL_DIR              := $(GIT_ROOT)/src/rtl
INTERNAL_LATTICE_INTG_RTL_DIR := $(GIT_ROOT)/src/intg/lattice/rtl

# -------- Frontend flags --------
INC_FLAGS  += -I$(INTERNAL_RTL_DIR) -I$(INTERNAL_LATTICE_INTG_RTL_DIR) -I$(EXTERNAL_RTL_DIR)
YOSYS_DEFS += -DSYNTHESIS=1

# ================================
# Define per-top source sets here
# ================================

SV_SRCS = $(wildcard $(INTERNAL_RTL_DIR)/*.sv) $(wildcard $(INTERNAL_LATTICE_INTG_RTL_DIR)/*.sv) $(wildcard $(INTERNAL_RTL_DIR)/*.v) $(wildcard $(INTERNAL_LATTICE_INTG_RTL_DIR)/*.v)

# From the new created v sources we need to create a hierarchy for them using vhier
V_SRCS = $(shell grep -ho "^\s*module [_a-zA-Z0-9]*" $(SV_SRCS) | sed 's/^\s*module \(.*\)/build\/vlog\/\1.v/' | xargs)

TARGETS = build/Top.bin
ASC_SRCS = $(TARGETS:%.bin=%.asc)
JSON_SRCS = $(ASC_SRCS:%.asc=%.json)
V_DEPS = $(JSON_SRCS:build/%.json=build/deps/%.d)

.PRECIOUS: $(V_DEPS) $(JSON_SRCS) $(ASC_SRCS)

all: $(TARGETS)

.PHONY: upload
upload:
	sudo dfu-util -d 1209:b1c0 --alt 0 --download build/Top.bin --reset

# Include generated dependencies
-include $(V_DEPS)

build/%.bin: build/%.asc
	icepack $< $@

build/%.asc: build/%.json $(PCF_FILE)
	nextpnr-ice40 -q $(PNR_PARAMS) --asc $@ --json $< --pcf $(PCF_FILE)

build/%.json: build/vlog/%.v
	yosys -p "read_verilog $(YOSYS_DEFS) $(shell cat build/deps/$*.d | sed 's/.*: //'); synth_ice40 -top $*; delete t:\$$print; opt_clean; write_json $@" | tee build.log | grep -i "warning\|error"

# Generate dependency file inline with vhier
build/deps/%.d: build/vlog/%.v
	mkdir -p $(BUILD_DIR)/deps
	echo "$(<:.v=.json): $(shell vhier --module-files build/vlog/* --top-module=$* | tr ' ' '\n' | sort -u | xargs)" > $@

$(V_SRCS): $(SV_SRCS) | $(BUILD_DIR)
	rm -rf $(BUILD_DIR)/vlog
	mkdir -p $(BUILD_DIR)/vlog
	$(GIT_ROOT)/tools/sv2v-Linux/sv2v --incdir="$(INTERNAL_RTL_DIR)" --write="$(BUILD_DIR)/vlog/" $(SV_SRCS)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

.PHONY: help
help:
	@echo "Usage:"
.PHONY: clean
clean:
	rm -rf $(BUILD_DIR)
