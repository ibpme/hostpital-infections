from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import math
if TYPE_CHECKING:
    from .bay import Bay
    from .ward import Ward
    from .patient import Patient


class MovementStrategy(ABC):

    def change_patient_location(self, patient: Patient, new_bay: Bay):
        """Change patients location from one bay to another"""
        # if not isinstance(patient, Patient):
        #     raise TypeError(f"{type(patient)} is not of Patient Type")
        # if not isinstance(new_bay, Bay):
        #     raise TypeError(f"{type(new_bay)} is not of Bay Type")
        old_bay = patient.location
        old_bay.remove_patient(patient)
        new_bay.add_patient(patient)

    @abstractmethod
    def move_patients(self, ward: Ward):
        pass


class IsolateInfectedStrategyy(MovementStrategy):

    def move_patients(self, ward: Ward):
        # Find available isolation bay in ward
        available_isobay = [
            isobay for isobay in ward.isobays if not isobay.is_full]
        for patient in ward.patients:
            if len(available_isobay) == 0:
                return
            if patient.detection_status and not patient.location.is_isobay:
                self.change_patient_location(patient, available_isobay.pop())


class GroupInfectedStrategyy(MovementStrategy):

    def switch_infected(self, from_bay: Bay, to_bay: Bay):
        detected = from_bay.detected.pop()
        # Does not switch, but add for bay only containing detected
        if(to_bay.num_of_undetected != 0):
            undetected = to_bay.undetected.pop()
            from_bay.remove_patient(detected)
            to_bay.remove_patient(undetected)
            from_bay.add_patient(undetected)
        to_bay.add_patient(detected)

    def move_patients(self, ward: Ward):
        max_capacity = ward.non_isobays[0].capacity
        # Move infected patients from least infected bay to the most infected bay
        bays_sort = ward.non_isobays
        bays_sort = sorted(bays_sort, key=lambda b: b.num_of_detected)
        i = 0
        j = len(ward.non_isobays) - 1
        while True:
            if i == j:
                break
            if bays_sort[i].num_of_detected == 0 or bays_sort[i].num_of_patients == 0:
                i += 1
                continue
            if bays_sort[j].num_of_detected == max_capacity:
                j -= 1
                continue
            self.switch_infected(bays_sort[i], bays_sort[j])
