from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bay import IsolationBay, Bay
    from ward import Ward
    from patient import Patient


class MovementStrategy(ABC):

    def change_patient_location(self, patient: Patient, new_bay: Bay):
        """Change patients location from one bay to another"""
        if not isinstance(patient, Patient):
            raise TypeError(f"{type(patient)} is not of Patient Type")
        if not isinstance(new_bay, Bay):
            raise TypeError(f"{type(new_bay)} is not of Bay Type")
        old_bay = patient.location
        old_bay.remove_patient(patient)
        new_bay.add_patient(patient)

    @abstractmethod
    def move_patients(self, ward: Ward):
        raise NotImplementedError()


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
