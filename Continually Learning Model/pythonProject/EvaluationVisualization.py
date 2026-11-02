import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

OUTPUT_DIR = "model_visualisations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", context="notebook")

plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
})

MODELS = [
    "oracle",
    "logistic_regression",
    "bnn_none",
    "bnn_pos_weight",
    "bnn_focal",
    "bnn_oversample",
]

MODEL_LABELS = {
    "oracle": "Oracle",
    "logistic_regression": "Logistic Regression",
    "bnn_none": "BNN (None)",
    "bnn_pos_weight": "BNN (Pos Weight)",
    "bnn_focal": "BNN (Focal)",
    "bnn_oversample": "BNN (Oversample)",
}

DATASETS = [
    "Road Proximity",
    "Slope",
    "Elevation",
    "Recency",
    "Sustained Activity",
    "Combined",
]

METRICS = [
    "pr_auc",
    "roc_auc",
    "precision",
    "recall",
    "f1",
    "top5_prec",
    "log_loss",
    "brier",
]

METRIC_LABELS = {
    "pr_auc": "PR-AUC",
    "roc_auc": "ROC-AUC",
    "precision": "Precision",
    "recall": "Recall",
    "f1": "F1 Score",
    "top5_prec": "Top-5 Precision",
    "log_loss": "Log Loss",
    "brier": "Brier Score",
}

raw_data = {
    "Road Proximity": [
        ["oracle", 0.3123, 0.8326, 0.2883, 0.6141, 0.3924, 0.4099, 0.2368, 0.0692],
        ["logistic_regression", 0.2948, 0.8323, 0.3058, 0.5757, 0.3994, 0.3646, 0.2469, 0.0700],
        ["bnn_none", 0.3062, 0.8290, 0.2967, 0.5484, 0.3851, 0.3801, 0.2410, 0.0697],
        ["bnn_pos_weight", 0.3005, 0.8256, 0.3065, 0.5192, 0.3854, 0.3757, 0.2411, 0.0697],
        ["bnn_focal", 0.3123, 0.8266, 0.2948, 0.5521, 0.3844, 0.3967, 0.2407, 0.0696],
        ["bnn_oversample", 0.2945, 0.8266, 0.2959, 0.5248, 0.3784, 0.3680, 0.2418, 0.0699],
    ],

    "Slope": [
        ["oracle", 0.2719, 0.7937, 0.2616, 0.6502, 0.3731, 0.3149, 0.2889, 0.0862],
        ["logistic_regression", 0.1924, 0.6585, 0.1953, 0.5336, 0.2860, 0.2751, 0.3285, 0.0935],
        ["bnn_none", 0.2480, 0.7814, 0.2471, 0.6746, 0.3617, 0.2762, 0.2949, 0.0873],
        ["bnn_pos_weight", 0.2580, 0.7885, 0.2576, 0.6283, 0.3654, 0.2983, 0.2908, 0.0867],
        ["bnn_focal", 0.2582, 0.7881, 0.2510, 0.6706, 0.3652, 0.2906, 0.2908, 0.0866],
        ["bnn_oversample", 0.2568, 0.7881, 0.2392, 0.7215, 0.3593, 0.2862, 0.2918, 0.0867],
    ],

    "Elevation" : [
        ["oracle", 0.2204, 0.7823, 0.2413, 0.5296, 0.3315, 0.2600, 0.2641, 0.0770],
        ["logistic_regression", 0.2229, 0.7815, 0.2452, 0.5224, 0.3337, 0.2522, 0.2663, 0.0777],
        ["bnn_none", 0.2231, 0.7785, 0.2228, 0.6281, 0.3290, 0.2456, 0.2653, 0.0771],
        ["bnn_pos_weight", 0.2174, 0.7763, 0.2235, 0.5767, 0.3221, 0.2511, 0.2659, 0.0773],
        ["bnn_focal", 0.2124, 0.7760, 0.2289, 0.5600, 0.3250, 0.2356, 0.2658, 0.0773],
        ["bnn_oversample", 0.2182, 0.7790, 0.2170, 0.6442, 0.3247, 0.2400, 0.2649, 0.0770],
    ],

    "Recency": [
        ["oracle", 0.1776, 0.6641, 0.3468, 0.2169, 0.2669, 0.2489, 0.1487, 0.0347],
        ["logistic_regression", 0.2036, 0.6877, 0.3607, 0.2169, 0.2709, 0.2412, 0.1478, 0.0347],
        ["bnn_none", 0.1846, 0.6817, 0.3211, 0.2338, 0.2706, 0.2279, 0.1501, 0.0350],
        ["bnn_pos_weight", 0.1984, 0.6838, 0.3428, 0.2211, 0.2688, 0.2378, 0.1502, 0.0349],
        ["bnn_focal", 0.1948, 0.6819, 0.3129, 0.2225, 0.2601, 0.2345, 0.1494, 0.0349],
        ["bnn_oversample", 0.1963, 0.6728, 0.3469, 0.2155, 0.2659, 0.2334, 0.1517, 0.0351],
    ],

    "Sustained Activity": [
        ["oracle", 0.4341, 0.8383, 0.4952, 0.5646, 0.5276, 0.5962, 0.1843, 0.0503],
        ["logistic_regression", 0.4590, 0.8423, 0.4741, 0.5543, 0.5111, 0.5907, 0.1877, 0.0514],
        ["bnn_none", 0.4494, 0.8473, 0.4707, 0.5908, 0.5239, 0.5785, 0.1867, 0.0511],
        ["bnn_pos_weight", 0.4558, 0.8483, 0.4690, 0.5901, 0.5226, 0.5940, 0.1869, 0.0510],
        ["bnn_focal", 0.4500, 0.8473, 0.4701, 0.5908, 0.5236, 0.5808, 0.1865, 0.0510],
        ["bnn_oversample", 0.4500, 0.8433, 0.4602, 0.5952, 0.5191, 0.5863, 0.1864, 0.0510],
    ],

    "Combined": [
        ["oracle", 0.3282, 0.7976, 0.3800, 0.3559, 0.3675, 0.4358, 0.2206, 0.0601],
        ["logistic_regression", 0.2841, 0.7773, 0.2450, 0.5109, 0.3312, 0.4082, 0.2316, 0.0623],
        ["bnn_none", 0.3025, 0.7885, 0.2845, 0.4607, 0.3518, 0.4148, 0.2252, 0.0610],
        ["bnn_pos_weight", 0.2951, 0.7863, 0.2727, 0.4833, 0.3486, 0.4137, 0.2283, 0.0617],
        ["bnn_focal", 0.3029, 0.7906, 0.2771, 0.4774, 0.3507, 0.4248, 0.2244, 0.0609],
        ["bnn_oversample", 0.2999, 0.7828, 0.2997, 0.4367, 0.3555, 0.4314, 0.2265, 0.0610],
    ],
}

columns = ["model"] + METRICS

frames = []

for dataset, rows in raw_data.items():
    df = pd.DataFrame(rows, columns=columns)
    df["dataset"] = dataset
    frames.append(df)

data = pd.concat(frames, ignore_index=True)

data["model_label"] = data["model"].map(MODEL_LABELS)

data.to_csv(
    os.path.join(OUTPUT_DIR, "all_model_results.csv"),
    index=False
)

PALETTE = sns.color_palette("colorblind", len(MODELS))

MODEL_COLORS = dict(zip(MODELS, PALETTE))


def save_plot(filename):
    plt.tight_layout()

    plt.savefig(
        os.path.join(OUTPUT_DIR, filename + ".png"),
        bbox_inches="tight"
    )

    plt.savefig(
        os.path.join(OUTPUT_DIR, filename + ".pdf"),
        bbox_inches="tight"
    )

    plt.close()


def plot_metric(metric):

    fig, ax = plt.subplots(figsize=(15, 7))

    sns.barplot(
        data=data,
        x="dataset",
        y=metric,
        hue="model_label",
        hue_order=[MODEL_LABELS[m] for m in MODELS],
        ax=ax,
        palette=PALETTE
    )

    ax.set_title(
        f"{METRIC_LABELS[metric]} Comparison Across Datasets",
        fontweight="bold",
        pad=15
    )

    ax.set_xlabel("Dataset")
    ax.set_ylabel(METRIC_LABELS[metric])

    ax.tick_params(axis="x", rotation=20)

    ax.legend(
        title="Model",
        bbox_to_anchor=(1.02, 1),
        loc="upper left"
    )

    save_plot(f"01_{metric}_comparison")


for metric in METRICS:
    plot_metric(metric)


for metric in METRICS:

    pivot = data.pivot(
        index="model_label",
        columns="dataset",
        values=metric
    )

    cmap = "RdYlGn_r" if metric in ["log_loss", "brier"] else "RdYlGn"

    plt.figure(figsize=(13, 6))

    sns.heatmap(
        pivot,
        annot=True,
        fmt=".3f",
        cmap=cmap,
        linewidths=0.5,
        cbar_kws={"label": METRIC_LABELS[metric]}
    )

    plt.title(
        f"{METRIC_LABELS[metric]} Heatmap",
        fontweight="bold",
        pad=15
    )

    plt.xlabel("Dataset")
    plt.ylabel("Model")

    save_plot(f"02_{metric}_heatmap")


fig, axes = plt.subplots(
    2, 3,
    figsize=(17, 10)
)

for ax, dataset in zip(axes.flat, DATASETS):

    subset = data[data["dataset"] == dataset]

    for model in MODELS:

        row = subset[subset["model"] == model]

        ax.scatter(
            row["recall"],
            row["precision"],
            s=110,
            color=MODEL_COLORS[model],
            label=MODEL_LABELS[model],
            edgecolors="black",
            linewidths=0.5
        )

        ax.annotate(
            MODEL_LABELS[model],
            (
                row["recall"].values[0],
                row["precision"].values[0]
            ),
            fontsize=7,
            xytext=(4, 4),
            textcoords="offset points"
        )

    ax.set_title(dataset, fontweight="bold")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")

    ax.set_xlim(0, 0.8)
    ax.set_ylim(0, 0.6)

fig.suptitle(
    "Precision vs Recall Across Datasets",
    fontsize=17,
    fontweight="bold"
)

save_plot("03_precision_recall")


average = data.groupby("model")[METRICS].mean()

normalised = average.copy()

for metric in ["log_loss", "brier"]:
    normalised[metric] = (
        1 - normalised[metric] / normalised[metric].max()
    )

normalised = (
    normalised - normalised.min()
) / (
    normalised.max() - normalised.min()
)

plt.figure(figsize=(13, 6))

sns.heatmap(
    normalised.T,
    annot=True,
    fmt=".2f",
    cmap="RdYlGn",
    linewidths=0.5,
    vmin=0,
    vmax=1,
    xticklabels=[MODEL_LABELS[m] for m in MODELS]
)

plt.title(
    "Overall Normalised Model Performance",
    fontsize=15,
    fontweight="bold"
)

plt.xlabel("Model")
plt.ylabel("Metric")

save_plot("04_overall_performance")


rank_data = data.copy()

for metric in METRICS:

    ascending = metric in ["log_loss", "brier"]

    rank_data[metric + "_rank"] = (
        rank_data.groupby("dataset")[metric]
        .rank(ascending=ascending, method="average")
    )

rank_columns = [m + "_rank" for m in METRICS]

ranking = rank_data.groupby("model")[rank_columns].mean()

ranking["average_rank"] = ranking.mean(axis=1)

ranking = ranking.sort_values("average_rank")

plt.figure(figsize=(11, 6))

sns.barplot(
    x=ranking["average_rank"].values,
    y=[MODEL_LABELS[m] for m in ranking.index],
    color="steelblue"
)

plt.title(
    "Average Model Ranking Across All Datasets",
    fontweight="bold"
)

plt.xlabel("Average Rank (Lower Is Better)")
plt.ylabel("Model")

save_plot("05_model_rankings")


dataset_avg = data.groupby("dataset")[[
    "pr_auc",
    "roc_auc",
    "f1",
    "top5_prec"
]].mean()

plt.figure(figsize=(12, 6))

dataset_avg.plot(
    kind="bar",
    figsize=(13, 6),
    colormap="viridis"
)

plt.title(
    "Average Performance by Dataset",
    fontweight="bold"
)

plt.xlabel("Dataset")
plt.ylabel("Average Metric Score")

plt.xticks(rotation=20)
plt.legend(title="Metric")

save_plot("06_dataset_comparison")


for dataset in DATASETS:

    subset = data[data["dataset"] == dataset].set_index("model")

    fig, ax = plt.subplots(figsize=(12, 6))

    subset[["pr_auc", "roc_auc", "f1", "top5_prec"]].plot(
        kind="bar",
        ax=ax,
        width=0.8
    )

    ax.set_title(
        f"Model Performance: {dataset}",
        fontweight="bold"
    )

    ax.set_xlabel("Model")
    ax.set_ylabel("Score")

    ax.set_xticklabels(
        [MODEL_LABELS[m] for m in subset.index],
        rotation=20
    )

    ax.legend(title="Metric")

    save_plot(
        "07_dataset_" + DATASETS.index(dataset).__str__()
    )


fig, axes = plt.subplots(
    1, 2,
    figsize=(15, 6)
)

sns.boxplot(
    data=data,
    x="model_label",
    y="precision",
    ax=axes[0],
    color="lightblue"
)

sns.boxplot(
    data=data,
    x="model_label",
    y="recall",
    ax=axes[1],
    color="lightgreen"
)

axes[0].set_title("Precision Distribution")
axes[1].set_title("Recall Distribution")

axes[0].tick_params(axis="x", rotation=30)
axes[1].tick_params(axis="x", rotation=30)

save_plot("08_precision_recall_distribution")


best_rows = []

for dataset in DATASETS:

    subset = data[data["dataset"] == dataset]

    for metric in METRICS:

        ascending = metric in ["log_loss", "brier"]

        best = subset.sort_values(
            metric,
            ascending=ascending
        ).iloc[0]

        best_rows.append({
            "dataset": dataset,
            "metric": metric,
            "best_model": best["model_label"],
            "score": best[metric]
        })

best_df = pd.DataFrame(best_rows)

best_df.to_csv(
    os.path.join(OUTPUT_DIR, "best_models.csv"),
    index=False
)

print("\nBEST MODEL PER DATASET AND METRIC")
print(best_df.to_string(index=False))


print("\nAVERAGE MODEL PERFORMANCE")

print(
    average.rename(index=MODEL_LABELS).round(4).to_string()
)

print("\nAVERAGE MODEL RANKING")

print(
    ranking.rename(index=MODEL_LABELS).round(2).to_string()
)

print("\nVisualisation complete!")
print(f"All results saved in: {OUTPUT_DIR}/")