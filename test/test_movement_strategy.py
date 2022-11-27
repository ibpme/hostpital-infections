from agents_enviroments.movement_strategy import change_patient_location
from agents_enviroments.bay import Bay
from agents_enviroments.patient import Patient
from agents_enviroments.ward import Ward
from agents_enviroments.parameters import Parameters
import unittest


class TestMovementStrategy(unittest.TestCase):

    def setUp(self) -> None:
        params = Parameters(
            C=0.3, V=1, m=0.4, k=0.4, treatment_prob=0.9, isolation_prob=0.01, screen_interval=4, result_length=2)
        self.ward = Ward(bays=[Bay(), Bay()], params=params)
        num_of_patients = 10
        patients = []
        for _ in range(num_of_patients):
            patients.append(Patient())
        self.ward.admit_patients(patients)

    def test_change_location(self):
        # Test with 2 Bays and 10 Patients
        bay1 = self.ward.bays[0]
        bay2 = self.ward.bays[1]
        patient1 = bay1.patients[0]
        patient1_id = patient1.id
        patient2 = bay2.patients[0]
        patient2_id = patient2.id
        change_patient_location(patient1, bay2)
        change_patient_location(patient2, bay1)
        check1 = map(lambda x: bool(x.id == patient1_id), bay2.patients)
        check2 = map(lambda x: bool(x.id == patient2_id), bay1.patients)
        assert any(check1)
        assert any(check2)
        check3 = map(lambda x: bool(x.id == patient1_id), bay1.patients)
        check4 = map(lambda x: bool(x.id == patient2_id), bay2.patients)
        self.assertFalse(any(check3))
        self.assertFalse(any(check4))


if __name__ == '__main__':
    unittest.main()
