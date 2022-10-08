from __future__ import annotations
from typing import TYPE_CHECKING, List
__author__ = "Iman-Budi Pranakasih (10118004)"
from copy import copy

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
        # Hidden detection are use to store patient colonization stateat screening time
        self.hidden_detection_status = None
        self.location = None
        # According to the paper this will have an inital gamma distribution and will change as each time interval passes.
        # Used to avoid 0 time length of stay
        self.length_stay = length_stay
        # Time is length of patient stay after admission
        self.time = 0
        # Time after screening/testing
        self.result_time = None
        # Treatment time
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
        self.colonisation_status = np.random.choice([1, 0], p=[prob, 1 - prob])
        if self.colonisation_status:
            return self
        return

    def screen_test(self, length=3, interval=4):
        # ? Is it possible to make test length not bounded by interval ?
        # ? ^^^  Needs multiple hidden detection status for the patient
        """Apply screening process to patient with a certain interval with (length) of time until result"""
        if length >= interval:
            raise Exception(
                "Length of test cannot be greater or equal to interval")
        # Check if patient has been screened and awaiting result
        if self.detection_status == 2:
            # Don't screen patient again
            return None
        # If patient have not been screened with
        # Patient are screened at least one day after admission
        # and are screened every interval days
        # If patient is scheduled for screening and not yet detected
        if(self.time % interval == 1 and self.detection_status == 0):
            # Assign when patient will get result and set detection status
            self.result_time = self.time + length
            self.detection_status = 2
            # Test 100% sensitivity
            # (Hidden detection is set to remember the state of colonized patient)
            self.hidden_detection_status = self.colonisation_status
            return self
        return None

    def get_result(self):
        """Get result of each screened patient"""
        # Check if patient has been screened/tested
        if self.detection_status == 2:
            # Check if patient result time is met
            if self.result_time == self.time:
                # Assign result (hidden_detection_status) to patient
                self.detection_status = self.hidden_detection_status
                self.result_time = None
                self.hidden_detection_status = None
                # If detected assign treatment and colonisation_status
                if self.detection_status == 1:
                    self.colonisation_status = 1
                    self.decolonisation_status = 1
                    return self
        #  Dont return if not yet screened or not yet detected
        return None

    def check_healed(self, prob=0.9):
        """
        This function will heal the paient given a probability
        for patient to recover from the disease and discharged.
        Note : Giving treament should be a increasing probability with respect to
        the time patients is in the ward
        """
        healed = np.random.choice([1, 0], p=[prob, 1 - prob])
        if healed:
            self.colonisation_status = 0
            self.detection_status = 0
            self.decolonisation_status = 0
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
        self.poisson_lambda = poisson_lambda
        self.gamma_k = gamma_k
        self.gamma_scale = gamma_scale
        self.colonized_prob = colonized_prob
        self.use_col_dist = False
        self.col_gamma_k = None
        self.col_gamma_scale = None
        self.reset_history()

    def set_col_length_dist(self, gamma_k=None, gamma_scale=None):
        """Set the colonized patient length of stay distributions to use a different distribution
        from the uncolonized patient

        Parameters
        ----------
        gamma_k : float, optional
        gamma_scale : float, optional

        Raises
        ------
        ValueError
            Invalid gamma distribution
        """
        self.use_col_dist = True
        if not gamma_k or not gamma_scale:
            raise ValueError("Invalid gamma_k and gamma_scale")
        self.col_gamma_k = gamma_k
        self.col_gamma_scale = gamma_scale

    def reset_history(self):
        self.admission_dist: List[int] = []
        self.length_stay_dist: List[int] = []

    def set_var(self, poisson_lambda=3, gamma_k=5, gamma_scale=1):
        """Set variable for admission rate (poisson distribution
        and length of stay (gamma distribution)
        """
        self.poisson_lambda = poisson_lambda
        self.gamma_k = gamma_k
        self.gamma_scale = gamma_scale

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
            colonized_prob = self.colonized_prob

        patients_array = []

        # Get the number of patients admited in a day
        num_admit_patients = np.random.poisson(self.poisson_lambda)

        for _ in range(num_admit_patients):
            # Generate the patient infection status
            colonized_status = np.random.choice(
                [1, 0], p=[colonized_prob, 1 - colonized_prob])
            # Get the patients length of stay from the gamma distribution
            if colonized_status and self.use_col_dist:
                length_stay = np.random.gamma(
                    self.col_gamma_k, scale=self.col_gamma_scale)
            else:
                length_stay = np.random.gamma(
                    self.gamma_k, scale=self.gamma_scale)
            # Generate the patients
            patients_array.append(
                Patient(colonisation_status=colonized_status, length_stay=length_stay))
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
            colonized_prob = self.colonized_prob
        # Get the patients for each day
        patient_sequence = [self.generate(
            colonized_prob=colonized_prob) for _ in range(time)]
        for patient_arr in patient_sequence:
            self.admission_dist.append(len(patient_arr))
            for patient in patient_arr:
                self.length_stay_dist.append(patient.length_stay)
        return patient_sequence

    def show_admit(self):
        """Show admission rate distribution"""
        dist_pos = self.admission_dist
        size = np.array(dist_pos, dtype=object).size
        print(size)
        plt.hist(dist_pos, weights=np.ones(size) / size)
        plt.title("Poisson Discrete")
        plt.xlabel("Num of patient admited each day")
        plt.ylabel("Probability distribution")
        plt.show()

    def show_length_stay(self):
        """Show length of stay distribution"""
        dist_gamma = self.length_stay_dist
        size = np.array(dist_gamma, dtype=object).size
        print(size)
        plt.hist(dist_gamma, weights=np.ones(size) / size)
        plt.title("Gamma Distribution")
        plt.xlabel("Length of stay ")
        plt.ylabel("Probability distribution")
        plt.show()
