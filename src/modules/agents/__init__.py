REGISTRY = {}

from .qmix_agent import QMIXRNNAgent, FFAgent
from .rnn_agent import RNNAgent
REGISTRY["rnn"] = RNNAgent
REGISTRY["qmixrnn"] = QMIXRNNAgent
REGISTRY["ff"] = FFAgent