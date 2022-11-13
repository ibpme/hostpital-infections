# %%
import random
from agents_enviroments import movement_strategy
import numpy as np
from matplotlib import pyplot as plt
import agents_enviroments
from agents_enviroments import History
from agents_enviroments.movement_strategy import GroupInfectedStrategyy, IsolateInfectedStrategy
from tqdm.auto import tqdm
import pandas as pd
import os


def main(seed, mod, generation_seed=10):
    num_of_bays = 10
    num_of_isobays = 6
    colonized_prob_on_admit = 0.05
    time = 150
    # strategies = [GroupInfectedStrategyy()]

    np.random.seed(generation_seed)
    random.seed(generation_seed)
    params = agents_enviroments.Parameters(
        C=0.3, V=1, m=mod, k=0.4, treatment_prob=0.9, isolation_prob=0.01, screen_interval=4, result_length=2)

    patient_generator = agents_enviroments.PatientGenerator()
    patient_generator.set_var(
        poisson_lambda=5, gamma_k=7, gamma_scale=1, seed=generation_seed)
    patient_generator.set_col_length_dist(
        gamma_k=11, gamma_scale=1, seed=generation_seed)
    patient_sequence = patient_generator.generate_sequence(
        colonized_prob=colonized_prob_on_admit, time=time)
    # %%
    bays = [agents_enviroments.Bay() for _ in range(num_of_bays)]
    isobays = [agents_enviroments.IsolationBay()
               for _ in range(num_of_isobays)]
    bays += isobays
    ward = agents_enviroments.Ward(bays, params=params)
    # %%
    np.random.seed(seed)
    random.seed(seed)
    history = History()
    history.reset()
    for patients in patient_sequence:
        ward.remove_patients()
        ward.screen_patients()
        ward.get_patient_results()
        ward.admit_patients(patients=patients)
        ward.generate_transmission()
        ward.generate_treatment()
        history.add_from_dict(ward.history_dict())
        ward.forward_time()

    # %%

    filename = "output_m.csv"
    result_dict = {
        "primary_cases": [ward.primary_cases],
        "secondary_cases": [ward.secondary_cases],
        "total_screens": [sum(history.screened)],
        "total_detection": [sum(history.new_detected)],
        "total_healed": [sum(history.healed)],
        "seed": [seed],

    }

    result_dict.update(params.__dict__)
    df = pd.DataFrame.from_dict(result_dict)
    if os.path.exists(filename):
        pd.concat([pd.read_csv(filename), df], axis=0).to_csv(
            filename, index=False)
    else:
        df.to_csv(filename, index=False)


if __name__ == '__main__':
    mods = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    pbar = tqdm(total=len(mods) * 100)
    for mod in mods:
        for i in range(100):
            main(i + 1000, mod)
            pbar.update(1)
