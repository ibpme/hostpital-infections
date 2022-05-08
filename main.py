"""
Program python untuk replikasi Agent Based Model untuk infeksi MRSA dalam rumah sakit. 
Dibuat untuk Bimbingan Tugas Akhir
"""
__author__ = "Iman-Budi Pranakasih (10118004)"

import numpy as np
from matplotlib import pyplot as plt
import agents_enviroments

bays = [agents_enviroments.Bay() for _ in range(6)]
ward = agents_enviroments.Ward(bays, C=0.03, V=1, m=0.67, k=0.4)

patient_generator = agents_enviroments.PatientGenerator()
patient_generator.set_var(poisson_lambda=5, gamma_k=4, gamma_scale=1)

time = np.arange(350)
for t in time:
    ward.remove_patients()
    ward.screen_patients_get_results()
    patients = patient_generator.generate(colonized_prob=0.02)
    ward.admit_patients(patients=patients)
    ward.generate_transmission()
    ward.update_history()
    ward.forward_time()

plt.figure(figsize=(16, 5))
plt.plot(time, ward.history["admission_sequence"])
plt.plot(time, ward.history["colonized_sequence"], color='red')
plt.legend(["Total", "Colonised", "New"])
plt.xlabel("Days")
plt.ylabel("Patients")
plt.show()
