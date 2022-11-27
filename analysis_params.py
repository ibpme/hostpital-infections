# %%
import pandas as pd
import matplotlib.pyplot as plt
import sys

# %%
var = sys.argv[1]
df = pd.read_csv("output_{}.csv".format(var))
df.head()

# %%
df["ratio_ps"] = df["secondary_cases"] / df["primary_cases"]
df["ratio_ps"].head()

# %%
df.groupby("{}".format(var))["ratio_ps"].mean().plot()
plt.show()
