"""Configuration of a Pixoo device"""

class PixooConfig:
    """Class representing the configuration of a device"""

    __address = None
    __size = 64
    __refresh_connection_automatically = True

    def __init__(self, address=None, size=64, refresh_connection_automatically=True):
        assert size in [16, 32, 64], (
            "Invalid screen size in pixels given. " "Valid options are 16, 32, and 64"
        )
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
