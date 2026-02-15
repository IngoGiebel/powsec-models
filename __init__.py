"""
powsec-models — Proof-of-Work Security Models
===============================================

Quantitative models for analyzing Bitcoin's proof-of-work security layer.

Modules
-------
miner_stress
    Miner capitulation probability and network security stress testing.
content_pollution
    Blockchain content pollution probability and saturation modeling.
hashrate_concentration
    Mining pool concentration, censorship resistance scoring.
institutional_exit
    ETF/institutional compliance triggers and exit cascade simulation.
"""

__version__ = "0.2.0"
__author__ = "Ingo Giebel"

from . import miner_stress
from . import content_pollution
from . import hashrate_concentration
from . import institutional_exit
