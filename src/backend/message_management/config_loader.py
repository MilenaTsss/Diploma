import json
import logging
import os

from message_management.enums import PhoneCommand

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PHONE_COMMANDS_PATH = os.path.join(BASE_DIR, "configs", "phone_commands.json")
SETTINGS_PATH = os.path.join(BASE_DIR, "configs", "barrier_settings.json")

logger = logging.getLogger(__name__)


def load_phone_commands():
    with open(PHONE_COMMANDS_PATH) as f:
        return json.load(f)


def get_phone_command(device_model: str, command: PhoneCommand) -> dict:
    commands = load_phone_commands()
    model_commands = commands.get(device_model)
    if not model_commands:
        raise ValueError(f"No phone commands defined for device model: {device_model}")

    cmd = model_commands.get(command.value)
    if not cmd:
        raise ValueError(f"Command '{command.value}' not found for model '{device_model}'")

    return cmd


def load_barrier_settings():
    with open(SETTINGS_PATH) as f:
        return json.load(f)


def get_setting(device_model: str, key: str) -> dict:
    settings = load_barrier_settings()

    if not settings:
        raise ValueError("No settings defined.")
    model_settings = settings.get(device_model)
    if not model_settings:
        raise ValueError(f"No settings defined for device model: {device_model}.")
    print(model_settings)

    setting = model_settings.get(key)
    if not setting:
        raise ValueError(f"Setting '{key}' not found for model '{device_model}'")

    return setting


def build_message(template: str, params: dict) -> str:
    try:
        return template.format(**params)
    except KeyError as e:
        raise ValueError(f"Missing parameter for template: {e}")
