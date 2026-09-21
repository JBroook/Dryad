import os
import django
from datetime import timedelta

from django.utils import timezone

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

django.setup()

from projects.models import Incident, Project

from projects.BNN import (
    generate_training_samples,
    undersample,
    chronological_split,
    train_mlp,
    evaluate_model,
    FEATURES
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

PROJECT_ID = 24

TEST_DAYS = 7
NEGATIVE_RATIO = 3


# --------------------------------------------------
# Load project
# --------------------------------------------------

project = Project.objects.get(
    pk=PROJECT_ID
)


# --------------------------------------------------
# Define time range
# --------------------------------------------------

end_time = (
    timezone.now()
    - timedelta(days=7)
)

start_time = (
    end_time
    - timedelta(days=30)
)


print(
    f"Project: {project}"
)

print(
    f"Start: {start_time}"
)

print(
    f"End:   {end_time}"
)


# --------------------------------------------------
# Generate samples
# --------------------------------------------------

samples = generate_training_samples(
    project,
    start_time,
    end_time,
)


print(
    f"\nGenerated {len(samples)} samples"
)

# --------------------------------------------------
# Inspect class distribution
# --------------------------------------------------

positive_count = sum(
    sample["target"] == 1
    for sample in samples
)

negative_count = sum(
    sample["target"] == 0
    for sample in samples
)


print(
    f"Positive: {positive_count}"
)

print(
    f"Negative: {negative_count}"
)


# --------------------------------------------------
# Chronological train/test split
# --------------------------------------------------

train_samples, test_samples = chronological_split(
    samples,
    test_days=TEST_DAYS,
)


print(
    f"\nTrain samples: {len(train_samples)}"
)

print(
    f"Test samples:  {len(test_samples)}"
)


train_positive = sum(
    sample["target"] == 1
    for sample in train_samples
)

train_negative = sum(
    sample["target"] == 0
    for sample in train_samples
)

test_positive = sum(
    sample["target"] == 1
    for sample in test_samples
)

test_negative = sum(
    sample["target"] == 0
    for sample in test_samples
)


print(
    "\nTrain:"
)

print(
    f"  Positive: {train_positive}"
)

print(
    f"  Negative: {train_negative}"
)

print(
    "\nTest:"
)

print(
    f"  Positive: {test_positive}"
)

print(
    f"  Negative: {test_negative}"
)


# --------------------------------------------------
# Undersample TRAINING DATA ONLY
# --------------------------------------------------

train_samples = undersample(
    train_samples,
    negative_ratio=NEGATIVE_RATIO,
)




print(
    f"\nAfter undersampling:"
)

print(
    f"Train samples: {len(train_samples)}"
)

print(
    "Positive:",
    sum(
        sample["target"] == 1
        for sample in train_samples
    ),
)

print(
    "Negative:",
    sum(
        sample["target"] == 0
        for sample in train_samples
    ),
)


# --------------------------------------------------
# Train model
# --------------------------------------------------

print(
    "\nTraining model..."
)

model, scaler = train_mlp(
    train_samples
)


# --------------------------------------------------
# Evaluate on untouched TEST data
# --------------------------------------------------

print(
    "\nEvaluating model..."
)

probabilities = evaluate_model(
    model,
    scaler,
    test_samples,
)

print(
    "\nDone."
)

import torch
import joblib

torch.save(
    model.state_dict(),
    "data/models/risk_model.pt"
)

joblib.dump(
    scaler,
    "data/models/risk_scaler.pkl"
)