# tests/test_adder.py
import cocotb
from cocotb.triggers import RisingEdge
from cocotb.clock import Clock

import numpy as np
import matplotlib.pyplot as plt

import pytest
import random

from puffs import test
from puffs import fixed
from puffs import channel

from models import adder
# ---------------------------
# Cocotb test
# ---------------------------
@cocotb.test()
async def adder_randomInput(dut):
    params = test.Params()
    log = test.Logger()

    # Seed logging
    seed = random.randint(-1_000_000_000, 1_000_000_000)
    log.info(f"seed={seed}")
    random.seed(seed)

    # Use pure integer dtype for an integer adder (no fixed-point)
    dtype = channel.Int()

    # Random input token generators (unsigned WIDTH-bit range)
    max_val = (1 << params.WIDTH) - 1
    A_tokens_src = channel.RandomInt((0, max_val))
    B_tokens_src = channel.RandomInt((0, max_val))

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    # Wrap DUT ports with Channels
    A = channel.Channel("A", dut.A_valid, dut.A_ready, dut.A_data, dtype=dtype)
    B = channel.Channel("B", dut.B_valid, dut.B_ready, dut.B_data, dtype=dtype)
    S = channel.Channel("S", dut.S_valid, dut.S_ready, dut.S_data, dtype=dtype)

    # Environment
    srcA = channel.Source(A, values=A_tokens_src, log=log)
    srcB = channel.Source(B, values=B_tokens_src, log=log)
    sinkS = channel.Sink(S, log=log)

    dutS_vals = []

    # Run N cycles
    N = 600
    for _ in range(N):
        # Per-cycle stimulus
        srcA.cycle()
        srcB.cycle()

        # Sink cycle (captures DUT outputs)
        sinkS.cycle()

        await RisingEdge(dut.clk)

        # Capture DUT value if handshake
        valid = sinkS.chan.valid.value.integer
        ready = sinkS.currReady
        if valid == 1 and ready == 1:
            dutS_vals.append(dtype.read(dut.S_data))

    # Build expected from the actual input tokens that handshook
    sent_A = srcA.chan.tokens
    sent_B = srcB.chan.tokens
    expected = [ (a + b) & max_val for a, b in zip(sent_A, sent_B) ]

    # Align lengths in case of backpressure skew
    L = min(len(expected), len(dutS_vals))
    expected = expected[:L]
    dutS_vals = dutS_vals[:L]

    # Assertions
    try:
        np.testing.assert_array_equal(dutS_vals, expected)
        log.info(f"PASS: {L} outputs matched expected sums (WIDTH={params.WIDTH}).")
    except AssertionError as e:
        log.error("Mismatch between DUT output and expected sums.")
        log.error(str(e))
        assert False

    # ---------------------------
    # Plots
    # ---------------------------
    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    # Inputs
    axs[0].plot(sent_A, label='A', marker='o')
    axs[0].plot(sent_B, label='B', marker='x')
    axs[0].set_title("Adder Inputs")
    axs[0].set_ylabel(f"Value (WIDTH={params.WIDTH})")
    axs[0].legend()
    axs[0].grid(True)

    # Output
    axs[1].plot(dutS_vals, label='Verilog DUT', marker='o')
    axs[1].plot(expected, label='Expected A+B', marker='x')
    axs[1].set_title("Adder Output")
    axs[1].set_ylabel("Sum")
    axs[1].legend()
    axs[1].grid(True)

    # Handshake trace
    axs[2].plot([len(sent_A[:i]) for i in range(1, len(sent_A)+1)],
                label='A tokens sent')
    axs[2].plot([len(sent_B[:i]) for i in range(1, len(sent_B)+1)],
                label='B tokens sent')
    axs[2].plot([len(dutS_vals[:i]) for i in range(1, len(dutS_vals)+1)],
                label='S tokens received')
    axs[2].set_title("Handshake Progress")
    axs[2].set_xlabel("Step")
    axs[2].set_ylabel("Cumulative tokens")
    axs[2].legend()
    axs[2].grid(True)

    plt.tight_layout()
    plt.savefig("adder_plot.png", dpi=300)
    plt.close()

    log.done()


# ---------------------------
# Pytest harness
# ---------------------------
@pytest.mark.parametrize("WIDTH", [8, 12, 16])
def test_adder(WIDTH):
    tb = test.Bench("adder", "adder_randomInput")
    tb.source("rtl/adder.v")
    tb.param({"WIDTH": WIDTH})
    tb.run()


if __name__ == "__main__":
    test_adder(8)
