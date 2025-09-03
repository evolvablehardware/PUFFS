# PUFFS
**P**ytest **U**nit **F**ramework for **F**PGA **S**imulation  

## Features
- **Pytest integration** — write and run tests like any Python project
- **Cocotb power** — simulate Verilog/SystemVerilog designs with Python
- **Channels** - Channel Level Source and Syncs for Testbenches in Python

## Example Overview

### Models
``` shell
src/models
```
This directory contains your python gold models for your RTL this also contains various abstractions for interacting with models in python such as channels

### Unit Tests
``` shell
src/unit
```
This directory contains your various unit tests for your RTL

## RTL
``` shell
src/rtl
```
This directory contains your verilog or system verilog files to be tested. See adder example  

