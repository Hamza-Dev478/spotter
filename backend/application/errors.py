"""Application-level errors raised by external-service adapters.

The DRF view layer maps these to HTTP status codes; nothing here knows about
HTTP, keeping the dependency arrow pointing inward.
"""


class GeocodingError(Exception):
    """An address could not be resolved to coordinates."""


class RoutingError(Exception):
    """A drivable route could not be computed between two points."""


class ProviderUnavailable(Exception):
    """An upstream provider (OSRM / Nominatim) failed or timed out."""
