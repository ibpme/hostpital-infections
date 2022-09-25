from __future__ import annotations
from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from .patient import Patient


class Bay:
    num_of_bays = 0

    def __init__(self, capacity=6):
        Bay.num_of_bays += 1
        self.id = Bay.num_of_bays
        self.capacity = capacity
        self.patients: List[Patient] = []

    @property
    def num_of_patients(self):
        """Number of patients inside bay"""
        return len(self.patients)

    @property
    def is_full(self):
        """Check is the bay is at full capacity"""
        return len(self.patients) == self.capacity

    def add_patient(self, patient):
        from .patient import Patient
        if not isinstance(patient, Patient):
            raise TypeError(f"{type(patient)} is not of Patient Type")
        if self.is_full:
            raise Exception(
                "Bay is at full capacity cannot add more patients !")
        patient.set_location(self)
        self.patients.append(patient)
        return

    def remove_patient(self, patient):
        from .patient import Patient
        if not isinstance(patient, Patient):
            raise TypeError(f"{type(patient)} is not of Patient Type")
        self.patients.remove(patient)
        return

    @property
    def is_isobay(self):
        return isinstance(self, IsolationBay)


class IsolationBay(Bay):
    num_of_isobays = 0

    def __init__(self):
        super().__init__(capacity=1)
        IsolationBay.num_of_isobays += 1


if __name__ == "__main__":
    print("Testing module")
    print(Bay().is_isobay)
    print(IsolationBay().is_isobay)
    print("Done")
