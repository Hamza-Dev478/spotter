"""Request validation for the trip-planning endpoint."""

from rest_framework import serializers


class LogMetaSerializer(serializers.Serializer):
    """Optional, presentation-only fields shown on the daily log sheets."""

    carrierName = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    mainOfficeAddress = serializers.CharField(required=False, allow_blank=True, max_length=300, default="")
    vehicleNumbers = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    driverName = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    coDriverName = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    homeTimezone = serializers.CharField(required=False, allow_blank=True, max_length=60, default="")
    shippingDocNumber = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    shipperCommodity = serializers.CharField(required=False, allow_blank=True, max_length=300, default="")


class TripInputSerializer(serializers.Serializer):
    currentLocation = serializers.CharField(max_length=500, trim_whitespace=True)
    pickupLocation = serializers.CharField(max_length=500, trim_whitespace=True)
    dropoffLocation = serializers.CharField(max_length=500, trim_whitespace=True)
    currentCycleUsedHrs = serializers.FloatField(min_value=0, max_value=70)
    startTime = serializers.DateTimeField(required=False, allow_null=True)
    logMeta = LogMetaSerializer(required=False)

    def validate_currentLocation(self, value: str) -> str:
        return self._non_empty(value)

    def validate_pickupLocation(self, value: str) -> str:
        return self._non_empty(value)

    def validate_dropoffLocation(self, value: str) -> str:
        return self._non_empty(value)

    @staticmethod
    def _non_empty(value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("This field may not be blank.")
        return value
