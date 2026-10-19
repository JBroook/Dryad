
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import soundfile as sf


# ============================================================
# CONFIGURATION
# ============================================================

DATASET_DIR = Path("FSC22")
METADATA_PATH = DATASET_DIR / "Metadata" / "Modified_Metadata.csv"
AUDIO_DIR = DATASET_DIR / "Audio Wise V1.0"
OUTPUT_DIR = DATASET_DIR / "plots"

# Change these to match your metadata column names.
CLASS_COLUMN = "Class Name"
FILENAME_COLUMN = "Dataset File Name"
FOLD_COLUMN = "Fold"

# Supported audio formats. Add more extensions if necessary.
AUDIO_EXTENSIONS = {
    ".wav"
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Consistent styling for all figures.
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 300,
    "font.family": "sans-serif",
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.titlesize": 14,
})


# ============================================================
# LOAD AND VALIDATE METADATA
# ============================================================

metadata = pd.read_csv(METADATA_PATH)

required_columns = {
    CLASS_COLUMN,
    FILENAME_COLUMN,
    FOLD_COLUMN,
}

missing_columns = required_columns - set(metadata.columns)

if missing_columns:
    raise ValueError(
        f"Missing metadata columns: {sorted(missing_columns)}. "
        f"Available columns: {list(metadata.columns)}"
    )

metadata[CLASS_COLUMN] = metadata[CLASS_COLUMN].astype("string").str.strip()

# Convert Fold to numeric so the folds can be ordered correctly.
metadata[FOLD_COLUMN] = pd.to_numeric(
    metadata[FOLD_COLUMN], errors="coerce"
)

print(f"Metadata rows: {len(metadata)}")
print(f"Audio classes: {metadata[CLASS_COLUMN].nunique()}")


# ============================================================
# FIGURE 1: NUMBER OF CLIPS PER AUDIO CLASS
# ============================================================

class_counts = (
    metadata[CLASS_COLUMN]
    .dropna()
    .value_counts()
    .sort_values(ascending=False)
)

fig, ax = plt.subplots(
    figsize=(12, max(6, len(class_counts) * 0.35))
)

sns.barplot(
    x=class_counts.values,
    y=class_counts.index,
    color="steelblue",
    ax=ax,
)

ax.set_title("Number of Audio Clips per Class", pad=12)
ax.set_xlabel("Number of clips")
ax.set_ylabel("Audio class")

# Annotate each bar with its count.
ax.bar_label(ax.containers[0], padding=3, fontsize=9)
ax.set_xlim(0, max(class_counts.values) * 1.12)

sns.despine(ax=ax, left=True)
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "01_clips_per_class.png",
    bbox_inches="tight",
)
plt.close(fig)


# ============================================================
# FIGURE 2: NUMBER OF CLIPS PER FOLD
# ============================================================

fold_counts = (
    metadata[FOLD_COLUMN]
    .dropna()
    .value_counts()
    .sort_index()
)

# Ensure all five folds appear, including a fold with zero clips.
fold_counts = fold_counts.reindex([1, 2, 3, 4, 5], fill_value=0)

fig, ax = plt.subplots(figsize=(8, 5))

sns.barplot(
    x=fold_counts.index.astype(int).astype(str),
    y=fold_counts.values,
    color="darkcyan",
    ax=ax,
)

ax.set_title("Number of Audio Clips per Fold", pad=12)
ax.set_xlabel("Fold")
ax.set_ylabel("Number of clips")

ax.bar_label(ax.containers[0], padding=4, fontsize=10)
ax.set_ylim(0, max(fold_counts.max() * 1.15, 1))

sns.despine(ax=ax, left=True)
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "02_clips_per_fold.png",
    bbox_inches="tight",
)
plt.close(fig)


# ============================================================
# SCAN AUDIO FILES FOR DURATION AND SAMPLE RATE
# ============================================================

def find_audio_file(filename, audio_dir):
    """
    Find an audio file from a metadata filename.

    Supports filenames with or without extensions and searches
    recursively within AUDIO_DIR.
    """
    candidate = Path(str(filename))

    # Handle metadata entries containing a relative subdirectory.
    direct_path = audio_dir / candidate
    if direct_path.is_file():
        return direct_path

    # If the filename already has an extension, search for it.
    if candidate.suffix:
        matches = list(audio_dir.rglob(candidate.name))
        return matches[0] if matches else None

    # Otherwise try the configured audio extensions.
    for extension in AUDIO_EXTENSIONS:
        matches = list(
            audio_dir.rglob(candidate.name + extension)
        )
        if matches:
            return matches[0]

    return None


audio_records = []
missing_files = []
failed_files = []

# Use unique filenames to avoid repeatedly scanning the same file.
filenames = metadata[FILENAME_COLUMN].dropna().unique()

print(f"\nScanning {len(filenames)} unique audio filenames...")

for filename in filenames:
    audio_path = find_audio_file(filename, AUDIO_DIR)

    if audio_path is None:
        missing_files.append(str(filename))
        continue

    try:
        # Metadata inspection only: no need to load the waveform.
        info = sf.info(str(audio_path))

        if info.samplerate <= 0 or info.frames < 0:
            raise ValueError("Invalid audio metadata")

        duration = info.frames / info.samplerate

        audio_records.append({
            FILENAME_COLUMN: str(filename),
            "duration_seconds": duration,
            "sample_rate_hz": info.samplerate,
            "channels": info.channels,
            "audio_path": str(audio_path),
        })

    except Exception as exc:
        failed_files.append((str(filename), str(exc)))

audio_stats = pd.DataFrame(audio_records)

if audio_stats.empty:
    raise RuntimeError(
        "No audio files could be read. Check AUDIO_DIR, filenames, "
        "extensions, and audio format support."
    )

print(f"Successfully inspected: {len(audio_stats)} files")
print(f"Missing files: {len(missing_files)}")
print(f"Unreadable files: {len(failed_files)}")

if missing_files:
    print("Examples of missing files:", missing_files[:10])

if failed_files:
    print("Examples of unreadable files:", failed_files[:5])

# Save the measurements so they can be reused in later analysis.
audio_stats.to_csv(
    OUTPUT_DIR / "audio_file_statistics.csv",
    index=False,
)


# ============================================================
# FIGURE 3: NUMBER OF CLIPS AT EACH DURATION
# ============================================================

# Round durations to 2 decimal places for readable grouping.
duration_counts = (
    audio_stats["duration_seconds"]
    .round(2)
    .value_counts()
    .sort_index()
)

fig, ax = plt.subplots(figsize=(10, 6))

sns.barplot(
    x=duration_counts.index,
    y=duration_counts.values,
    color="mediumpurple",
    ax=ax,
)

ax.set_title("Number of Audio Clips by Duration", pad=12)
ax.set_xlabel("Clip duration (seconds)")
ax.set_ylabel("Number of clips")

# Label each bar with its frequency.
ax.bar_label(ax.containers[0], padding=4, fontsize=10)

ax.set_ylim(0, max(duration_counts.max() * 1.15, 1))

# Avoid overcrowding if there are many distinct durations.
if len(duration_counts) > 15:
    ax.tick_params(axis="x", labelrotation=45)

sns.despine(ax=ax, left=True)
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "03_duration_distribution.png",
    bbox_inches="tight",
)
plt.close(fig)

# Print useful statistics for interpretation.
print("\nDuration summary:")
print(f"Minimum: {audio_stats['duration_seconds'].min():.3f} seconds")
print(f"Maximum: {audio_stats['duration_seconds'].max():.3f} seconds")
print(f"Median:  {audio_stats['duration_seconds'].median():.3f} seconds")
print(f"Unique durations (rounded to 2 decimals): {len(duration_counts)}")


# ============================================================
# FIGURE 4: DISTRIBUTION OF AUDIO SAMPLE RATES
# ============================================================

# Sample rates are discrete values, so a count plot is clearer
# than a KDE or continuous histogram.
sample_rate_counts = (
    audio_stats["sample_rate_hz"]
    .value_counts()
    .sort_index()
)

fig, ax = plt.subplots(figsize=(10, 6))

sns.barplot(
    x=sample_rate_counts.index.astype(str),
    y=sample_rate_counts.values,
    color="coral",
    ax=ax,
)

ax.set_title("Distribution of Audio Sample Rates", pad=12)
ax.set_xlabel("Sample rate (Hz)")
ax.set_ylabel("Number of clips")

ax.bar_label(ax.containers[0], padding=4, fontsize=10)
ax.set_ylim(0, max(sample_rate_counts.max() * 1.15, 1))

sns.despine(ax=ax, left=True)
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "04_sample_rate_distribution.png",
    bbox_inches="tight",
)
plt.close(fig)



# ============================================================
# FIGURE 5: THREAT VS NON-THREAT CLASS DISTRIBUTION
# ============================================================

THREAT_COLUMN = "Threat"

# Normalise Boolean values and common string representations.
threat_normalised = (
    metadata[THREAT_COLUMN]
    .astype("string")
    .str.strip()
    .str.lower()
)

threat_mapping = {
    "true": True,
    "false": False,
    "1": True,
    "0": False,
}

metadata["_threat_bool"] = threat_normalised.map(threat_mapping)

# Keep valid class names and threat labels.
valid_metadata = metadata.dropna(
    subset=[CLASS_COLUMN, "_threat_bool"]
).copy()

# Each unique audio class should have exactly one Threat label.
class_labels = valid_metadata[
    [CLASS_COLUMN, "_threat_bool"]
].drop_duplicates()

# Detect classes assigned conflicting threat labels.
label_counts = class_labels.groupby(CLASS_COLUMN)["_threat_bool"].nunique()
conflicting_classes = label_counts[label_counts > 1].index.tolist()

if conflicting_classes:
    raise ValueError(
        "Some classes have conflicting Threat labels: "
        f"{conflicting_classes}"
    )

# Count unique classes, not clips.
class_labels = class_labels.drop_duplicates(subset=[CLASS_COLUMN])

class_counts = (
    class_labels["_threat_bool"]
    .map({False: "Non-threat classes", True: "Threat classes"})
    .value_counts()
    .reindex(["Non-threat classes", "Threat classes"], fill_value=0)
)

total_classes = int(class_counts.sum())

if total_classes == 0:
    raise ValueError("No valid audio classes with Threat labels found.")

class_percentages = class_counts / total_classes * 100

# Plot the class-level distribution.
fig, ax = plt.subplots(figsize=(8, 6))

bars = ax.bar(
    class_counts.index,
    class_counts.values,
    color=["seagreen", "indianred"],
    width=0.6,
)

for bar, count, percentage in zip(
    bars, class_counts.values, class_percentages.values
):
    ax.annotate(
        f"{count} classes\n({percentage:.1f}%)",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 5),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=11,
    )

ax.set_title("Distribution of Threat and Non-threat Classes", pad=12)
ax.set_xlabel("Class category")
ax.set_ylabel("Number of unique classes")
ax.set_ylim(0, max(class_counts.max() * 1.2, 1))

sns.despine(ax=ax, left=True)
fig.tight_layout()

fig.savefig(
    OUTPUT_DIR / "05_threat_vs_non_threat_classes.png",
    bbox_inches="tight",
)
plt.close(fig)

# Print class-level results.
print("\nThreat class distribution:")
print(class_counts.to_string())

print("\nClass percentages:")
print(class_percentages.round(2).to_string())

non_threat_classes = int(class_counts["Non-threat classes"])
threat_classes = int(class_counts["Threat classes"])

if threat_classes > 0:
    print(
        "\nNon-threat : Threat class ratio = "
        f"{non_threat_classes}:{threat_classes}"
    )
    print(
        "Simplified ratio = "
        f"{non_threat_classes / threat_classes:.2f}:1"
    )
else:
    print("Class ratio is undefined because there are zero threat classes.")

# Optional: remove the temporary column.
metadata.drop(columns=["_threat_bool"], inplace=True)



# ============================================================
# SUMMARY STATISTICS
# ============================================================

print("\nDuration statistics (seconds):")
print(audio_stats["duration_seconds"].describe().round(3))

print("\nSample rate counts (Hz):")
print(sample_rate_counts.to_string())

print(f"\nAll figures and audio statistics saved to: {OUTPUT_DIR.resolve()}")
