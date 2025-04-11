import asyncio
import base64
import os
import shlex
import keyboard
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict
from uuid import uuid4

from anthropic.types.beta import BetaToolComputerUse20241022Param

# Import our asyncio-compatible GUI automation module
from .async_gui import get_screen_size, move_mouse, click_mouse, double_click, \
    drag_mouse, type_text, press_key, take_screenshot, get_cursor_position

from .base import BaseAnthropicTool, ToolError, ToolResult
from .run import run

OUTPUT_DIR = "/tmp/outputs"

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action = Literal[
    "key",
    "type",
    "mouse_move",
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
]


class Resolution(TypedDict):
    width: int
    height: int


# sizes above XGA/WXGA are not recommended (see README.md)
# scale down to one of these targets if ComputerTool._scaling_enabled is set
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}
SCALE_DESTINATION = MAX_SCALING_TARGETS["FWXGA"]


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"


class ComputerToolOptions(TypedDict):
    display_height_px: int
    display_width_px: int
    display_number: int | None


def chunks(s: str, chunk_size: int) -> list[str]:
    return [s[i : i + chunk_size] for i in range(0, len(s), chunk_size)]


class ComputerTool(BaseAnthropicTool):
    """
    A tool that allows the agent to interact with the screen, keyboard, and mouse of the current macOS computer.
    The tool parameters are defined by Anthropic and are not editable.
    Requires cliclick to be installed: brew install cliclick
    """

    name: Literal["computer"] = "computer"
    api_type: Literal["computer_20241022"] = "computer_20241022"
    width: int
    height: int
    display_num: int | None

    _screenshot_delay = 1.0  # macOS is generally faster than X11
    _scaling_enabled = True

    @property
    def options(self) -> ComputerToolOptions:
        return {
            "display_width_px": self.width,
            "display_height_px": self.height,
            "display_number": self.display_num,
        }

    def to_params(self) -> BetaToolComputerUse20241022Param:
        return {"name": self.name, "type": self.api_type, **self.options}

    def __init__(self):
        super().__init__()

        # We'll get the screen size when needed asynchronously
        # This avoids blocking during initialization
        self.width, self.height = 1366, 768  # Default values, will be updated
        self.display_num = None  # macOS doesn't use X11 display numbers
        
        # Flag to indicate whether screen size has been initialized
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure screen size is initialized asynchronously"""
        if not self._initialized:
            self.width, self.height = await get_screen_size()
            self._initialized = True
            
    async def __call__(
        self,
        *,
        action: Action,
        text: str | None = None,
        coordinate: tuple[int, int] | None = None,
        **kwargs,
    ):
        await self._ensure_initialized()
        print("Action: ", action, text, coordinate)
        if action in ("mouse_move", "left_click_drag"):
            if coordinate is None:
                raise ToolError(f"coordinate is required for {action}")
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")
            if not isinstance(coordinate, list) or len(coordinate) != 2:
                raise ToolError(f"{coordinate} must be a tuple of length 2")
            if not all(isinstance(i, int) and i >= 0 for i in coordinate):
                raise ToolError(f"{coordinate} must be a tuple of non-negative ints")

            x, y = self.scale_coordinates(ScalingSource.API, coordinate[0], coordinate[1])

            if action == "mouse_move":
                await move_mouse(x, y)
                return ToolResult(output=f"Moved mouse to {x},{y}", error=None, base64_image=None)
            elif action == "left_click_drag":
                # Get current position first
                curr_x, curr_y = await get_cursor_position()
                await drag_mouse(curr_x, curr_y, x, y)
                return ToolResult(output=f"Dragged mouse from {curr_x},{curr_y} to {x},{y}", error=None, base64_image=None)

        if action in ("key", "type"):
            if text is None:
                raise ToolError(f"text is required for {action}")
            if coordinate is not None:
                raise ToolError(f"coordinate is not accepted for {action}")
            if not isinstance(text, str):
                raise ToolError(output=f"{text} must be a string")

            if action == "key":
                try:
                    await press_key(text)
                    return ToolResult(output=f"Pressed key: {text}", error=None, base64_image=None)
                except Exception as e:
                    return ToolResult(output=None, error=str(e), base64_image=None)
            elif action == "type":
                try:
                    await type_text(text, TYPING_DELAY_MS)
                    # Take a screenshot after typing
                    screenshot_result = await self.screenshot()
                    return ToolResult(
                        output=f"Typed: {text}",
                        error=None,
                        base64_image=screenshot_result.base64_image
                    )
                except Exception as e:
                    return ToolResult(output=None, error=str(e), base64_image=None)

        if action in (
            "left_click",
            "right_click",
            "double_click",
            "middle_click",
            "screenshot",
            "cursor_position",
        ):
            if text is not None:
                raise ToolError(f"text is not accepted for {action}")

            if action == "screenshot":
                return await self.screenshot()
            elif action == "cursor_position":
                x, y = await get_cursor_position()
                # Scale coordinates if needed
                x, y = self.scale_coordinates(ScalingSource.COMPUTER, x, y)
                return ToolResult(output=f"X={x},Y={y}", error=None, base64_image=None)
            else:
                # Handle mouse clicks
                try:
                    if action == "left_click":
                        await click_mouse(button="left")
                    elif action == "right_click":
                        await click_mouse(button="right")
                    elif action == "middle_click":
                        await click_mouse(button="middle")
                    elif action == "double_click":
                        await double_click()
                    
                    # Take a screenshot after the action
                    screenshot_result = await self.screenshot()
                    return ToolResult(
                        output=f"Performed {action}",
                        error=None,
                        base64_image=screenshot_result.base64_image
                    )
                except Exception as e:
                    return ToolResult(output=None, error=str(e), base64_image=None)

        raise ToolError(f"Invalid action: {action}")

    async def screenshot(self):
        """Take a screenshot of the current screen and return the base64 encoded image."""
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"screenshot_{uuid4().hex}.png"

        # Use our async screenshot function
        success = await take_screenshot(str(path))
        if not success:
            raise ToolError(f"Failed to take screenshot")

        if self._scaling_enabled:
            # Scale the screenshot if needed
            x, y = SCALE_DESTINATION['width'], SCALE_DESTINATION['height']
            await self.shell(
                f"sips -z {y} {x} {path}",  # sips is macOS native image processor
                take_screenshot=False
            )

        if path.exists():
            img_data = base64.b64encode(path.read_bytes()).decode()
            return ToolResult(output=None, error=None, base64_image=img_data)
        
        raise ToolError(f"Failed to read screenshot from {path}")

    async def shell(self, command: str, take_screenshot=False) -> ToolResult:
        """Run a shell command and return the output, error, and optionally a screenshot."""
        _, stdout, stderr = await run(command)
        base64_image = None

        if take_screenshot:
            # delay to let things settle before taking a screenshot
            await asyncio.sleep(self._screenshot_delay)
            base64_image = (await self.screenshot()).base64_image

        return ToolResult(output=stdout, error=stderr, base64_image=base64_image)

    def scale_coordinates(self, source: ScalingSource, x: int, y: int) -> tuple[int, int]:
        """
        Scale coordinates between original resolution and target resolution (SCALE_DESTINATION).

        Args:
            source: ScalingSource.API for scaling up from SCALE_DESTINATION to original resolution
                   or ScalingSource.COMPUTER for scaling down from original to SCALE_DESTINATION
            x, y: Coordinates to scale

        Returns:
            Tuple of scaled (x, y) coordinates
        """
        if not self._scaling_enabled:
            return x, y

        # Calculate scaling factors
        x_scaling_factor = SCALE_DESTINATION['width'] / self.width
        y_scaling_factor = SCALE_DESTINATION['height'] / self.height

        if source == ScalingSource.API:
            # Scale up from SCALE_DESTINATION to original resolution
            if x > SCALE_DESTINATION['width'] or y > SCALE_DESTINATION['height']:
                raise ToolError(f"Coordinates {x}, {y} are out of bounds for {SCALE_DESTINATION['width']}x{SCALE_DESTINATION['height']}")
            return round(x / x_scaling_factor), round(y / y_scaling_factor)
        else:
            # Scale down from original resolution to SCALE_DESTINATION
            return round(x * x_scaling_factor), round(y * y_scaling_factor)
