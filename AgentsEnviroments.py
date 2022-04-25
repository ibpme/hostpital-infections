__author__ = "Iman-Budi Pranakasih (10118004)"

import numpy as np
import matplotlib.pyplot as plt


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
        self.hidden_detection_status = None
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

    @property
    def remaining_stay(self):
        """Time remaining from length of stay"""
        return int(self.length_stay - self.time)

    def set_location(self, bay):
        """Move patient to bay"""
        if not isinstance(bay, Bay):
            raise TypeError(f"{type(bay)} is not of Bay Type")
        self.location = bay

    def infect_prob(self, prob):
        """Infect the patient and change colonisation status with a probability"""
        if self.colonisation_status == 1:
            raise Exception("Patient already colonised")
        self.colonisation_status = np.random.choice([1, 0], p=[prob, 1-prob])
        return self.colonisation_status

    def screen_test(self, length=2):
        """Apply screening process to patient, with (length )of time until result"""
        # If screening interval is 4
        if (self.time == 2, self.time % 4) and self.time > 0:
            # If patient have
            if self.detection_status != 2:
                self.result_time = self.time + length
                self.detection_status = 2
                # Test 100% sensitivity (hidden detection is set to remember the state of colonized patient)
                if self.colonisation_status:
                    self.hidden_detection_status = 1
                else:
                    self.hidden_detection_status = 0
                return True
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
            return True
        return False

    def give_treatment(self):
        # TODO : Fix function according to paper
        prob = 0.9
        # This function will give a probability for patient to recover from the disease and discharged.
        healed = np.random.choice([1, 0], p=[prob, 1-prob])
        if healed:
            self.colonisation_status = 0
            self.detection_status = 0
        return healed

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


class Bay:
    num_of_bays = 0

    def __init__(self, capacity=6):
        Bay.num_of_bays += 1
        self.id = Bay.num_of_bays
        self.capacity = capacity
        self.patients: list[Patient] = []

    @property
    def num_of_patients(self):
        """Number of patients inside bay"""
        return len(self.patients)

    @property
    def is_full(self):
        """Check is the bay is at full capacity"""
        return len(self.patients) == self.capacity

    def add_patient(self, patient):
        if not isinstance(patient, Patient):
            raise TypeError(f"{type(patient)} is not of Patient Type")
        if self.is_full:
            raise Exception(
                "Bay is at full capacity cannot add more patients !")
        patient.set_location(self)
        self.patients.append(patient)
        return

    def remove_patient(self, patient):
        if not isinstance(patient, Patient):
            raise TypeError(f"{type(patient)} is not of Patient Type")
        self.patients.remove(patient)
        return


class IsolationBay(Bay):
    num_of_isobays = 0

    def __init__(self):
        super().__init__(capacity=1)
        IsolationBay.num_of_isobays += 1


class Ward:

    def __init__(self, bays: 'list[Bay]', **params):
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
    def suc_patients(self) -> "list[Patient]":
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
    def col_patients(self) -> "list[Patient]":
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
    def total_patients(self):
        """Total patients inside bays in ward"""
        patients = 0
        if not self.bays:
            return 0
        for bay in self.bays:
            patients += bay.num_of_patients
        return patients

    @property
    def total_col_patients(self):
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
            boolean if patient is admited 
        """

        # Choose an available bay for patient i
        for bay in self.bays:
            if bay.is_full:
                continue
            else:
                bay.add_patient(patient)
                return True
        else:
            # print("All bays are full, patient cannot be admited")
            return False

    def admit_patients(self, patients: 'list[Patient]') -> int:
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

    def remove_patients(self):
        """Discharge/remove patients when length of stay is met
        """
        patients_removed = 0
        for bay in self.bays:
            for patient in bay.patients:
                if patient.remaining_stay == 0:
                    bay.remove_patient(patient)
                    patients_removed += 1
        return patients_removed

    def change_patient_location(self, patient, new_bay):
        """Change patients location from one bay to another"""
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


class PatientGenerator:

    def __init__(self, poisson_lambda=None, gamma_k=None, gamma_scale=None, colonized_prob=None) -> None:
        """Generate list of patients with specific attributes and probability distributions 
        """
        self._poisson_lambda = poisson_lambda
        self._gamma_k = gamma_k
        self._gamma_scale = gamma_scale
        self._colonized_prob = colonized_prob
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

    def generate(self, colonized_prob: float = None) -> "list[Patient]":
        """Generate list of patients to be admited to the ward usually in one time unit

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
            [1, 0], p=[colonized_prob, 1-colonized_prob], size=num_admit_patients,)
        patients_array = []
        for status, length_stay in zip(colonized_status_sequence, length_stay_sequence):
            patients_array.append(
                Patient(colonisation_status=status, length_stay=length_stay))
        self.history["admission_sequence"] = np.append(
            self.history["admission_sequence"], num_admit_patients)
        self.history["length_stay_dist"] = np.append(
            self.history["length_stay_dist"], length_stay_sequence)
        self.history["colonized_sequence"] = np.append(
            self.history["colonized_sequence"], int(sum(colonized_status_sequence)))
        return patients_array

    def generate_sequence(self, colonized_prob: float = None, time=350) -> "list[Patient]":
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
            colonized_prob=colonized_prob) for _i in range(time)]
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
