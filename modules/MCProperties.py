import datetime
import os

class Properties(dict):
    def __init__(self, path: str):
        super().__init__()
        self.path = path

        if not os.path.exists(self.path):
            raise FileNotFoundError

        with open(self.path, "r") as file:
            for line in file:
                if line.startswith("#"):
                    continue
                splitted = line.split("=")
                self[splitted[0]] = splitted[1].replace("\n", "")

    def __str__(self):
        copy = {}
        for key, value in self.copy().items():
            if key.startswith("#"):
                continue
            copy[key] = value.replace("\n", "")
        return str(copy)

    def getValue(self, key: str):
        return str(self.get(key))

    def setValue(self, SelectedKey: str, NewValue: str):
        self[SelectedKey] = NewValue
        return self[SelectedKey]

    def RemoveValue(self, SelectedKey: str, ValueToDelete):
        for key, value in self.items():
            if SelectedKey in self:
                if ValueToDelete in self[SelectedKey]:
                    self[key].replace(ValueToDelete, "")
                    return self[key]

    def save(self):
        with open(self.path, "w") as file:
            file.write("#Minecraft server properties\n")
            file.write(f"#{datetime.datetime.now().astimezone().strftime('%a %b %d %H:%M:%S %Z %Y')}\n")
            for line in self:
                file.write(line + "=" + self[line] + "\n")
        return True
