"""
FPL Multi-GW Optimiser Package

This package provides tools for optimizing Fantasy Premier League squads
across multiple gameweeks using machine learning forecasting and 
mathematical optimization.
"""

__version__ = "0.1.0"
__author__ = "FPL Optimiser"

from .data_collection import FPLDataCollector
from .data_validation import FPLDataValidator

__all__ = [
    "FPLDataCollector",
    "FPLDataValidator"
]