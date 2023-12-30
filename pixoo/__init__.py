"""Pixoo class to access the Divoom Pixoo frame"""
import base64
from enum import IntEnum

from PIL import Image, ImageOps

from pixoo.config import PixooConfig
from pixoo._colors import Palette
from pixoo.font import Font
from pixoo.simulator import Simulator, SimulatorConfig
from pixoo.api import PixooBaseApi


def clamp(value, minimum=0, maximum=255):
    """Function to keep a value in a range"""
    if value > maximum:
        return maximum
    if value < minimum:
        return minimum

    return value


def clamp_color(rgb):
    """Function to ensure the RGB color values are in the right range"""
    return clamp(rgb[0]), clamp(rgb[1]), clamp(rgb[2])


def lerp(start, end, interpolant):
    """Function to calculate increment on a linear interpolation in one dimension"""
    return start + interpolant * (end - start)


def lerp_location(xy1, xy2, interpolant):
    """Function to calculate increment on a linear interpolation in two dimensions"""
    return lerp(xy1[0], xy2[0], interpolant), lerp(xy1[1], xy2[1], interpolant)


def minimum_amount_of_steps(xy1, xy2):
    """Function to calculate the larger of horizontal or vertical distance"""
    return max(abs(xy1[0] - xy2[0]), abs(xy1[1] - xy2[1]))


def rgb_to_hex_color(rgb):
    """Function to convert RGB color to hex"""
    return f"#{rgb[0]:0>2X}{rgb[1]:0>2X}{rgb[2]:0>2X}"


def round_location(xy):
    """Function to round coordinates"""
    return round(xy[0]), round(xy[1])


class Channel(IntEnum):
    """Class representing a Channel"""

    FACES = 0
    CLOUD = 1
    VISUALIZER = 2
    CUSTOM = 3


class ImageResampleMode(IntEnum):
    """Class representing an image sample mode"""

    PIXEL_ART = Image.Resampling.NEAREST
    SMOOTH = Image.Resampling.LANCZOS


class TextScrollDirection(IntEnum):
    """Class representing the text scroll direction"""

    LEFT = 0
    RIGHT = 1


class Pixoo(PixooBaseApi):
    """Class representing the Pixoo device"""

    __buffer = []
    __buffers_send = 0
    __counter = 0
    __refresh_counter_limit = 32
    __simulator = None

    def __init__(
        self,
        pixoo_config=PixooConfig(),
        debug=False,
        simulated=False,
        simulation_config=SimulatorConfig(),
    ):
        self.refresh_connection_automatically = (
            pixoo_config.refresh_connection_automatically
        )
        super().__init__(pixoo_config.address)
        self.debug = debug
        self.size = pixoo_config.size
        self.simulated = simulated

        # Total number of pixels
        self.pixel_count = self.size * self.size

        # Generate URL
        self.__url = f"http://{pixoo_config.address}/post"

        # Prefill the buffer
        self.fill()

        # Retrieve the counter
        self.__load_counter()

        # Resetting if needed
        if (
            self.refresh_connection_automatically
            and self.__counter > self.__refresh_counter_limit
        ):
            self.__reset_counter()

        # We're going to need a simulator
        if self.simulated:
            self.__simulator = Simulator(self, simulation_config)


    def clear(self, rgb=Palette.BLACK):
        """Function to clear the buffer"""
        self.fill(rgb)

    def clear_rgb(self, r, g, b):
        """Function to clear the buffer"""
        self.fill_rgb(r, g, b)

    def draw_filled_rectangle(
        self, top_left_xy=(0, 0), bottom_right_xy=(1, 1), rgb=Palette.BLACK
    ):
        """Function to draw a filled rectangle"""
        for y in range(top_left_xy[1], bottom_right_xy[1] + 1):
            for x in range(top_left_xy[0], bottom_right_xy[0] + 1):
                self.draw_pixel((x, y), rgb)

    def draw_filled_rectangle_from_top_left_to_bottom_right_rgb(
        self,
        top_left_x=0,
        top_left_y=0,
        bottom_right_x=1,
        bottom_right_y=1,
        r=0,
        g=0,
        b=0,
    ):
        """Function to draw a filled rectangle"""
        self.draw_filled_rectangle(
            (top_left_x, top_left_y), (bottom_right_x, bottom_right_y), (r, g, b)
        )

    def draw_image(
        self,
        image_path_or_object,
        xy=(0, 0),
        image_resample_mode=ImageResampleMode.PIXEL_ART,
        pad_resample=False,
    ):
        """Function to draw an image at a location"""
        image = (
            image_path_or_object
            if isinstance(image_path_or_object, Image.Image)
            else Image.open(image_path_or_object)
        )
        size = image.size
        width = size[0]
        height = size[1]

        # See if it needs to be scaled/resized to fit the display
        if width > self.size or height > self.size:
            if pad_resample:
                image = ImageOps.pad(image, (self.size, self.size), image_resample_mode)
            else:
                image.thumbnail((self.size, self.size), image_resample_mode)

            if self.debug:
                print(
                    f'[.] Resized image to fit on screen (saving aspect ratio): "{image_path_or_object}" ({width}, {height}) '
                    f"-> ({image.size[0]}, {image.size[1]})"
                )

        # Convert the loaded image to RGBA to also support transparency
        rgb_image = image.convert("RGBA")

        # Iterate over all pixels in the image that are left and buffer them
        for y in range(image.size[1]):
            for x in range(image.size[0]):
                location = (x, y)
                if rgb_image.getpixel(location)[3] == 0:
                    continue
                placed_x = x + xy[0]
                if self.size - 1 < placed_x or placed_x < 0:
                    continue

                placed_y = y + xy[1]
                if self.size - 1 < placed_y or placed_y < 0:
                    continue
                self.draw_pixel((placed_x, placed_y), rgb_image.getpixel(location))

    def draw_image_at_location(
        self,
        image_path_or_object,
        x,
        y,
        image_resample_mode=ImageResampleMode.PIXEL_ART,
    ):
        """Function to draw an image at a location"""
        self.draw_image(image_path_or_object, (x, y), image_resample_mode)

    def draw_line(self, start_xy, stop_xy, rgb=Palette.WHITE):
        """Function to draw a line"""
        line = set()

        # Calculate the amount of steps needed between the points to draw a nice line
        amount_of_steps = minimum_amount_of_steps(start_xy, stop_xy)

        # Iterate over them and create a nice set of pixels
        for step in range(amount_of_steps):
            if amount_of_steps == 0:
                interpolant = 0
            else:
                interpolant = step / amount_of_steps

            # Add a pixel as a rounded location
            line.add(round_location(lerp_location(start_xy, stop_xy, interpolant)))

        # Draw the actual pixel line
        for pixel in line:
            self.draw_pixel(pixel, rgb)

    def draw_line_from_start_to_stop_rgb(
        self, start_x, start_y, stop_x, stop_y, r=255, g=255, b=255
    ):
        """Function to draw a line"""
        self.draw_line((start_x, start_y), (stop_x, stop_y), (r, g, b))

    def draw_pixel(self, xy, rgb):
        """Function to draw a pixel"""
        # If it's not on the screen, we're not going to bother
        if xy[0] < 0 or xy[0] >= self.size or xy[1] < 0 or xy[1] >= self.size:
            if self.debug:
                limit = self.size - 1
                print(
                    f"[!] Invalid coordinates given: ({xy[0]}, {xy[1]}) (maximum coordinates are ({limit}, {limit})" # pylint: disable=line-too-long
                )
            return

        # Calculate the index
        index = xy[0] + (xy[1] * self.size)

        # Color it
        self.draw_pixel_at_index(index, rgb)

    def draw_pixel_at_index(self, index, rgb):
        """Function to draw a pixel"""
        # Validate the index
        if index < 0 or index >= self.pixel_count:
            if self.debug:
                print(
                    f"[!] Invalid index given: {index} (maximum index is {self.pixel_count - 1})"
                )
            return

        # Clamp the color, just to be safe
        rgb = clamp_color(rgb)

        # Move to place in array
        index = index * 3

        self.__buffer[index] = rgb[0]
        self.__buffer[index + 1] = rgb[1]
        self.__buffer[index + 2] = rgb[2]

    def draw_pixel_at_index_rgb(self, index, r, g, b):
        """Function to draw a pixel"""
        self.draw_pixel_at_index(index, (r, g, b))

    def draw_pixel_at_location_rgb(self, x, y, r, g, b):
        """Function to draw a pixel"""
        self.draw_pixel((x, y), (r, g, b))

    def draw_character(self, character, xy=(0, 0), rgb=Palette.WHITE, font=None):
        """Function to draw a character"""
        if font is None:
            font = Font.FONT_PICO_8
        matrix = Font.retrieve_glyph(character, font)
        if matrix is not None:
            teiler = matrix[-1]
            for index, bit in enumerate(matrix):
                if bit == 1:
                    local_x = index % teiler
                    local_y = int(index / teiler)
                    self.draw_pixel((xy[0] + local_x, xy[1] + local_y), rgb)

    def draw_character_at_location_rgb(self, character, x=0, y=0, r=255, g=255, b=255, font=None):
        """Function to draw a character at a given location"""
        self.draw_character(character, (x, y), (r, g, b), font)

    def draw_text(self, text, xy=(0, 0), rgb=Palette.WHITE, font=None):
        """Function to draw a text"""
        if font is None:
            font = Font.FONT_PICO_8
        matrix = 0
        for __, character in enumerate(text):
            self.draw_character(character, (matrix + xy[0], xy[1]), rgb, font)
            matrix += Font.retrieve_glyph(character, font)[-1] + 1

    def draw_text_at_location_rgb(self, text, x, y, r, g, b, font=None):
        """Function to draw a text"""
        self.draw_text(text, (x, y), (r, g, b), font)

    def fill(self, rgb=Palette.BLACK):
        """Function to fill the buffer"""
        self.__buffer = []
        rgb = clamp_color(rgb)
        for __ in range(self.pixel_count):
            self.__buffer.extend(rgb)

    def fill_rgb(self, r, g, b):
        """Function to fill the buffer"""
        self.fill((r, g, b))

    def get_settings(self):
        """Function to retreive the settings"""
        data = self.send_command("Channel/GetAllConf")
        return {key: val for key, val in data.items() if key != "error_code"}

    def push(self):
        """Function to send the buffer to the device"""
        self.__send_buffer()

    def send_text(
        self,
        text,
        xy=(0, 0),
        color=Palette.WHITE,
        identifier=1,
        font=2,
        width=64,
        movement_speed=0,
        direction=TextScrollDirection.LEFT,
    ):
        """Function to send text directly to the device without the buffer"""
        # This won't be possible
        if self.simulated:
            return

        # Make sure the identifier is valid
        identifier = clamp(identifier, 0, 19)
        self.send_command(
            command="Draw/SendText",
            text_id=identifier,
            x=xy[0],
            y=xy[1],
            dir=direction,
            font=font,
            text_width=width,
            speed=movement_speed,
            text_string=text,
            color=rgb_to_hex_color(color),
            align=1,  # Align text was not previously defined, so assuming 1
        )

    def set_brightness(self, brightness):
        """Function to set the brightness"""
        # This won't be possible
        if self.simulated:
            return

        brightness = clamp(brightness, 0, 100)
        self.send_command(
            command="Channel/SetBrightness",
            brightness=brightness,
        )

    def set_channel(self, channel):
        """Function to set the channel"""
        # This won't be possible
        if self.simulated:
            return

        self.send_command(
            command="Channel/SetIndex",
            select_index=channel,
        )

    def set_clock(self, clock_id):
        """Function to set the clock"""
        # This won't be possible
        if self.simulated:
            return

        self.send_command(
            command="Channel/SetClockSelectId",
            clock_id=clock_id,
        )

    def set_custom_channel(self, index):
        """Function to set the custom channel, which is channel #3"""
        self.set_custom_page(index)
        self.set_channel(3)

    def set_custom_page(self, index):
        """Function to set a custom page"""
        self.send_command(
            command="Channel/SetCustomPageIndex",
            custom_page_index=index,
        )

    def set_face(self, face_id):
        """Function to set a (clock) face"""
        self.set_clock(face_id)

    def set_screen(self, on=True):
        """Function to switch screen on or off"""
        # This won't be possible
        if self.simulated:
            return

        self.send_command(
            command="Channel/OnOffScreen",
            on_off=1 if on else 0,
        )

    def set_screen_off(self):
        """Function to switch screen off"""
        self.set_screen(False)

    def set_screen_on(self):
        """Function to set screen on"""
        self.set_screen(True)

    def set_visualizer(self, equalizer_position):
        """Function to set equalizer position"""
        # This won't be possible
        if self.simulated:
            return

        self.send_command(
            command="Channel/SetEqPosition",
            eq_position=equalizer_position,
        )

    # def __clamp_location(self, xy):
    #     """Function ensure location is in range"""
    #     return clamp(xy[0], 0, self.size - 1), clamp(xy[1], 0, self.size - 1)

    # def __error(self, error):
    #     """Function to print debug error"""
    #     if self.debug:
    #         print("[x] Error on request " + str(self.__counter))
    #         print(error)

    def __load_counter(self):
        """Function to load counter from device"""
        # Just assume it's starting at the beginning if we're simulating
        if self.simulated:
            self.__counter = 1
            return

        data = self.send_command(command="Draw/GetHttpGifId")
        self.__counter = int(data["PicId"])
        if self.debug:
            print("[.] Counter loaded and stored: " + str(self.__counter))

    def __send_buffer(self):
        """Function to send buffer to device"""
        # Add to the internal counter
        self.__counter = self.__counter + 1

        # Check if we've passed the limit and reset the counter for the animation remotely
        if (
            self.refresh_connection_automatically
            and self.__counter >= self.__refresh_counter_limit
        ):
            self.__reset_counter()
            self.__counter = 1

        if self.debug:
            print(f"[.] Counter set to {self.__counter}")

        # If it's simulated, we don't need to actually push it to the divoom
        if self.simulated:
            self.__simulator.display(self.__buffer, self.__counter)

            # Simulate this too I suppose
            self.__buffers_send = self.__buffers_send + 1
            return

        # Encode the buffer to base64 encoding
        self.send_command(
            command="Draw/SendHttpGif",
            pic_num=1,
            pic_width=self.size,
            pic_offset=0,
            pic_id=self.__counter,
            pic_speed=1000,
            pic_data=str(base64.b64encode(bytearray(self.__buffer)).decode()),
        )
        self.__buffers_send = self.__buffers_send + 1

        if self.debug:
            print(f"[.] Pushed {self.__buffers_send} buffers")

    def __reset_counter(self):
        """Function to reset the counter"""
        if self.debug:
            print("[.] Resetting counter remotely")

        # This won't be possible
        if self.simulated:
            return

        self.send_command(
            command="Draw/ResetHttpGifId",
        )

    @property
    def url(self):
        """Get device URL"""
        return self.__url

    @property
    def address(self):
        """Get device address"""
        return self.__address

    @property
    def buffer(self):
        """Get buffer of device"""
        return self.__buffer


__all__ = ["Channel", "ImageResampleMode", "Pixoo", "TextScrollDirection"]
