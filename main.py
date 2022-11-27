# %%
import random
import numpy as np
from matplotlib import pyplot as plt
import agents_enviroments
from agents_enviroments import History
from agents_enviroments.movement_strategy import GroupInfectedStrategy, IsolateInfectedStrategy, MovementStrategy
from tqdm.auto import tqdm
import pandas as pd
import os
from typing import List


def flatten(l: List[list]):
    return [item for sublist in l for item in sublist]


def get_strategy_names(strategies: List[MovementStrategy]) -> str:
    if len(strategies) == 0:
        return "NoStrategies"
    return "_".join(list(map(str, strategies)))


def get_params(mod: dict):
    params = {
        "C": 0.3,
        "V": 1.0,
        "m": 0.9,
        "k": 0.4,
        "strategies": [],
        "screen_interval": 4,
        "result_length": 2,
    }
    if list(mod.keys())[0] == "interval_result":
        params.update(
            {"screen_interval": mod["interval_result"][0],
             "result_length": mod["interval_result"][1]}
        )
    else:
        params.update(mod)
    return params


def main(seed: int, mod: dict, generation_seed: int = 10):
    num_of_bays = 10
    num_of_isobays = 6
    colonized_prob_on_admit = 0.05
    time = 150

    np.random.seed(generation_seed)
    random.seed(generation_seed)
    initial_params = get_params(mod)
    params = agents_enviroments.Parameters(
        C=initial_params["C"],
        V=initial_params["V"],
        m=initial_params["m"],
        k=initial_params["k"],
        treatment_prob=0.9,
        isolation_prob=0.01,
        screen_interval=initial_params["screen_interval"],
        result_length=initial_params["result_length"]
    )
    strategies: List[MovementStrategy] = initial_params["strategies"]
    patient_generator = agents_enviroments.PatientGenerator()
    patient_generator.set_var(
        poisson_lambda=5, gamma_k=7, gamma_scale=1)
    patient_generator.set_col_length_dist(
        gamma_k=11, gamma_scale=1)
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
        for strategy in strategies:
            strategy.move_patients(ward)
        history.add_from_dict(ward.history_dict())
        ward.forward_time()

    # %%

    filename = "output_{}.csv".format(list(mod.keys())[0])
    result_dict = {
        "primary_cases": [ward.primary_cases],
        "secondary_cases": [ward.secondary_cases],
        "total_screens": [sum(history.screened)],
        "total_detection": [sum(history.new_detected)],
        "total_healed": [sum(history.healed)],
        "strategy": [get_strategy_names(strategies)],
        "interval_result": ["_".join([str(initial_params["screen_interval"]), str(initial_params["result_length"])])],
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
    mod_dicts = {
        "V": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2],
        "C": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.1, 1.2, ],
        "k": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        "m": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
        "strategies": [[], [GroupInfectedStrategy()], [IsolateInfectedStrategy()], [GroupInfectedStrategy(), IsolateInfectedStrategy()]],
        "interval_result": [[5, 4], [5, 3], [5, 2], [4, 3], [4, 2], [3, 2], [3, 1]]
    }
    flat_count = flatten(mod_dicts.values())
    pbar = tqdm(total=len(flat_count) * 100)
    for params, mods in mod_dicts.items():
        for mod in mods:
            for i in range(100):
                main(i + 1000, {params: mod})
                pbar.update(1)
