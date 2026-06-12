import matplotlib.pyplot as plt

# Common x-axis labels
x_labels = ["Low", "Midlow", "Middle", "Midhigh", "High"]

# ==========================================================
# MCDPCDD
# ==========================================================

mcdpcdd_f1 = {
    "Window Size": [0.39, 0.36, 0.41, 0.34, 0.37],
    "Num Subwindows": [0.22, 0.17, 0.41, 0.33, 0.31],
    "Percentile": [0.31, 0.35, 0.41, 0.29, 0.00],
    "Learning Rate": [0.36, 0.16, 0.41, 0.37, 0.30],
}

mcdpcdd_latency = {
    "Window Size": [55.42, 76.25, 60.11, 67.62, 84.29],
    "Num Subwindows": [56.11, 47.75, 60.11, 69.70, 72.42],
    "Percentile": [73.19, 52.04, 60.11, 43.91, 9.75],
    "Learning Rate": [67.62, 38.00, 60.11, 65.12, 70.33],
}

plt.figure(figsize=(8,5))

for name, values in mcdpcdd_f1.items():
    plt.plot(x_labels, values, marker='o', label=name)

plt.title("MCDPCDD Parameter Sensitivity (F1-score)")
plt.xlabel("Parameter Setting")
plt.ylabel("F1-score")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.figure(figsize=(8,5))

for name, values in mcdpcdd_latency.items():
    plt.plot(x_labels, values, marker='o', label=name)

plt.title("MCDPCDD Parameter Sensitivity (Latency)")
plt.xlabel("Parameter Setting")
plt.ylabel("Latency")
plt.grid(True)
plt.legend()
plt.tight_layout()


# ==========================================================
# Martjushev
# ==========================================================

mart_f1 = {
    "Window Size": [0.64, 0.64, 0.64, 0.64, 0.64],
    "Population Min": [0.45, 0.62, 0.64, 0.62, 0.59],
    "Population Max": [0.51, 0.56, 0.64, 0.49, 0.42],
    "Threshold": [0.48, 0.54, 0.64, 0.62, 0.47],
}

mart_latency = {
    "Window Size": [24.68, 24.68, 24.68, 24.68, 24.68],
    "Population Min": [30.44, 23.43, 24.68, 27.97, 32.25],
    "Population Max": [23.29, 22.24, 24.68, 40.36, 54.12],
    "Threshold": [26.73, 24.12, 24.68, 23.33, 34.27],
}

plt.figure(figsize=(8,5))

for name, values in mart_f1.items():
    plt.plot(x_labels, values, marker='o', label=name)

plt.title("Martjushev Parameter Sensitivity (F1-score)")
plt.xlabel("Parameter Setting")
plt.ylabel("F1-score")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.figure(figsize=(8,5))

for name, values in mart_latency.items():
    plt.plot(x_labels, values, marker='o', label=name)

plt.title("Martjushev Parameter Sensitivity (Latency)")
plt.xlabel("Parameter Setting")
plt.ylabel("Latency")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.show()