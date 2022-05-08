from __future__ import annotations
from typing import TYPE_CHECKING, List
import numpy as np

if TYPE_CHECKING:
    from .patient import Patient
    from .bay import IsolationBay, Bay


class Ward:

    def __init__(self, bays: List[Bay], **params):
        if not params:
            raise TypeError(
                "Please initialize transmission variables C,V,m and k ")
        self.bays = bays

        self.history = {
            "admission_sequence": np.array([]),
            "colonized_sequence": np.array([], dtype=int),
            "new_infection_sequence": np.array([], dtype=int),
            "lambda": np.array([])
        }

        self.new_infections = 0
        self.lambda_seq = []

        self.C = params["C"]
        self.V = params["V"]
        self.m = params["m"]
        self.k = params["k"]

    @property
    def capacity(self):
        """Total ward capacity"""
        total_capacity = 0
        for bay in self.bays:
            total_capacity += bay.capacity
        return total_capacity

    @property
    def suc_patients(self) -> List[Patient]:
        """Suceptible patients inside bays in ward"""
        patients = []
        if not self.bays:
            return patients
        for bay in self.bays:
            for patient in bay.patients:
                if patient.colonisation_status == 0:
                    patients.append(patient)
        return patients

    @property
    def col_patients(self) -> List[Patient]:
        """Colonized patients inside bays in ward"""
        col_patients = []
        if not self.bays:
            return col_patients
        for bay in self.bays:
            for patient in bay.patients:
                if patient.colonisation_status == 1:
                    col_patients.append(patient)
        return col_patients

    @property
    def total_patients(self) -> List[Patient]:
        """Total patients inside bays in ward"""
        patients = 0
        if not self.bays:
            return 0
        for bay in self.bays:
            patients += bay.num_of_patients
        return patients

    @property
    def total_col_patients(self) -> List[Patient]:
        """Total colonized patients inside bays in ward"""
        col_patients = 0
        for bay in self.bays:
            for patient in bay.patients:
                col_patients += patient.colonisation_status
        return col_patients

    def admit_patient(self, patient):
        """Method for admiting patient.
        We use this, globally when admiting patients without worrying about 
        how the patient is admited. 
        We also implement how each patient is assigned to a bay here.

        Parameters
        ----------
        patient : Patient
            patient to be admited
        returns:
            boolean if the patient is admited 
        """

        # Choose an available bay for patient i
        from .bay import IsolationBay
        for bay in self.bays:
            if bay.is_full:
                continue
            if isinstance(bay, IsolationBay):
                prob = 0.01
                # Isolation bay probability
                if np.random.choice([1, 0], p=[prob, 1-prob]):
                    bay.add_patient(patient)
                    return True
            else:
                bay.add_patient(patient)
                return True
        else:
            # All bays are full / not available
            return False

    def admit_patients(self, patients: List[Patient]) -> int:
        """Same as admit_patient but takes an array

        Parameters
        ----------
        patients : [Patients]
            list of patients
        k: shape of gamma distribution
        scale : scale of gamma distribution

        returns:
            number of patient not admited
        """
        patients_not_admited = 0
        for patient in patients:
            patient_admited = self.admit_patient(patient)
            if not patient_admited:
                patients_not_admited += 1
        return patients_not_admited

    def remove_patients(self) -> int:
        """Discharge/remove patients when length of stay is met
        """
        patients_removed = 0
        for bay in self.bays:
            for patient in bay.patients:
                if patient.remaining_stay == 0:
                    bay.remove_patient(patient)
                    patients_removed += 1
        return patients_removed

    def change_patient_location(self, patient: Patient, new_bay: Bay):
        """Change patients location from one bay to another"""
        from .patient import Patient
        if not isinstance(patient, Patient):
            raise TypeError(f"{type(patient)} is not of Patient Type")
        if not isinstance(new_bay, Bay):
            raise TypeError(f"{type(new_bay)} is not of Bay Type")
        old_bay = patient.location
        old_bay.remove_patient(patient)
        new_bay.add_patient(patient)

        return

    def transmission_prob(self, patient_c: Patient, patient_s: Patient):
        """Transmission probabilty given a suceptible and colonised Patient pair"""
        from .patient import Patient
        if not isinstance(patient_c, Patient):
            raise TypeError(f"{type(patient_c)} is not of Patient Type")

        if not isinstance(patient_s, Patient):
            raise TypeError(f"{type(patient_s)} is not of Patient Type")

        if patient_c.colonisation_status == 0:
            raise Exception("patient_c is not a colonised patient")

        if patient_s.colonisation_status == 1:
            raise Exception("patient_s is not a suceptible patient")

        C = self.C
        V = self.V
        m = self.m
        k = self.k
        n_ward = self.total_patients

        s_bay = patient_s.location
        c_bay = patient_c.location
        # this redundancy is needed to avoid detecting patient awaiting result
        col_detected = patient_c.detection_status == 0

        if s_bay == c_bay:
            n_bay = len(patient_s.location.patients)
            same_bay = True
        else:
            same_bay = False

        if not col_detected and same_bay:
            lambda_t = C*V*((m/(n_bay-1)) + ((1-m)/(n_ward-1)))
        if not col_detected and not same_bay:
            lambda_t = C*V*((1-m)/(n_ward-1))
        if col_detected and same_bay:
            lambda_t = C*V*k*((m/(n_bay-1)) + ((1-m)/(n_ward-1)))
        if col_detected and not same_bay:
            lambda_t = C*V*k*((1-m)/(n_ward-1))
        return lambda_t

    @staticmethod
    def exp_trans_prob(lambda_t):
        """Exponential form of probability function"""
        return 1-np.math.exp(-lambda_t)

    def generate_transmission(self):
        """Generate the transmission reaction for each patient inside the ward.
        This function generates new infections.
        """
        new_infections = 0
        lambda_arr = []
        suc_patient_arr = self.suc_patients
        col_patient_arr = self.col_patients
        for suc_patient in suc_patient_arr:
            for col_patient in col_patient_arr:
                trans_prob = self.exp_trans_prob(
                    self.transmission_prob(col_patient, suc_patient))
                status = suc_patient.infect_prob(trans_prob)
                lambda_arr.append(trans_prob)
                new_infections += status
                if status:
                    break
            continue
        self.new_infections = new_infections
        self.lambda_seq = lambda_arr
        return new_infections

    def generate_treatment(self):
        """Generate treatment for each patient"""
        for bay in self.bays:
            for patient in bay.patients:
                if patient.detection_status == 1:
                    healed = patient.give_treatment()
                    if healed:
                        self.remove_patients(patient)

    def screen_patients_get_results(self):
        """Screen each patient in ward is patient is not screened yet
         and get the result if available"""
        for bay in self.bays:
            for patient in bay.patients:
                patient.screen_test()
                if patient.result_time:
                    patient.get_result()

    def update_history(self):
        """History of patients state sequence"""
        self.history["admission_sequence"] = np.append(
            self.history["admission_sequence"], self.total_patients)
        self.history["colonized_sequence"] = np.append(
            self.history["colonized_sequence"], self.total_col_patients)
        self.history["new_infection_sequence"] = np.append(
            self.history["new_infection_sequence"], self.new_infections)
        self.history["lambda"] = np.append(
            self.history["lambda"], self.lambda_seq)

    def forward_time(self):
        """Forward all patient time"""
        for bay in self.bays:
            for patient in bay.patients:
                patient.time += 1

    def occupancy_stats(self):
        """Show current patients capacity"""
        stats = {}
        for i, bay in enumerate(self.bays):
            bay_key = "Bay-{}".format(i+1)
            stats.update(
                {bay_key: {"Patients": bay.num_of_patients, "Capacity": bay.capacity}})
        stats.update({"Total": self.total_patients, "Capacity": self.capacity})
        return stats

    def move_patients(self):
        for bay in self.bays:
            for patient in bay.patients:
                pass