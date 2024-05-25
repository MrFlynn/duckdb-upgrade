import platform
import sys

from enum import Enum, auto
from typing import NamedTuple


class Platforms(Enum):
    Linux = auto()
    MacOS = auto()
    Windows = auto()

    def __str__(self) -> str:
        if self == self.MacOS:
            return "osx"

        return self.name.lower()


class Architectures(Enum):
    AMD64 = auto()
    ARM64 = auto()

    def __str__(self) -> str:
        if self == self.ARM64:
            return "aarch64"

        return self.name.lower()


class PlatformDetails(NamedTuple):
    Platform: Platforms
    Arch: Architectures

    def get_arch(self) -> str:
        if self.Platform == Platforms.MacOS:
            return "universal"
        else:
            return str(self.Arch)


class InvalidPlatform(Exception):
    def __init__(self) -> None:
        super().__init__()

        self.platform = sys.platform
        self.arch = platform.machine()

    def __str__(self) -> str:
        return f"Combination of {self.platform} and {self.arch} are not supported by DuckDB"


VALID_PLATFORMS = {
    PlatformDetails(Platforms.Linux, Architectures.AMD64),
    PlatformDetails(Platforms.Linux, Architectures.ARM64),
    PlatformDetails(Platforms.MacOS, Architectures.AMD64),
    PlatformDetails(Platforms.MacOS, Architectures.ARM64),
    PlatformDetails(Platforms.Windows, Architectures.AMD64),
}


def get_platform_details() -> PlatformDetails:
    current_platform, current_arch = Platforms.Linux, Architectures.AMD64

    if sys.platform.startswith("linux"):
        current_platform = Platforms.Linux
    elif sys.platform.startswith("darwin"):
        current_platform = Platforms.MacOS
    elif sys.platform.startswith("win"):
        current_platform = Platforms.Windows
    else:
        raise InvalidPlatform()

    arch = platform.machine().lower()
    if arch == "x86_64" or arch == "amd64":
        current_arch = Architectures.AMD64
    elif arch == "arm64" or arch == "aarch64":
        current_arch = Architectures.ARM64
    else:
        raise InvalidPlatform()

    details = PlatformDetails(current_platform, current_arch)
    if details not in VALID_PLATFORMS:
        raise InvalidPlatform()

    return details
