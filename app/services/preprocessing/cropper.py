"""Cropping utilities for question diagrams, tables, and visual figures."""

import io
from typing import Dict, List, Optional, Tuple, Union
from PIL import Image
import pymupdf


class RegionCropper:
    @staticmethod
    def crop_box(
        image: Image.Image,
        bbox: Union[List[float], Tuple[float, float, float, float]],
    ) -> Image.Image:
        """
        Crop a rectangular region from a PIL Image given [x0, y0, x1, y1].
        Clamps coordinates to image boundary.
        """
        w, h = image.size
        x0, y0, x1, y1 = bbox

        # Ensure valid coordinates
        left = max(0, min(int(x0), w - 1))
        top = max(0, min(int(y0), h - 1))
        right = max(left + 1, min(int(x1), w))
        bottom = max(top + 1, min(int(y1), h))

        return image.crop((left, top, right, bottom))

    @staticmethod
    def extract_pdf_embedded_images(
        pdf_page: pymupdf.Page,
        min_width: int = 40,
        min_height: int = 40,
    ) -> List[Tuple[Image.Image, Tuple[float, float, float, float]]]:
        """
        Extract embedded vector/raster images directly from a PyMuPDF PDF page stream.
        Returns: List of (PIL.Image, (x0, y0, x1, y1))
        """
        extracted = []
        doc = pdf_page.parent
        image_list = pdf_page.get_images(full=True)

        for img_info in image_list:
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                img = Image.open(io.BytesIO(image_bytes))

                # Filter out tiny icon artifacts
                if img.width >= min_width and img.height >= min_height:
                    # Attempt to find visual bounding box on page
                    rects = pdf_page.get_image_rects(xref)
                    bbox = tuple(rects[0]) if rects else (0, 0, img.width, img.height)
                    extracted.append((img, bbox))
            except Exception:
                continue

        return extracted


region_cropper = RegionCropper()
