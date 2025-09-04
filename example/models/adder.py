# models/adder.py
import numpy as np

class Model:
    def __init__(self,
                 numInputs,
                 inData,
                 outData,
                 weights=None,            # unused (kept for API parity)
                 bias=None,               # unused
                 timeConstantStep=None,   # unused
                 initialPosition=None,    # unused
                 sigmoid=None,            # unused
                 log=None):
        # Parameters (kept for parity with your neuron model)
        self.numInputs = numInputs

        # Channels
        self.inData = inData         # list[Channel] or single Channel
        self.outData = outData

        # Internal state (none needed for pure adder)
        self.log = log

        # Optional mask if your dtype exposes one (for WIDTH wrap)
        self._mask = None
        try:
            self._mask = getattr(getattr(self.outData, "dtype", None), "mask", None)
        except Exception:
            self._mask = None

    def _ready_inputs(self):
        """Return True if all required input channels have a valid token this cycle."""
        if isinstance(self.inData, list):
            return all(ch.isValid() for ch in self.inData)
        else:
            return self.inData.isValid()

    def _recv_inputs(self):
        """Receive and return a numpy array of inputs."""
        if isinstance(self.inData, list):
            vals = np.asarray([ch.recv() for ch in self.inData])
        else:
            v = self.inData.recv()
            # allow scalar or vector from a single channel
            vals = np.asarray(v if isinstance(v, (list, tuple, np.ndarray)) else [v])
        return vals

    def cycle(self):
        # Wait until all inputs have a token
        if not self._ready_inputs():
            return

        inputs = self._recv_inputs()

        if self.log is not None:
            self.log.check(
                inputs.shape[0] == self.numInputs,
                f"Expected {self.numInputs} inData, found {inputs.shape[0]}"
            )

        total = int(np.sum(inputs))

        # Apply optional mask to emulate DUT WIDTH wrap if dtype provides one
        if self._mask is not None:
            total &= self._mask

        # Send result; Channel/dtype handles encoding/wrapping as needed
        self.outData.send(total)
