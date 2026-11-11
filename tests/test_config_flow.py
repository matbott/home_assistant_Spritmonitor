"""Tests for the setup form (config flow)."""
from unittest.mock import patch

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.spritmonitor.config_flow import normalize_bearer_token
from custom_components.spritmonitor.const import (
    API_VEHICLES_URL,
    CONF_BEARER_TOKEN,
    CONF_CURRENCY,
    DEFAULT_APP_TOKEN,
    DOMAIN,
    TOKEN_URL,
)

from .conftest import ENTRY_DATA, VEHICLE, make_entry

USER_INPUT = {**ENTRY_DATA}


@pytest.fixture
def bypass_setup():
    """Don't set the entry up after the flow - that is covered by test_init."""
    with patch("custom_components.spritmonitor.async_setup_entry", return_value=True) as mock_setup:
        yield mock_setup


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("abc123", "Bearer abc123"),
        ("  abc123  ", "Bearer abc123"),
        ("Bearer abc123", "Bearer abc123"),
        ("bearer abc123", "bearer abc123"),
    ],
)
def test_normalize_bearer_token(token, expected):
    assert normalize_bearer_token(token) == expected


async def test_form_defaults(hass):
    hass.config.currency = "GBP"
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["description_placeholders"] == {"token_url": TOKEN_URL}

    defaults = {str(key): key.default() for key in result["data_schema"].schema if callable(getattr(key, "default", None))}
    assert defaults[CONF_CURRENCY] == "GBP"
    assert defaults["app_token"] == DEFAULT_APP_TOKEN


async def test_create_entry_adds_bearer_prefix(hass, aioclient_mock, bypass_setup):
    aioclient_mock.get(API_VEHICLES_URL, json=[VEHICLE])
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data={**USER_INPUT, CONF_BEARER_TOKEN: "raw-token"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "VW Golf"
    assert result["data"][CONF_BEARER_TOKEN] == "Bearer raw-token"
    assert result["result"].unique_id == "spritmonitor_100001"
    # The normalised token is the one sent to Spritmonitor
    assert aioclient_mock.mock_calls[0][3]["Authorization"] == "Bearer raw-token"


async def test_title_falls_back_to_vehicle_id(hass, aioclient_mock, bypass_setup):
    aioclient_mock.get(API_VEHICLES_URL, json=[{**VEHICLE, "make": "", "model": ""}])
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["title"] == "Spritmonitor Vehicle 100001"


async def test_unknown_vehicle_shows_invalid_auth(hass, aioclient_mock):
    aioclient_mock.get(API_VEHICLES_URL, json=[{**VEHICLE, "id": 1}])
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.parametrize("exc", [aiohttp.ClientError(), ValueError()])
async def test_connection_problems_show_cannot_connect(hass, aioclient_mock, exc):
    aioclient_mock.get(API_VEHICLES_URL, exc=exc)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_rejected_token_shows_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get(API_VEHICLES_URL, status=401)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["errors"] == {"base": "cannot_connect"}


async def test_same_vehicle_twice_is_aborted(hass, aioclient_mock, bypass_setup):
    make_entry().add_to_hass(hass)
    aioclient_mock.get(API_VEHICLES_URL, json=[VEHICLE])
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}, data=USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
