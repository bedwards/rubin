from .base import PresetStyle, VocalPreset, GuitarPreset, MasterPreset
from .analog_console import ANALOG_CONSOLE_VOCAL, ANALOG_CONSOLE_GUITAR, ANALOG_CONSOLE_MASTER
from .tape import TAPE_VOCAL, TAPE_GUITAR, TAPE_MASTER
from .lofi import LOFI_VOCAL, LOFI_GUITAR, LOFI_MASTER

__all__ = [
    "PresetStyle",
    "VocalPreset", "GuitarPreset", "MasterPreset",
    "ANALOG_CONSOLE_VOCAL", "ANALOG_CONSOLE_GUITAR", "ANALOG_CONSOLE_MASTER",
    "TAPE_VOCAL", "TAPE_GUITAR", "TAPE_MASTER",
    "LOFI_VOCAL", "LOFI_GUITAR", "LOFI_MASTER",
]
