import matplotlib.pyplot as plt
import os


outputDirectory = "Evaluation/Plots"
os.makedirs(outputDirectory, exist_ok=True)


xLabels = ['Low', 'Mid-low', 'Middle', 'Mid-high', 'High']
xValues = range(len(xLabels))


mcdpcddF1 = {
    'Window Size': [0.39, 0.36, 0.41, 0.34, 0.37],
    'Number of Subwindows': [0.22, 0.17, 0.41, 0.33, 0.31],
    'Confidence Interval': [0.31, 0.35, 0.41, 0.29, 0.00],
    'Learning Rate': [0.36, 0.16, 0.41, 0.37, 0.30]
}

mcdpcddLatency = {
    'Window Size': [55.42, 76.25, 60.11, 67.62, 84.29],
    'Number of Subwindows': [56.11, 47.75, 60.11, 69.70, 72.42],
    'Confidence Interval': [73.19, 52.04, 60.11, 43.91, 9.75],
    'Learning Rate': [67.62, 38.00, 60.11, 65.12, 70.33]
}

martjushevF1 = {
    'Minimum Population Size': [0.45, 0.62, 0.64, 0.62, 0.59],
    'Maximum Population Size': [0.51, 0.56, 0.64, 0.49, 0.42],
    'Detection Threshold': [0.48, 0.54, 0.64, 0.62, 0.47]
}

martjushevLatency = {
    'Minimum Population Size': [30.44, 23.43, 24.68, 27.97, 32.25],
    'Maximum Population Size': [23.29, 22.24, 24.68, 40.36, 54.12],
    'Detection Threshold': [26.73, 24.12, 24.68, 23.33, 34.27]
}


def CreateSensitivityPlot(data, title, yLabel, filename):

    plt.figure(figsize=(9, 5))

    for parameter, values in data.items():

        plt.plot(
            xValues,
            values,
            marker='o',
            linewidth=2,
            label=parameter
        )

        # Highlight middle parameter value as optimal
        plt.scatter(
            2,
            values[2],
            s=160,
            color='black',
            edgecolors='white',
            linewidth=1.2,
            zorder=5
        )

    plt.xticks(xValues, xLabels)
    plt.xlabel('Parameter Value')
    plt.ylabel(yLabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    savePath = os.path.join(outputDirectory, filename)

    plt.savefig(savePath, dpi=300, bbox_inches='tight')

    plt.close()


CreateSensitivityPlot(
    mcdpcddF1,
    'MCDPCDD Parameter Sensitivity (F1 Score)',
    'F1 Score',
    'paramSensitivity_mcdpcdd_f1.png'
)

CreateSensitivityPlot(
    mcdpcddLatency,
    'MCDPCDD Parameter Sensitivity (Latency)',
    'Latency',
    'paramSensitivity_mcdpcdd_latency.png'
)

CreateSensitivityPlot(
    martjushevF1,
    'Martjushev Parameter Sensitivity (F1 Score)',
    'F1 Score',
    'paramSensitivity_martjushev_f1.png'
)

CreateSensitivityPlot(
    martjushevLatency,
    'Martjushev Parameter Sensitivity (Latency)',
    'Latency',
    'paramSensitivity_martjushev_latency.png'
)