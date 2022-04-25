"""
Program python untuk replikasi Agent Based Model untuk infeksi MRSA dalam rumah sakit. 
Dibuat untuk Bimbingan Tugas Akhir
"""
__author__ = "Iman-Budi Pranakasih (10118004)"

# TODO: -Make a running simulation of admision rate with a ditribustion of colonised and suceptible patient

import math
from numpy.random import gamma

from AgentsEnviroments import Patient, Bay, IsolationBay,Ward
bays = []
def total_patients(bays=bays):
    patients = 0
    for bay in bays:
        patients += len(bay.patients)
    return patients


def total_col_patients(bays=bays):
    col_patients = 0
    for bay in bays:
        for patient in bay.patients:
            col_patients += patient.colonisation_status
    return col_patients


def transmission_prob(patient_c, patient_s):
    if not isinstance(patient_c, Patient):
        raise TypeError(f"{type(patient_c)} is not of Patient Type")
        return
    if not isinstance(patient_s, Patient):
        raise TypeError(f"{type(patient_s)} is not of Patient Type")
        return
    if not patient_c.colonisation_status:
        raise Exception("patient_c is not a colonised patient")
        return
    if patient_s.colonisation_status == 1:
        raise Exception("patient_s is not a suceptible patient")
        return
    C = 0.1
    V = 5
    m = 0.67
    k = 0.4
    n_ward = total_patients()

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
        lambda_t = C*V*(m/(n_bay-1) + (1-m)/(n_ward-1))
    if not col_detected and not same_bay:
        lambda_t = C*V*((1-m)/(n_ward-1))
    if col_detected and same_bay:
        lambda_t = C*V*k*(m/(n_bay-1) + (1-m)/(n_ward-1))
    if col_detected and not same_bay:
        lambda_t = C*V*k*((1-m)/(n_ward-1))

    return lambda_t


def exp_trans_prob(lambda_t):
    return math.exp(-lambda_t)


def change_patient_location(patient, new_bay):
    if not isinstance(patient, Patient):
        raise TypeError(f"{type(patient)} is not of Patient Type")
        return
    if not isinstance(new_bay, Bay):
        raise TypeError(f"{type(new_bay)} is not of Bay Type")
        return
    old_bay = patient.location
    old_bay.remove_patient(patient)
    new_bay.add_patient(patient)

    return


def admit_patient(patient, bay, k, theta):
    length_stay = round(int(gamma(k, scale=theta)))
    # k is shape thetha is scale
    patient.length_stay = length_stay
    new_patient = patient
    bay.add_patient(new_patient)
    return new_patient


def screen_patient(patient):
    screen_time = 2  # 48-72 hours according to the paper
    # TODO : This function needs to change the patient detection status 2 days after the screening
    patient.detection_status = 2
    patient.result_time = patient.time+screen_time


def main():
    # Create Bays and IsolationBays in Ward
    for _ in range(NUM_BAYS):
        bays.append(Bay())
    for _ in range(NUM_ISOLATION_BAY):
        bays.append(IsolationBay())


if __name__ == "__main__":
    NUM_BAYS = 6
    NUM_ISOLATION_BAY = 6
    screening_interval = 10  # days where patient is routinely screened

    main()
