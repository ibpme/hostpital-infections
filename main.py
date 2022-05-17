"""
Program python untuk replikasi Agent Based Model untuk infeksi MRSA dalam rumah sakit.
Dibuat untuk Bimbingan Tugas Akhir
"""
__author__ = "Iman-Budi Pranakasih (10118004)"
import numpy as np
from matplotlib import pyplot as plt
import agents_enviroments

bays = [agents_enviroments.Bay() for _ in range(6)]
ward = agents_enviroments.Ward(bays, C=0.117, V=1, m=0.67, k=0.4)
ward.set_treatment_prob(0.7)

patient_generator = agents_enviroments.PatientGenerator()
patient_generator.set_var(poisson_lambda=7, gamma_k=6, gamma_scale=1)

# patient_generator.generate_sequence(colonized_prob=0)
# patient_generator.show_admit()
# patient_generator.show_length_stay()
# patient_generator.reset_history()

time = np.arange(350)
for t in time:
    ward.remove_patients()
    ward.screen_patients_get_results()
    patients = patient_generator.generate(colonized_prob=0.1)
    ward.admit_patients(patients=patients)
    ward.generate_transmission()
    ward.generate_treatment()
    ward.update_history("num_total", ward.total_patients)
    ward.forward_time()


plt.figure(figsize=(16, 5))
history = ward.history_sequence()
admission = np.array(history["admission"])
colonized = np.array(history["colonized"])
total = np.array(history["total"])
new_infections = np.array(history["new_infections"])
non_primary_cases = []
for admited_patients in ward.history["admission"]:
    col_admited_patient = 0
    for patient in admited_patients:
        col_admited_patient += patient.colonisation_status
    non_primary_cases.append(col_admited_patient)
non_primary_cases = np.array(non_primary_cases)
primary_cases = admission-non_primary_cases
legend = []
plt.plot(time, total, color='blue')
legend.append("Total")

plt.plot(time, colonized, color='red')
legend.append("Colonized")

# plt.plot(time, primary_cases, color="yellow")
# legend.append("Primary Cases")

# plt.plot(time, new_infections, color="purple")
# legend.append("New Infection (Secondary Case)")

# plt.plot(time, admission, color="green")
# legend.append("Admited")

plt.legend(legend)
plt.xlabel("Days")
plt.ylabel("Patients")
plt.show()
