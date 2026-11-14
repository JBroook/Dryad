import math
import random
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timedelta

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler

FEATURES = [
    "elevation",
    "slope",
    "distance_to_road",
    "attacks_last_24h",
    "attacks_last_7d",
    "attacks_last_30d",
    "days_since_last_attack",
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
]

RANDOM_SEED = 42
NUM_CELLS = 300
SIMULATION_DAYS = 365
WARMUP_DAYS = 30
TARGET_WINDOW_DAYS = 7
SIMULATION_STEP_HOURS = 6
STEPS_PER_DAY = 24 // SIMULATION_STEP_HOURS
STEPS_PER_TARGET_WINDOW = TARGET_WINDOW_DAYS * STEPS_PER_DAY
MAX_DAYS_SINCE_LAST_ATTACK = 30.0

TEST_DAYS = 60
VALIDATION_DAYS = 45
SPLIT_GAP_DAYS = 7
TOP_FRACTION = 0.05

BATCH_SIZE = 512
MAX_EPOCHS = 60
PATIENCE = 8
LEARNING_RATE = 0.003
MC_PASSES = 100
FOCAL_GAMMA = 2.0
FOCAL_ALPHA = 0.75

IMBALANCE_STRATEGIES = ["none", "pos_weight", "focal", "oversample"]


class MockGridCell:
    def __init__(self, cell_id, elevation, slope, distance_to_road):
        self.id = cell_id
        self.elevation = elevation
        self.slope = slope
        self.distance_to_road = distance_to_road


class RiskPredictorMCDropout(nn.Module):
    def __init__(self, num_input_features=11):
        super().__init__()
        self.blinear1 = nn.Linear(num_input_features, 64)
        self.dropout1 = nn.Dropout(p=0.2)
        self.blinear2 = nn.Linear(64, 64)
        self.dropout2 = nn.Dropout(p=0.2)
        self.blinear3 = nn.Linear(64, 32)
        self.dropout3 = nn.Dropout(p=0.2)
        self.output = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = F.gelu(self.blinear1(x))
        x = self.dropout1(x)
        x = F.gelu(self.blinear2(x))
        x = self.dropout2(x)
        x = F.gelu(self.blinear3(x))
        x = self.dropout3(x)
        x = self.output(x)
        return {"logits": x, "probabilities": self.sigmoid(x)}


def cyclical(value, period):
    return (
        math.sin(2 * math.pi * value / period),
        math.cos(2 * math.pi * value / period),
    )


def sigmoid(x):
    return 1 / (1 + math.exp(-x))


def get_attack_history(timestamps, observation_time):
    history_end = bisect_left(timestamps, observation_time)

    def attacks_since(window):
        return history_end - bisect_left(timestamps, observation_time - window)

    if history_end > 0:
        days_since = (observation_time - timestamps[history_end - 1]).total_seconds() / 86400
        days_since = min(days_since, MAX_DAYS_SINCE_LAST_ATTACK)
    else:
        days_since = MAX_DAYS_SINCE_LAST_ATTACK

    return {
        "attacks_last_24h": attacks_since(timedelta(hours=24)),
        "attacks_last_7d": attacks_since(timedelta(days=7)),
        "attacks_last_30d": attacks_since(timedelta(days=30)),
        "days_since_last_attack": days_since,
    }


def get_future_attack_target(timestamps, observation_time):
    first_future_index = bisect_left(timestamps, observation_time)
    future_end = observation_time + timedelta(days=TARGET_WINDOW_DAYS)
    has_future_attack = (
        first_future_index < len(timestamps)
        and timestamps[first_future_index] < future_end
    )
    return int(has_future_attack)


def build_feature_values(grid_cell, observation_time, incident_timestamps):
    history = get_attack_history(incident_timestamps, observation_time)
    hour_sin, hour_cos = cyclical(observation_time.hour, 24)
    day_sin, day_cos = cyclical(observation_time.weekday(), 7)
    return {
        "elevation": grid_cell.elevation,
        "slope": grid_cell.slope,
        "distance_to_road": grid_cell.distance_to_road,
        "attacks_last_24h": history["attacks_last_24h"],
        "attacks_last_7d": history["attacks_last_7d"],
        "attacks_last_30d": history["attacks_last_30d"],
        "days_since_last_attack": history["days_since_last_attack"],
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "day_sin": day_sin,
        "day_cos": day_cos,
    }


def calculate_step_event_probability(sample, dataset_id):
    distance_km = sample["distance_to_road"] / 1000
    slope = sample["slope"]
    elevation = sample["elevation"]
    days_since = sample["days_since_last_attack"]
    attacks_30d = sample["attacks_last_30d"]

    logit = 0

    if dataset_id == 1: # Road proximity
        logit = -8.3 + 4.5 * math.exp(-distance_km / 0.7)
    elif dataset_id == 2: # Slope
        logit = -8.4 + 4.0 * math.exp(-(((slope - 15) / 10) ** 2))
    elif dataset_id == 3: # Elevation
        logit = -8.3 + 4.0 * sigmoid((1500 - elevation) / 350)
    elif dataset_id == 4: # Recent activity
        logit = -7.0 + 5.0 * math.exp(-days_since / 6)
    elif dataset_id == 5: # Sustained activity
        logit = -7.0 + 3.8 * (1 - math.exp(-0.7 * attacks_30d))
    elif dataset_id == 6: # Combined
        road_access = math.exp(-distance_km / 0.9)
        slope_suitability = math.exp(-(((slope - 15) / 14) ** 2))
        recency = math.exp(-days_since / 6)
        daylight = -sample["hour_cos"]
        logit = (
            -7.8
            + 3.5 * road_access * (0.3 + 0.7 * slope_suitability)
            + 2.5 * recency * road_access
            + 0.8 * daylight
            + 0.4 * sample["day_cos"]
        )

    return sigmoid(logit)


def calculate_true_probability(grid_cell, observation_time, incident_timestamps, dataset_id):
    history = incident_timestamps[: bisect_left(incident_timestamps, observation_time)]
    probability_no_attack = 1.0
    for step in range(STEPS_PER_TARGET_WINDOW):
        step_start = observation_time + timedelta(hours=step * SIMULATION_STEP_HOURS)
        features = build_feature_values(grid_cell, step_start, history)
        probability_no_attack *= 1 - calculate_step_event_probability(features, dataset_id)
    return 1 - probability_no_attack


def create_grid_cells(num_cells):
    cells = []
    for cell_id in range(num_cells):
        elevation = 4000 * random.betavariate(2, 3)
        slope = min(60.0, max(0.0, random.gauss(5 + 0.006 * elevation, 7)))
        distance_to_road = min(6000.0, random.expovariate(1 / (400 + 0.6 * elevation)))
        cells.append(MockGridCell(cell_id, elevation, slope, distance_to_road))
    return cells


def generate_synthetic_dataset(dataset_id, num_cells=NUM_CELLS, simulation_days=SIMULATION_DAYS):
    random.seed(RANDOM_SEED + dataset_id)
    cells = create_grid_cells(num_cells)

    start_time = datetime(2026, 1, 1, 0, 0, 0)
    step_minutes = SIMULATION_STEP_HOURS * 60
    incidents_by_cell = defaultdict(list)

    for step in range(simulation_days * STEPS_PER_DAY):
        step_start = start_time + timedelta(hours=step * SIMULATION_STEP_HOURS)
        for cell in cells:
            features = build_feature_values(cell, step_start, incidents_by_cell[cell.id])
            if random.random() < calculate_step_event_probability(features, dataset_id):
                attack_time = step_start + timedelta(minutes=random.randrange(step_minutes))
                incidents_by_cell[cell.id].append(attack_time)

    samples = []
    for cell in cells:
        incident_timestamps = incidents_by_cell[cell.id]
        for day in range(WARMUP_DAYS, simulation_days - TARGET_WINDOW_DAYS):
            hour_offset = SIMULATION_STEP_HOURS * random.randrange(STEPS_PER_DAY)
            observation_time = start_time + timedelta(days=day, hours=hour_offset)
            features = build_feature_values(cell, observation_time, incident_timestamps)
            features["target"] = get_future_attack_target(incident_timestamps, observation_time)
            features["grid_cell_id"] = cell.id
            features["timestamp"] = observation_time
            features["day_index"] = day
            features["true_prob"] = calculate_true_probability(
                cell, observation_time, incident_timestamps, dataset_id
            )
            samples.append(features)

    return samples


def split_samples_chronologically(samples):
    gap = timedelta(days=SPLIT_GAP_DAYS)
    last_time = max(s["timestamp"] for s in samples)

    test_start = last_time - timedelta(days=TEST_DAYS)
    validation_end = test_start - gap
    validation_start = validation_end - timedelta(days=VALIDATION_DAYS)
    train_end = validation_start - gap

    train = [s for s in samples if s["timestamp"] < train_end]
    validation = [s for s in samples if validation_start <= s["timestamp"] < validation_end]
    test = [s for s in samples if s["timestamp"] >= test_start]
    return train, validation, test


def samples_to_arrays(samples):
    features = np.array([[s[f] for f in FEATURES] for s in samples], dtype=np.float32)
    targets = np.array([s["target"] for s in samples], dtype=np.float32)
    return features, targets


def focal_loss(logits, targets):
    bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
    probability_of_truth = torch.exp(-bce)
    alpha = FOCAL_ALPHA * targets + (1 - FOCAL_ALPHA) * (1 - targets)
    return (alpha * (1 - probability_of_truth) ** FOCAL_GAMMA * bce).mean()


def build_loss_function(imbalance_strategy, positives, negatives):
    if imbalance_strategy == "pos_weight":
        pos_weight = negatives / positives.clamp(min=1.0)
        return lambda logits, targets: F.binary_cross_entropy_with_logits(
            logits, targets, pos_weight=pos_weight
        )
    if imbalance_strategy == "focal":
        return focal_loss
    return F.binary_cross_entropy_with_logits


@torch.no_grad()
def predict_logits(model, X, mc_passes=MC_PASSES):
    model.train()
    passes = [model(X)["logits"].squeeze(-1) for _ in range(mc_passes)]
    return torch.stack(passes).mean(dim=0).numpy()


@torch.no_grad()
def predict_deterministic_probabilities(model, X):
    model.eval()
    return model(X)["probabilities"].squeeze(-1).numpy()


def train_bnn(train_samples, validation_samples, imbalance_strategy):
    train_features, train_targets = samples_to_arrays(train_samples)
    validation_features, validation_targets = samples_to_arrays(validation_samples)

    scaler = StandardScaler()
    X_train = torch.tensor(scaler.fit_transform(train_features), dtype=torch.float32)
    y_train = torch.tensor(train_targets)
    X_validation = torch.tensor(scaler.transform(validation_features), dtype=torch.float32)

    torch.manual_seed(RANDOM_SEED)
    model = RiskPredictorMCDropout(num_input_features=len(FEATURES))
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    positives = y_train.sum()
    negatives = len(y_train) - positives
    loss_function = build_loss_function(imbalance_strategy, positives, negatives)

    sampler = None
    if imbalance_strategy == "oversample":
        sample_weights = torch.where(y_train == 1, 0.5 / positives, 0.5 / negatives)
        sampler = WeightedRandomSampler(sample_weights, num_samples=len(y_train), replacement=True)

    loader = DataLoader(
        TensorDataset(X_train, y_train),
        batch_size=BATCH_SIZE,
        sampler=sampler,
        shuffle=sampler is None,
    )

    best_pr_auc = -1.0
    best_state = None
    epochs_without_improvement = 0

    for _ in range(MAX_EPOCHS):
        model.train()
        for batch_features, batch_targets in loader:
            optimizer.zero_grad()
            logits = model(batch_features)["logits"].squeeze(-1)
            loss_function(logits, batch_targets).backward()
            optimizer.step()

        validation_pr_auc = average_precision_score(
            validation_targets, predict_deterministic_probabilities(model, X_validation)
        )
        if validation_pr_auc > best_pr_auc:
            best_pr_auc = validation_pr_auc
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
            if epochs_without_improvement >= PATIENCE:
                break

    model.load_state_dict(best_state)

    validation_logits = predict_logits(model, X_validation)
    calibrator = LogisticRegression(C=1e6, max_iter=1000)
    calibrator.fit(validation_logits.reshape(-1, 1), validation_targets)

    return model, scaler, calibrator


def predict_bnn_probabilities(model, scaler, calibrator, samples):
    features, _ = samples_to_arrays(samples)
    X = torch.tensor(scaler.transform(features), dtype=torch.float32)
    logits = predict_logits(model, X)
    return calibrator.predict_proba(logits.reshape(-1, 1))[:, 1]


def select_threshold(y_true, probabilities):
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    f1_scores = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-12)
    return float(thresholds[np.argmax(f1_scores)])


def precision_at_top_fraction(y_true, scores, day_indices, fraction=TOP_FRACTION):
    selected_targets = []
    for day in np.unique(day_indices):
        positions = np.where(day_indices == day)[0]
        count = max(1, math.ceil(fraction * len(positions)))
        top_positions = positions[np.argsort(-scores[positions], kind="stable")[:count]]
        selected_targets.extend(y_true[top_positions])
    return float(np.mean(selected_targets))


def evaluate_predictions(name, y_true, probabilities, day_indices, threshold):
    y_true = y_true.astype(int)
    probabilities = np.clip(probabilities, 1e-6, 1 - 1e-6)
    predictions = (probabilities >= threshold).astype(int)
    return {
        "model": name,
        "pr_auc": average_precision_score(y_true, probabilities),
        "roc_auc": roc_auc_score(y_true, probabilities),
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
        "top5_precision": precision_at_top_fraction(y_true, probabilities, day_indices),
        "log_loss": log_loss(y_true, probabilities, labels=[0, 1]),
        "brier": brier_score_loss(y_true, probabilities),
    }


def print_result_table(results):
    print(
        f"{'model':<24}{'pr_auc':>8}{'roc_auc':>9}{'precision':>11}"
        f"{'recall':>8}{'f1':>8}{'top5_prec':>11}{'log_loss':>10}{'brier':>8}"
    )
    for r in results:
        print(
            f"{r['model']:<24}{r['pr_auc']:>8.4f}{r['roc_auc']:>9.4f}{r['precision']:>11.4f}"
            f"{r['recall']:>8.4f}{r['f1']:>8.4f}{r['top5_precision']:>11.4f}"
            f"{r['log_loss']:>10.4f}{r['brier']:>8.4f}"
        )


def run_evaluation(dataset_id, name):
    print(f"Dataset {dataset_id}: {name}")
    samples = generate_synthetic_dataset(dataset_id)
    train, validation, test = split_samples_chronologically(samples)

    train_features, y_train = samples_to_arrays(train)
    validation_features, y_validation = samples_to_arrays(validation)
    test_features, y_test = samples_to_arrays(test)
    test_day_indices = np.array([s["day_index"] for s in test])

    print(
        f"Samples train/validation/test: {len(train)}/{len(validation)}/{len(test)}  "
        f"positive rate: {y_train.mean():.4f}/{y_validation.mean():.4f}/{y_test.mean():.4f}"
    )

    results = []

    oracle_validation = np.array([s["true_prob"] for s in validation])
    oracle_test = np.array([s["true_prob"] for s in test])
    oracle_threshold = select_threshold(y_validation, oracle_validation)
    results.append(
        evaluate_predictions("oracle", y_test, oracle_test, test_day_indices, oracle_threshold)
    )

    baseline_scaler = StandardScaler().fit(train_features)
    baseline = LogisticRegression(max_iter=1000).fit(baseline_scaler.transform(train_features), y_train)
    baseline_validation = baseline.predict_proba(baseline_scaler.transform(validation_features))[:, 1]
    baseline_test = baseline.predict_proba(baseline_scaler.transform(test_features))[:, 1]
    results.append(
        evaluate_predictions(
            "logistic_regression",
            y_test,
            baseline_test,
            test_day_indices,
            select_threshold(y_validation, baseline_validation),
        )
    )

    for strategy in IMBALANCE_STRATEGIES:
        model, scaler, calibrator = train_bnn(train, validation, strategy)
        validation_probabilities = predict_bnn_probabilities(model, scaler, calibrator, validation)
        test_probabilities = predict_bnn_probabilities(model, scaler, calibrator, test)
        results.append(
            evaluate_predictions(
                f"bnn_{strategy}",
                y_test,
                test_probabilities,
                test_day_indices,
                select_threshold(y_validation, validation_probabilities),
            )
        )

    print_result_table(results)
    print()
    return results


if __name__ == "__main__":
    np.random.seed(RANDOM_SEED)

    datasets = [
        (1, "Road Proximity Dataset"),
        (2, "Slope Dataset"),
        (3, "Elevation Dataset"),
        (4, "Recency Dataset"),
        (5, "Sustained Dataset (Attacks Last 30 Days)"),
        (6, "Combined Interactions"),
    ]

    all_results = []
    for dataset_id, dataset_name in datasets:
        all_results.append(run_evaluation(dataset_id, dataset_name))

    print("Mean PR-AUC as a fraction of oracle PR-AUC across datasets")
    model_names = [r["model"] for r in all_results[0]][1:]
    for position, model_name in enumerate(model_names, start=1):
        ratios = [run[position]["pr_auc"] / run[0]["pr_auc"] for run in all_results]
        print(f"{model_name:<24}{np.mean(ratios):>8.4f}")