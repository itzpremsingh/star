class IntConverter:
    regex = r"\d+"

    @staticmethod
    def convert(value: str) -> int:
        return int(value)


class StringConverter:
    regex = r"[^/]+"

    @staticmethod
    def convert(value: str) -> str:
        return value


class FloatConverter:
    regex = r"\d+\.\d+"

    @staticmethod
    def convert(value: str) -> float:
        return float(value)


converters = {
    "int": IntConverter,
    "string": StringConverter,
    "float": FloatConverter,
}
