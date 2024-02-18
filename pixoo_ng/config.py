"""Configuration of a Pixoo device"""

from pixoo.find_device import get_pixoo_devices as _get_pixoo_devices
import pixoo.exceptions as _exceptions

class PixooConfig:
    """Class representing the configuration of a device"""

    __address = None
    __size = 64
    __refresh_connection_automatically = True


    @staticmethod
    def __get_first_pixoo_device_address():
        pixoo_devices = _get_pixoo_devices()
        if len(pixoo_devices) > 1:
            raise _exceptions.MoreThanOnePixooFound(f"PixoDevices: {pixoo_devices}")
        pixoo_device = pixoo_devices[0]  # Just take first (and unique) item
        dev_name = pixoo_device["DeviceName"]
        dev_ip = pixoo_device["DevicePrivateIP"]
        print(f" Pixo Device auto identified!!! DeviceName: {dev_name} (IP: {dev_ip})")
        return dev_ip


    def __init__(self, address=None, size=64, refresh_connection_automatically=True):
        assert size in [16, 32, 64], (
            "Invalid screen size in pixels given. " "Valid options are 16, 32, and 64"
        )

        if address is None:
            self.__address = self.__get_first_pixoo_device_address()
        else:
            self.__address = address

        self.__size = size
        self.__refresh_connection_automatically = refresh_connection_automatically

    @property
    def address(self):
        """Function to return the address of the Pixoo device"""
        return self.__address

    @property
    def size(self):
        """Function to return the size of the Pixoo device"""
        return self.__size

    @property
    def refresh_connection_automatically(self):
        """Function to return the setting for automatic refresh"""
        return self.__refresh_connection_automatically
