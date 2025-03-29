import json

ADD_PHONE_COMMAND = "add_phone"
REMOVE_PHONE_COMMAND = "remove_phone"

PHONE_COMMANDS_PATH = "configs/phone_commands.json"
SETTINGS_PATH = "configs/barrier_settings.json"


def load_phone_commands():
    with open(PHONE_COMMANDS_PATH) as f:
        return json.load(f)


def load_barrier_settings():
    with open(SETTINGS_PATH) as f:
        return json.load(f)


def get_phone_commands_for_device(device_type: str):
    all_commands = load_phone_commands()
    return all_commands.get(device_type, {}).get("commands", [])


def get_settings_for_device(device_type: str):
    all_settings = load_barrier_settings()
    return all_settings.get(device_type, {}).get("settings", [])


def find_phone_command_by_name(device_type: str, name: str):
    commands = get_phone_commands_for_device(device_type)
    return next((cmd for cmd in commands if cmd["name"] == name), None)


def find_setting_by_key(device_type: str, key: str):
    settings = get_settings_for_device(device_type)
    return next((s for s in settings if s["key"] == key), None)

def build_message(template: str, params: dict) -> str:
    try:
        return template.format(**params)
    except KeyError as e:
        raise ValueError(f"Missing parameter for template: {e}")
