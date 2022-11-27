# %%
import pandas as pd
import matplotlib.pyplot as plt

# %%
df = pd.read_csv("output_strategies.csv")
df.head()

# %%
strategies = df["strategy"].unique()

# %%
df["ratio_ps"] = df["secondary_cases"] / df["primary_cases"]
df["ratio_ps"].head()

# %%
result = df.groupby("strategy")["ratio_ps"].mean().sort_values().values
name = ["No Intervention", "Group", "Isolate", "Group and Isolate"]
plt.barh(y=name, width=result)
