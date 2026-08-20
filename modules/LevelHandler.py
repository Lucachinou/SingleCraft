import nbtlib

def get_enabled_features(file_path: str):
    file = nbtlib.load(file_path)
    return file.get("Data").get("enabled_features")

def add_enabled_features(file_path: str, feature: str):
    with nbtlib.load(file_path) as file:
        if file.get("Data").get("enabled_features") and feature not in file.get("Data").get("enabled_features"):
            file["enabled_features"].append(feature)
        if file.get("Data").get("DataPacks"):
            if file.get("Data").get("DataPacks").get("Disabled") and feature in file.get("Data").get("DataPacks").get("Disabled"):
                file["DataPacks"]["Disabled"].remove(feature)
            if file.get("Data").get("DataPacks").get("Enabled") and feature not in file.get("Data").get("DataPacks").get("Enabled"):
                file["DataPacks"]["Enabled"].append(feature)
    return True

def remove_enabled_features(file_path: str, feature: str):
    with nbtlib.load(file_path) as file:
        if file.get("Data").get("enabled_features") and feature in file.get("Data").get("enabled_features"):
            file["enabled_features"].remove(feature)
        if file.get("Data").get("DataPacks"):
            if file.get("Data").get("DataPacks").get("Disabled") and feature not in file.get("Data").get("DataPacks").get("Disabled"):
                file["DataPacks"]["Disabled"].append(feature)
            if file.get("Data").get("DataPacks").get("Enabled") and feature in file.get("Data").get("DataPacks").get("Enabled"):
                file["DataPacks"]["Enabled"].remove(feature)
        else:
            return False
    return True

def get_enabled_datapacks(file_path: str):
    with nbtlib.load(file_path) as file:
        if file.get("Data").get("DataPacks"):
            return file.get("Data").get("DataPacks").get("Enabled")
    return False

def get_disabled_datapacks(file_path: str):
    with nbtlib.load(file_path) as file:
        if file.get("Data").get("DataPacks"):
            return file.get("Data").get("DataPacks").get("Disabled")
    return False

def get_all_datapacks(file_path: str):
    enabled = get_enabled_datapacks(file_path)
    disabled = get_disabled_datapacks(file_path)
    return enabled, disabled
