"""Digital Twin package – core state representations for stations.

Each twin module provides a simple dataclass / Pydantic model with deterministic
calculations. The twins are independent from the API layer; they are updated by
`services.digital_twin_service` when new telemetry arrives.
"""
