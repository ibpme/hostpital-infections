from __future__ import annotations
from typing import TYPE_CHECKING, List
__author__ = "Iman-Budi Pranakasih (10118004)"

import numpy as np
from matplotlib import pyplot as plt

if TYPE_CHECKING:
    from .bay import Bay


class Patient:
    num_of_patients = 0

    def __init__(self, colonisation_status: int = 0, detection_status: int = 0, decolonisation_status: int = 0, length_stay: int = 10):
        """
        States of a patient are grouped into the following categories:

        - Colonisation status, which includes two states: (0) susceptible and colonised (1).
        - Detection status, which contains three states: undetected (0),screened but awaiting result(2), and detected (1).
        - Decolonisation treatment status, which has two states: receiving decolonisation treatment (1) and not receiving decolonisation treatment (0).
        - Location status, that is, which bay or isolation bed. (Bay) 
        """
        Patient.num_of_patients += 1
        self.id = Patient.num_of_patients
        self.colonisation_status = colonisation_status
        self.detection_status = detection_status
        self.decolonisation_status = decolonisation_status
        # self.hidden_detection_status = None
        self.location = None
        # According to the paper this will have an inital gamma distribution and will change as each time interval passes.
        # Used to avoid 0 time length of stay
        if length_stay == 0:
            length_stay = 1
        self.length_stay = length_stay
        # Time is length of patient stay after admission
        self.time = 0
        # Time after screening/testing
        self.result_time = None
        # Treatment Probability
        self.treatment_prob = 0.3
        self.treatment_time = None

    @property
    def remaining_stay(self):
        """Time remaining from length of stay"""
        return int(self.length_stay - self.time)

    def set_location(self, bay: Bay):
        from .bay import Bay
        """Move patient to bay"""
        if not isinstance(bay, Bay):
            raise TypeError(f"{type(bay)} is not of Bay Type")
        self.location = bay

    def infect_prob(self, prob):
        """Infect the patient and change colonisation status with a probability"""
        if self.colonisation_status == 1:
            raise Exception("Patient already colonised")
        self.colonisation_status = np.random.choice([1, 0], p=[prob, 1-prob])
        if self.colonisation_status:
            return self
        return

    def screen_test(self, length=3, interval=4):
        """Apply screening process to patient with a certain interval with (length) of time until result"""
        if length >= interval:
            raise Exception("Length of test cannot be greater than interval")
        if (self.time == length, self.time % interval == 0) and self.time > 0:
            # If patient have not been screened
            if self.detection_status != 2:
                self.result_time = self.time + length
                self.detection_status = 2
                # Test 100% sensitivity (hidden detection is set to remember the state of colonized patient)
                self.hidden_detection_status = self.colonisation_status
                return self
        return False

    def get_result(self):
        """Get result of each screened patient"""
        if not self.result_time:
            return False
        # Check if result time is due
        if self.result_time - self.time == 0:
            self.detection_status = self.hidden_detection_status
            self.result_time = None
            self.hidden_detection_status = None
            if self.detection_status == 1:
                return self
        return False

    def check_healed(self, prob=0.9):
        """
        This function will heal the paient given a probability 
        for patient to recover from the disease and discharged.
        Note : Giving treament should be a increasing probability with respect to 
        the time patients is in the ward
        """
        healed = np.random.choice([1, 0], p=[prob, 1-prob])
        if healed:
            self.colonisation_status = 0
            self.detection_status = 0
        return healed

    def give_treatment(self, treatment_prob):
        if self.treatment_time is not None:
            if self.treatment_time == 0:
                if self.check_healed(treatment_prob):
                    return self
            else:
                self.treatment_time -= 1
        else:
            self.treatment_time = 5
        return None

    def __repr__(self):
        if self.location:
            return f"Patient<{self.id}>,\
                Bay<{self.location.id}>\n\
                Colonized: {self.colonisation_status}\n\
                Detection: {self.detection_status}\n\
                Decolonisation: {self.decolonisation_status}"
        else:
            return f"Patient<{self.id}>,\
                Bay<NotAssigned>\n\
                Colonized: {self.colonisation_status}\n\
                Detection: {self.detection_status}\n\
                Decolonisation: {self.decolonisation_status}"


class PatientGenerator:

    def __init__(self, poisson_lambda=None, gamma_k=None, gamma_scale=None, colonized_prob=None) -> None:
        """Generate list of patients with specific attributes and probability distributions 
        """
        self._poisson_lambda = poisson_lambda
        self._gamma_k = gamma_k
        self._gamma_scale = gamma_scale
        self._colonized_prob = colonized_prob
        self.primary_cases = []
        self.reset_history()

    def reset_history(self):
        self.history = {
            "admission_sequence": np.array([]),
            "length_stay_dist": np.array([], dtype=int),
            "colonized_sequence": np.array([], dtype=int),
        }

    def set_var(self, poisson_lambda=3, gamma_k=5, gamma_scale=1):
        """Set variable for admission rate (poisson distribution
        and length of stay (gamma distribution)
        """
        self._poisson_lambda = poisson_lambda
        self._gamma_k = gamma_k
        self._gamma_scale = gamma_scale

    def generate(self, colonized_prob: float = None) -> List[Patient]:
        """Generate list of patients to be admited to the ward usually in one time unit
        On admission, the patient has a certain probability of
        being colonised with MRSA (ie, primary case) or not
        (ie, susceptible patient). However, the patient's MRSA status
        is unknown to the ward until the patient is screened. The
        susceptibility of the patient to colonisation is also determined at admission
        Parameters
        ----------
        colonized_prob : float, optional
            Probability/Distribution of colonization during admission, by default None

        Returns
        -------
        list[Patient]
            list of patients
        """
        if not colonized_prob and colonized_prob != 0:
            colonized_prob = self._colonized_prob

        num_admit_patients = np.random.poisson(self._poisson_lambda)
        length_stay_sequence = np.random.gamma(
            self._gamma_k, scale=self._gamma_scale, size=num_admit_patients)
        colonized_status_sequence = np.random.choice(
            [1, 0], p=[colonized_prob, 1-colonized_prob], size=num_admit_patients)
        patients_array = []
        for status, length_stay in zip(colonized_status_sequence, length_stay_sequence):
            patients_array.append(
                Patient(colonisation_status=status, length_stay=length_stay))
        return patients_array

    def generate_sequence(self, colonized_prob: float = None, time=350) -> List[List[Patient]]:
        """Generate list of patients to be admited to the ward inside sequence 

        Parameters
        ----------
        colonized_prob : float, optional
            Probability/Distribution of colonization during admission, by default None

        Returns
        -------
        list[list[Patient]]
            sequence of list of patients
        """
        if not colonized_prob and colonized_prob != 0:
            colonized_prob = self._colonized_prob
        patient_sequence = [self.generate(
            colonized_prob=colonized_prob) for _ in range(time)]
        primary_cases = []
        for patient_arr in patient_sequence:
            self.history["admission_sequence"] = np.append(
                self.history["admission_sequence"], len(patient_arr))
            self.history["length_stay_dist"] = np.append(self.history["length_stay_dist"], [
                patient.length_stay for patient in patient_arr])
        for patient_admit in patient_sequence:
            for patient in patient_admit:
                if patient.colonisation_status == 1:
                    primary_cases.append(patient)
        self.primary_cases = primary_cases
        return patient_sequence

    def show_admit(self):
        """Show admission rate distribution"""
        dist_pos = self.history["admission_sequence"]
        plt.hist(dist_pos, weights=np.ones(dist_pos.size)/dist_pos.size)
        plt.title("Poisson Discrete")
        plt.xlabel("Num of patient admited each day")
        plt.ylabel("Probability distribution")
        plt.show()

    def show_length_stay(self):
        """Show length of stay distribution"""
        dist_gamma = self.history["length_stay_dist"]
        plt.hist(dist_gamma, weights=np.ones(dist_gamma.size)/dist_gamma.size)
        plt.title("Gamma Distribution")
        plt.xlabel("Length of stay ")
        plt.ylabel("Probability distribution")
        plt.show()
