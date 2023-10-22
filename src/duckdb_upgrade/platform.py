import enum
import platform
import sys

from typing import NamedTuple


class Platforms(enum.StrEnum):
    Linux = "linux"
    MacOS = "osx"
    Windows = "windows"


class Architectures(enum.StrEnum):
    AMD64 = "amd64"
    ARM64 = "aarch64"


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
    PlatformDetails(Platforms.Linux, Architectures.ARM64),
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

    if platform.machine() == "x86_64":
        current_arch = Architectures.AMD64
    elif platform.machine() == "arm64":
        current_arch = Architectures.ARM64
    else:
        raise InvalidPlatform()

    details = PlatformDetails(current_platform, current_arch)
    if details not in VALID_PLATFORMS:
        raise InvalidPlatform()

    return details
