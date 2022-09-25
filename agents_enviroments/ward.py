from __future__ import annotations
from typing import TYPE_CHECKING, List
from agents_enviroments.movement_strategy import MovementStrategy
from agents_enviroments.parameters import Parameters
import numpy as np

if TYPE_CHECKING:
    from .patient import Patient
    from .bay import Bay
    from .history import History


class Ward:

    def __init__(self, bays: List[Bay], params: Parameters):
        self.bays = bays
        self.params = params
        # Dynamic Atributes in ward for Patients Status
        self.new_patients: List[Patient] = []
        self.new_infections: List[Patient] = []
        self.screened_patients: List[Patient] = []
        self.new_detected_patients: List[Patient] = []
        self.patients_removed: List[Patient] = []
        self.healed_patients: List[Patient] = []
        self.time = 0

    @property
    def isobays(self) -> List[Bay]:
        return [bay for bay in self.bays if bay.is_isobay]

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
        """Colonized patients inside bays in ward (detected)"""
        col_patients = []
        if not self.bays:
            return col_patients
        for bay in self.bays:
            for patient in bay.patients:
                if patient.colonisation_status == 1:
                    col_patients.append(patient)
        return col_patients

    @property
    def total_new_infections(self):
        return len(self.new_infections)

    @property
    def patients(self) -> List[Patient]:
        all_patients = []
        if not self.bays:
            return all_patients
        for bay in self.bays:
            for patient in bay.patients:
                all_patients.append(patient)
        return all_patients

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
        """Total colonized patients inside bays in ward (detected)"""
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
                prob = self.params.isolation_prob
                # Isolation bay probability
                if np.random.choice([1, 0], p=[prob, 1-prob]):
                    bay.add_patient(patient)
                    return patient
                else:
                    continue
            else:
                bay.add_patient(patient)
                return patient
        else:
            # All bays are full / not available
            return None

    def admit_patients(self, patients: List[Patient]) -> int:
        """Same as admit_patient but takes an array and updates history

        Parameters
        ----------
        patients : [Patients]
            list of patients
        returns:
            number of patient not admited
        """
        patients_not_admited = 0
        patients_admited = []
        for patient in patients:
            patient_admited = self.admit_patient(patient)
            if not patient_admited:
                patients_not_admited += 1
            else:
                patients_admited.append(patient_admited)
        self.new_patients = patients_admited
        return patients_not_admited

    def remove_patients(self) -> int:
        """Discharge/remove patients when length of stay is met
        """
        patients_removed = []
        for bay in self.bays:
            for patient in bay.patients:
                if patient.remaining_stay == 0:
                    bay.remove_patient(patient)
                    patients_removed.append(patient)
        self.patients_removed = patients_removed
        return patients_removed

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

        C = self.params.C
        V = self.params.V
        m = self.params.m
        k = self.params.k
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
        This function generates new infections. (Undetected)
        """
        new_infections = []
        suc_patient_arr = self.suc_patients
        col_patient_arr = self.col_patients
        for suc_patient in suc_patient_arr:
            for col_patient in col_patient_arr:
                trans_prob = self.exp_trans_prob(
                    self.transmission_prob(col_patient, suc_patient))
                new_infection = suc_patient.infect_prob(trans_prob)
                if new_infection:
                    new_infections.append(new_infection)
                    break
            continue
        self.new_infections = new_infections
        return

    def generate_treatment(self, discharge_healed=True):
        """Generate treatment for each patient and remove if patient is healed"""
        healed_patients = []
        for bay in self.bays:
            for patient in bay.patients:
                if patient.detection_status == 1:
                    healed = patient.give_treatment(self.params.treatment_prob)
                    if healed:
                        # Should patient be removed if healed ?
                        healed_patients.append(healed)
                        if discharge_healed:
                            healed.location.remove_patient(healed)
        self.healed_patients = healed_patients

    def screen_patients(self):
        """Screen each patient in ward is patient is not screened yet
        This might change the patient detection status
         """
        screened_patients = []
        for bay in self.bays:
            for patient in bay.patients:
                screened_patient = patient.screen_test()
                if screened_patient:
                    screened_patients.append(screened_patient)
        self.screened_patients = screened_patients

    def get_patient_results(self):
        """Get the result if available.
        This might change the patient detection status
         """
        detected_patients = []
        for bay in self.bays:
            for patient in bay.patients:
                detected = patient.get_result()
                if detected:
                    detected_patients.append(detected)
        self.new_detected_patients = detected_patients

    def forward_time(self):
        """Forward all patient time"""
        self.time += 1
        for bay in self.bays:
            for patient in bay.patients:
                patient.time += 1

    def history_dict(self):
        "Save the state of the ward and patients to history in dictionary"
        hist = {
            "new_patients": len(self.new_patients),
            "colonized": self.total_col_patients,
            "new_infections": len(self.new_infections),
            "screened_patients": len(self.screened_patients),
            "new_detected_patients": len(self.new_detected_patients),
            "removed_patients": len(self.patients_removed),
            "healed_patients": len(self.healed_patients),
            "total": self.total_patients
        }
        return hist

    def occupancy_stats(self):
        """Show current patients capacity"""
        stats = {}
        for i, bay in enumerate(self.bays):
            bay_key = "Bay-{}".format(i+1)
            stats.update(
                {bay_key: {"Patients": bay.num_of_patients, "Capacity": bay.capacity}})
        stats.update({"Total": self.total_patients, "Capacity": self.capacity})
        return stats

    def move_patients(self, movement_strategy: MovementStrategy):
        movement_strategy.move_patients(self)
