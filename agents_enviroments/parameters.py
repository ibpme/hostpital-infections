from dataclasses import dataclass


@dataclass
class Parameters:
    C: float
    V: float
    m: float
    k: float
    treatment_prob: float
    isolation_prob: float
    result_time: int
    screen_interval: int
