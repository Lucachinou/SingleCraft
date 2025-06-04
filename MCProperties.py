import os

class Properties(list):
    def __init__(self, path: str):
        super().__init__()
        self.path = path

        if not os.path.exists(self.path):
            raise FileNotFoundError

        with open(self.path, "r") as file:
            for line in file:
                self.append(line.replace("\n", ""))

    def __str__(self):
        copy = []
        for line in self.copy():
            if line.startswith("#"):
                continue
            copy.append(line)
        return str(copy)

    def getValue(self, index: int):
        index = index + 2
        return str(self[index].split("=")[1])

    def getTitle(self, index: int):
        index = index + 2
        return str(self[index].split("=")[0])

    def setValue(self, index: int, value):
        if value is True:
            value = str("true")
        elif value is False:
            value = str("false")
        index = index + 2
        newindex = f"{self[index].split("=")[0]}={str(value)}"
        self[index] = newindex
        return True

    def RemoveValue(self, index: int, value: str):
        index = index + 2
        parts = self[index].split("=")
        elements = parts[1].split(", ")
        elements.remove(value)
        elementsWithoutValue = ", ".join(elements)
        self[index] = parts[0] + "=" + elementsWithoutValue
        return str(parts[0] + "=" + elementsWithoutValue)

    def save(self):
        with open(self.path, "w") as file:
            for line in self:
                file.write(line + "\n")
        return True
