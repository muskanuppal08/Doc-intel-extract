"""Image enhancement and normalization for degraded or scanned documents."""

from PIL import Image, ImageOps, ImageEnhance, ImageFilter


class ImageNormalizer:
    @staticmethod
    def fix_orientation(image: Image.Image) -> Image.Image:
        """Correct image orientation using EXIF metadata if present."""
        return ImageOps.exif_transpose(image)

    @staticmethod
    def enhance_for_ocr(
        image: Image.Image,
        contrast_factor: float = 1.5,
        sharpness_factor: float = 1.5,
    ) -> Image.Image:
        """
        Enhance degraded, blurry, or low-contrast document images:
        1. Auto-rotate based on EXIF.
        2. Convert to grayscale.
        3. Boost contrast to separate text from background noise.
        4. Apply mild unsharp masking to restore edge definition.
        """
        img = ImageNormalizer.fix_orientation(image)

        # Convert to grayscale
        if img.mode != "L":
            img = img.convert("L")

        # Boost contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)

        # Sharpen edges
        sharpener = ImageEnhance.Sharpness(img)
        img = sharpener.enhance(sharpness_factor)

        return img

    @staticmethod
    def binarize_adaptive(image: Image.Image, threshold: int = 140) -> Image.Image:
        """Convert grayscale image to crisp black-and-white for low-quality scans."""
        gray = image.convert("L")
        return gray.point(lambda p: 255 if p > threshold else 0)


normalizer = ImageNormalizer()
