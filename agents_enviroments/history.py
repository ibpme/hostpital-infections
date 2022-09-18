from dataclasses import dataclass
from numpy import ndarray
import numpy as np


@dataclass(init=True)
class History:
    new_patients: ndarray = np.array([])
    colonized: ndarray = np.array([])
    new_infections: ndarray = np.array([])
    total: ndarray = np.array([])
    new_detected: ndarray = np.array([])
    screened: ndarray = np.array([])
    healed: ndarray = np.array([])
    removed: ndarray = np.array([])
    current_time: int = 0
    time = []

    def add(self, key, values: ndarray):
        if key == "new_patients":
            self.new_patients = np.append(self.new_patients, values)
        elif key == "colonized":
            self.colonized = np.append(self.colonized, values)
        elif key == "new_infections":
            self.new_infections = np.append(self.new_infections, values)
        elif key == "new_detected_patients":
            self.new_detected = np.append(
                self.new_detected, values)
        elif key == "screened_patients":
            self.screened = np.append(self.screened, values)
        elif key == "healed_patients":
            self.healed = np.append(self.healed, values)
        elif key == "removed_patients":
            self.removed = np.append(self.removed, values)
        elif key == "total":
            self.total = np.append(self.total, values)
        else:
            raise ValueError(f"Unknown Key {key}")

    def add_from_dict(self, hist_dict):
        for key, value in hist_dict.items():
            self.add(key, value)
        self.time.append(self.current_time)
        self.current_time += 1
