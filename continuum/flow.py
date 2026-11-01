"""Optical flow on the CPU, used until the GPU estimators have run."""

from __future__ import annotations

import cv2
import numpy as np


def dis_magnitude(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Flow norm in pixels between two RGB frames."""
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    flow = dis.calc(
        cv2.cvtColor(before, cv2.COLOR_RGB2GRAY), cv2.cvtColor(after, cv2.COLOR_RGB2GRAY), None
    )
    return np.linalg.norm(flow, axis=2)
