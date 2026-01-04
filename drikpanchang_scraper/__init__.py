"""
Navagraha (9-planet) gochar computation using Skyfield.

Public API:
  - SkyFieldEphemerisEngine.compute_all_planets(): Compute all planets (1900-2025)
  - SkyFieldEphemerisEngine.find_transition_times(): Compute specific planet
  - SkyFieldEphemerisEngine.get_planet_longitude(): Get position for a date
"""

__version__ = "2.0.0"
__author__ = "Prakash Kantumutchu"

# Only import Skyfield-based engine (no C++ dependencies)
try:
    from .ephemeris_skyfield import SkyFieldEphemerisEngine
    __all__ = ['SkyFieldEphemerisEngine']
except ImportError as e:
    print(f"Error importing Skyfield engine: {e}")
    print("Install skyfield: pip install skyfield")
    raise
