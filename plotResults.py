import pandas as pd
import matplotlib.pyplot as plt
import sys

df = pd.read_pickle(sys.argv[1])

print(df)

fig = df.pivot(index='Ratio', columns='NumPrimes', values='Leakage').plot(figsize=(5,3))
plt.xlabel("Number of Lines Primed")
plt.ylabel("Maximal Leakage (bits)")
plt.legend(title="Number of Primes")
plt.tight_layout()
plt.show()
