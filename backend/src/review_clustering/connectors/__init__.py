"""
Connector Layer for External Review APIs.

This module provides connectors for fetching reviews from various external sources
such as Google Play Store, Apple App Store, and custom REST APIs.
"""

from .base_connector import BaseConnector, ReviewData, ConnectorConfig
from .google_play_connector import GooglePlayConnector
from .app_store_connector import AppStoreConnector
from .generic_api_connector import GenericAPIConnector

__all__ = [
    "BaseConnector",
    "ReviewData",
    "ConnectorConfig",
    "GooglePlayConnector",
    "AppStoreConnector",
    "GenericAPIConnector",
]
