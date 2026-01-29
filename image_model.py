import cv2
import numpy as np


class ImageModel:
    """
    Encapsulates image data + OpenCV processing methods.
    Stores original + current image and filepath.
    Images are stored in BGR format (OpenCV standard).
    """

    def __init__(self):
        self._original = None
        self._current = None
        self._filepath = None

    # ---- basic getters ----
    def has_image(self) -> bool:
        return self._current is not None

    def get_current(self):
        return self._current

    def get_filepath(self):
        return self._filepath

    def get_dimensions(self):
        if self._current is None:
            return None
        h, w = self._current.shape[:2]
        return (w, h)

    # ---- file operations ----
    def load(self, path: str):
        img = cv2.imread(path)
        if img is None:
            raise ValueError("Unsupported file or cannot read image.")
        self._filepath = path
        self._original = img.copy()
        self._current = img.copy()

    def set_current(self, img_bgr):
        self._current = img_bgr

    def set_filepath(self, path: str):
        self._filepath = path

    def reset_to_original(self):
        if self._original is not None:
            self._current = self._original.copy()

    # ---- image processing ----
    def to_grayscale(self):
        gray = cv2.cvtColor(self._current, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    def apply_blur(self, intensity: int):
        k = max(1, int(intensity))
        if k % 2 == 0:
            k += 1
        return cv2.GaussianBlur(self._current, (k, k), 0)

    def edge_detect(self, low=50, high=150):
        gray = cv2.cvtColor(self._current, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, low, high)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    def adjust_brightness_contrast(self, brightness=0, contrast=1.0):
        # brightness: -100..100, contrast: 0.2..3.0
        img = self._current.astype(np.int16)
        img = img * float(contrast) + int(brightness)
        img = np.clip(img, 0, 255).astype(np.uint8)
        return img

    def rotate(self, angle: int):
        if angle == 90:
            return cv2.rotate(self._current, cv2.ROTATE_90_CLOCKWISE)
        if angle == 180:
            return cv2.rotate(self._current, cv2.ROTATE_180)
        if angle == 270:
            return cv2.rotate(self._current, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return self._current

    def flip(self, mode: str):
        if mode == "horizontal":
            return cv2.flip(self._current, 1)
        if mode == "vertical":
            return cv2.flip(self._current, 0)
        return self._current

    def resize_scale(self, scale_percent: int):
        h, w = self._current.shape[:2]
        new_w = max(1, int(w * scale_percent / 100))
        new_h = max(1, int(h * scale_percent / 100))
        return cv2.resize(self._current, (new_w, new_h), interpolation=cv2.INTER_AREA)
