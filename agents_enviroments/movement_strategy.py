from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import math
from copy import deepcopy
if TYPE_CHECKING:
    from .bay import Bay
    from .ward import Ward
    from .patient import Patient


def change_patient_location(patient: Patient, new_bay: Bay):
    """Change patients location from one bay to another"""
    # if not isinstance(patient, Patient):
    #     raise TypeError(f"{type(patient)} is not of Patient Type")
    # if not isinstance(new_bay, Bay):
    #     raise TypeError(f"{type(new_bay)} is not of Bay Type")
    old_bay = patient.location
    old_bay.remove_patient(patient)
    new_bay.add_patient(patient)


def switch_patients_location(patient: Patient, other_patient: Patient):
    bay = patient.location
    other_bay = other_patient.location
    bay.remove_patient(patient)
    other_bay.remove_patient(other_patient)
    bay.add_patient(other_patient)
    other_bay.add_patient(patient)


class MovementStrategy(ABC):
    @abstractmethod
    def move_patients(self, ward: Ward):
        pass


class IsolateInfectedStrategy(MovementStrategy):

    def __str__(self) -> str:
        return "IsolateInfectedStrategy"

    def move_patients(self, ward: Ward):
        # Find available isolation bay in ward
        available_isobay = [
            isobay for isobay in ward.isobays if not isobay.is_full]
        for patient in ward.patients:
            if len(available_isobay) == 0:
                return
            if patient.detection_status and not patient.location.is_isobay:
                change_patient_location(patient, available_isobay.pop())


class GroupInfectedStrategy(MovementStrategy):

    def __str__(self) -> str:
        return "GroupInfectedStrategy"

    def switch_detected_undetected(self, from_bay: Bay, to_bay: Bay):
        # If no undetected patients , we will move the patient if it is avaliable
        if to_bay.num_of_undetected == 0:
            if to_bay.is_full:
                # If bay is full then it is all detected. calling this function without detected checking throws exception
                raise Exception(
                    "Bad Function Call : To bay {} is full of detected patients".format(to_bay.id))
            # If available then we will move patients to the bay
            detected = deepcopy(from_bay).detected.pop()
            detected = from_bay.get_patient(detected.id)
            change_patient_location(detected, to_bay)
            return
        #  Prevent unwanted mutablity
        detected = deepcopy(from_bay).detected.pop()
        undected = deepcopy(to_bay).undetected.pop()
        detected = from_bay.get_patient(detected.id)
        undected = to_bay.get_patient(undected.id)
        switch_patients_location(detected, undected)

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
            if bays_sort[i].num_of_detected == 0:
                i += 1
                continue
            if bays_sort[j].num_of_detected == max_capacity:
                j -= 1
                continue
            self.switch_detected_undetected(bays_sort[i], bays_sort[j])
