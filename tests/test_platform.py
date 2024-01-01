import itertools
import platform as plt
import pytest
import sys

from src.duckdb_upgrade import platform
from typing import Callable, NamedTuple, Optional


def test_platforms_str() -> None:
    class Test(NamedTuple):
        Platform: platform.Platforms
        Result: str

    tests = [
        Test(Platform=platform.Platforms.Linux, Result="linux"),
        Test(Platform=platform.Platforms.MacOS, Result="osx"),
        Test(Platform=platform.Platforms.Windows, Result="windows"),
    ]

    for test in tests:
        assert str(test.Platform) == test.Result


def test_architectures_str() -> None:
    class Test(NamedTuple):
        Architecture: platform.Architectures
        Result: str

    tests = [
        Test(Architecture=platform.Architectures.AMD64, Result="amd64"),
        Test(Architecture=platform.Architectures.ARM64, Result="aarch64"),
    ]

    for test in tests:
        assert str(test.Architecture) == test.Result


def test_platform_details_get_arch() -> None:
    class Test(NamedTuple):
        PlatformDetail: platform.PlatformDetails
        Result: str

    tests = [
        Test(PlatformDetail=platform.PlatformDetails(Platform=p, Arch=a), Result=str(a))
        for p, a in itertools.product(
            [platform.Platforms.Linux, platform.Platforms.Windows],
            [platform.Architectures.AMD64, platform.Architectures.ARM64],
        )
    ] + [
        Test(
            PlatformDetail=platform.PlatformDetails(
                Platform=platform.Platforms.MacOS, Arch=platform.Architectures.AMD64
            ),
            Result="universal",
        ),
        Test(
            PlatformDetail=platform.PlatformDetails(
                Platform=platform.Platforms.MacOS, Arch=platform.Architectures.ARM64
            ),
            Result="universal",
        ),
    ]

    for test in tests:
        assert test.PlatformDetail.get_arch() == test.Result


def test_invalid_platform_str() -> None:
    assert (
        str(platform.InvalidPlatform())
        == f"Combination of {sys.platform} and {plt.machine()} are not supported by DuckDB"
    )


def test_get_platform_details(monkeypatch: pytest.MonkeyPatch) -> None:
    class Test(NamedTuple):
        Result: Optional[platform.PlatformDetails]
        SysPlatformPatchValue: str
        MachinePatchFunc: Callable[[], str]
        ShouldAssert: bool

    tests = [
        Test(
            Result=platform.PlatformDetails(
                Platform=platform.Platforms.Linux,
                Arch=platform.Architectures.AMD64,
            ),
            SysPlatformPatchValue="linux",
            MachinePatchFunc=lambda: "x86_64",
            ShouldAssert=False,
        ),
        Test(
            Result=platform.PlatformDetails(
                Platform=platform.Platforms.Linux,
                Arch=platform.Architectures.ARM64,
            ),
            SysPlatformPatchValue="linux",
            MachinePatchFunc=lambda: "arm64",
            ShouldAssert=False,
        ),
        Test(
            Result=platform.PlatformDetails(
                Platform=platform.Platforms.MacOS,
                Arch=platform.Architectures.AMD64,
            ),
            SysPlatformPatchValue="darwin",
            MachinePatchFunc=lambda: "x86_64",
            ShouldAssert=False,
        ),
        Test(
            Result=platform.PlatformDetails(
                Platform=platform.Platforms.MacOS,
                Arch=platform.Architectures.ARM64,
            ),
            SysPlatformPatchValue="darwin",
            MachinePatchFunc=lambda: "arm64",
            ShouldAssert=False,
        ),
        Test(
            Result=platform.PlatformDetails(
                Platform=platform.Platforms.Windows,
                Arch=platform.Architectures.AMD64,
            ),
            SysPlatformPatchValue="windows",
            MachinePatchFunc=lambda: "x86_64",
            ShouldAssert=False,
        ),
        Test(
            Result=None,
            SysPlatformPatchValue="windows",
            MachinePatchFunc=lambda: "arm64",
            ShouldAssert=True,
        ),
        Test(
            Result=None,
            SysPlatformPatchValue="linux",
            MachinePatchFunc=lambda: "s390x",
            ShouldAssert=True,
        ),
    ]

    for test in tests:
        monkeypatch.setattr(sys, "platform", test.SysPlatformPatchValue)
        monkeypatch.setattr(plt, "machine", test.MachinePatchFunc)

        if not test.ShouldAssert:
            assert test.Result == platform.get_platform_details()
        else:
            with pytest.raises(platform.InvalidPlatform):
                platform.get_platform_details()
