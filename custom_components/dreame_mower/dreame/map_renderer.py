"""Vector polygon map renderer for Dreame mower.

Renders MowerVectorMap data (zone polygons, paths, mowing trails) into
PNG images using PIL. This is a standalone renderer that does NOT use the
existing DreameMowerMapRenderer (which expects pixel-grid/bitmap data).
"""
import io
import logging
from PIL import Image, ImageDraw, ImageFont

from .types import MowerVectorMap

_LOGGER = logging.getLogger(__name__)

# Rendering constants
_MAX_IMAGE_SIZE = 2048  # Max pixels on longest side
_MIN_IMAGE_SIZE = 400   # Min pixels on longest side
_PADDING = 40           # Pixel padding around map edges
_BACKGROUND_COLOR = (30, 30, 30)  # Dark grey background
_ZONE_OUTLINE_COLOR = (255, 255, 255, 180)  # White outlines
_ZONE_OUTLINE_WIDTH = 2
_PATH_COLOR = (200, 200, 100, 150)  # Yellow-ish for navigation paths
_PATH_WIDTH = 2
_MOW_PATH_COLOR = (100, 200, 100, 100)  # Green for mowing trails
_MOW_PATH_WIDTH = 1
_LABEL_COLOR = (255, 255, 255, 220)  # White text
_FORBIDDEN_COLOR = (200, 50, 50, 120)  # Red for no-go zones

# Zone fill colors — distinct colors for up to 8 zones, cycling after
_ZONE_COLORS = [
    (76, 153, 0, 140),    # Green
    (0, 128, 128, 140),   # Teal
    (0, 102, 204, 140),   # Blue
    (153, 102, 0, 140),   # Brown
    (102, 51, 153, 140),  # Purple
    (204, 102, 0, 140),   # Orange
    (0, 153, 153, 140),   # Cyan
    (153, 153, 0, 140),   # Olive
]


class MowerVectorMapRenderer:
    """Renders MowerVectorMap to PNG images."""

    def __init__(self) -> None:
        self._cached_image: bytes | None = None
        self._cached_last_updated: float | None = None
        self.render_complete: bool = True

    def render(self, vector_map: MowerVectorMap | None) -> bytes | None:
        """Render a MowerVectorMap to PNG bytes.

        Args:
            vector_map: The vector map data to render.

        Returns:
            PNG image as bytes, or None if map data is invalid.
        """
        if vector_map is None:
            return None

        if not vector_map.boundary:
            _LOGGER.debug("No boundary in vector map, cannot render")
            return None

        # Cache check
        if (self._cached_image is not None
                and self._cached_last_updated == vector_map.last_updated):
            return self._cached_image

        self.render_complete = False
        try:
            image = self._render_to_image(vector_map)
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            self._cached_image = buf.getvalue()
            self._cached_last_updated = vector_map.last_updated
            return self._cached_image
        finally:
            self.render_complete = True

    def _render_to_image(self, vmap: MowerVectorMap) -> Image.Image:
        """Render vector map data to a PIL Image."""
        boundary = vmap.boundary

        # Calculate image dimensions preserving aspect ratio
        map_w = boundary.width
        map_h = boundary.height

        if map_w == 0 or map_h == 0:
            return Image.new("RGBA", (100, 100), _BACKGROUND_COLOR)

        scale = min(
            (_MAX_IMAGE_SIZE - 2 * _PADDING) / max(map_w, 1),
            (_MAX_IMAGE_SIZE - 2 * _PADDING) / max(map_h, 1),
        )
        # Ensure minimum size
        scale = max(scale, _MIN_IMAGE_SIZE / max(map_w, map_h, 1))

        img_w = int(map_w * scale) + 2 * _PADDING
        img_h = int(map_h * scale) + 2 * _PADDING

        image = Image.new("RGBA", (img_w, img_h), _BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        def to_pixel(x: int, y: int) -> tuple[int, int]:
            """Convert map coordinates to pixel coordinates."""
            px = int((x - boundary.x1) * scale) + _PADDING
            # Flip Y axis — map coords have Y increasing downward,
            # but we want Y=0 at top of image for natural "north up" view
            py = img_h - (int((y - boundary.y1) * scale) + _PADDING)
            return (px, py)

        # 1. Draw zone fills
        for i, zone in enumerate(vmap.zones):
            if len(zone.path) < 3:
                continue
            color = _ZONE_COLORS[i % len(_ZONE_COLORS)]
            polygon = [to_pixel(x, y) for x, y in zone.path]
            draw.polygon(polygon, fill=color, outline=_ZONE_OUTLINE_COLOR, width=_ZONE_OUTLINE_WIDTH)

        # 2. Draw forbidden areas
        for zone in vmap.forbidden_areas:
            if len(zone.path) < 3:
                continue
            polygon = [to_pixel(x, y) for x, y in zone.path]
            draw.polygon(polygon, fill=_FORBIDDEN_COLOR, outline=(200, 50, 50, 220), width=2)

        # 3. Draw mowing paths (trails)
        for mow_path in vmap.mow_paths:
            for segment in mow_path.segments:
                if len(segment) < 2:
                    continue
                points = [to_pixel(x, y) for x, y in segment]
                draw.line(points, fill=_MOW_PATH_COLOR, width=_MOW_PATH_WIDTH)

        # 4. Draw navigation paths between zones
        for path in vmap.paths:
            if len(path.path) < 2:
                continue
            points = [to_pixel(x, y) for x, y in path.path]
            draw.line(points, fill=_PATH_COLOR, width=_PATH_WIDTH)

        # 5. Draw zone labels
        for zone in vmap.zones:
            if not zone.name or len(zone.path) < 3:
                continue
            # Calculate centroid for label placement
            cx = sum(x for x, y in zone.path) // len(zone.path)
            cy = sum(y for x, y in zone.path) // len(zone.path)
            px, py = to_pixel(cx, cy)
            # Draw label with area
            label = zone.name
            if zone.area > 0:
                label += f"\n{zone.area:.0f}m\u00b2"
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None
            bbox = draw.textbbox((px, py), label, font=font, anchor="mm")
            # Draw background rectangle for readability
            draw.rectangle(
                [bbox[0] - 3, bbox[1] - 2, bbox[2] + 3, bbox[3] + 2],
                fill=(0, 0, 0, 160),
            )
            draw.text((px, py), label, fill=_LABEL_COLOR, font=font, anchor="mm")

        return image
