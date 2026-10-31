import json
import os
import glob
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    ConfusionMatrixDisplay
)


def load_fold_stats(base_dir):
    fold_files = sorted(
        glob.glob(os.path.join(base_dir, "fold_*/training_stats.json"))
    )

    if not fold_files:
        raise FileNotFoundError(
            f"No training_stats.json files found under {base_dir}"
        )

    all_fold_stats = []

    for fpath in fold_files:
        with open(fpath, "r") as f:
            all_fold_stats.append(json.load(f))

    return all_fold_stats


def get_metric_array(all_fold_stats, metric):
    """
    Extract a metric from all folds.
    Missing values are represented as NaN.
    """
    return np.array([
        [
            item.get(metric, np.nan)
            if item.get(metric) is not None else np.nan
            for item in fold
        ]
        for fold in all_fold_stats
    ], dtype=float)


def plot_mean_std(ax, epochs, values, label, color):
    """
    Plot mean and standard deviation across folds.
    """
    mean = np.nanmean(values, axis=0)
    std = np.nanstd(values, axis=0)

    ax.plot(
        epochs,
        mean,
        label=label,
        color=color,
        linewidth=2
    )

    ax.fill_between(
        epochs,
        mean - std,
        mean + std,
        color=color,
        alpha=0.15
    )

def plot_cv_learning_curves(all_fold_stats, save_path=None):

    num_folds = len(all_fold_stats)
    epochs = [item['epoch'] for item in all_fold_stats[0]]

    # Extract metrics
    train_losses = get_metric_array(all_fold_stats, 'loss')
    test_losses = get_metric_array(all_fold_stats, 'test_loss')

    train_accs = get_metric_array(all_fold_stats, 'accuracy')
    test_accs = get_metric_array(all_fold_stats, 'test_accuracy')

    precision_macro = get_metric_array(all_fold_stats, 'test_precision_macro')
    precision_weighted = get_metric_array(all_fold_stats, 'test_precision_weighted')

    recall_macro = get_metric_array(all_fold_stats, 'test_recall_macro')
    recall_weighted = get_metric_array(all_fold_stats, 'test_recall_weighted')

    f1_macro = get_metric_array(all_fold_stats, 'test_f1_macro')
    f1_weighted = get_metric_array(all_fold_stats, 'test_f1_weighted')

    roc_auc_macro = get_metric_array(all_fold_stats, 'test_roc_auc_macro')

    # Create figure with increased height
    fig, axes = plt.subplots(2, 2, figsize=(16, 13))

    # 1. LOSS
    ax = axes[0, 0]

    plot_mean_std(ax, epochs, train_losses, 'Train Loss', 'blue')
    plot_mean_std(ax, epochs, test_losses, 'Test Loss', 'orange')

    ax.set_title(f'{num_folds}-Fold CV Loss (Mean ± Std)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    # 2. ACCURACY
    ax = axes[0, 1]

    plot_mean_std(ax, epochs, train_accs, 'Train Accuracy', 'blue')
    plot_mean_std(ax, epochs, test_accs, 'Test Accuracy', 'orange')

    ax.set_title(f'{num_folds}-Fold CV Accuracy (Mean ± Std)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Accuracy (%)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    # 3. PRECISION, RECALL AND F1
    ax = axes[1, 0]

    plot_mean_std(ax, epochs, precision_macro, 'Precision (Macro)', 'blue')
    plot_mean_std(ax, epochs, recall_macro, 'Recall (Macro)', 'green')
    plot_mean_std(ax, epochs, f1_macro, 'F1 (Macro)', 'red')

    plot_mean_std(ax, epochs, precision_weighted, 'Precision (Weighted)', 'cyan')
    plot_mean_std(ax, epochs, recall_weighted, 'Recall (Weighted)', 'lime')
    plot_mean_std(ax, epochs, f1_weighted, 'F1 (Weighted)', 'magenta')

    ax.set_title('Test Precision, Recall and F1 (Mean ± Std)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Score')
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, ncol=2)
    ax.grid(True, linestyle='--', alpha=0.6)

    # 4. ROC AUC
    ax = axes[1, 1]

    plot_mean_std(ax, epochs, roc_auc_macro, 'ROC AUC (Macro)', 'purple')

    ax.set_title('Test ROC AUC (Mean ± Std)')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('ROC AUC')
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)

    # FIGURE SPACING
    fig.suptitle(
        f'{num_folds}-Fold Cross-Validation Training Performance',
        fontsize=16,
        fontweight='bold',
        y=0.98
    )

    # More space between top and bottom plots
    plt.subplots_adjust(
        left=0.07,
        right=0.97,
        top=0.92,
        bottom=0.07,
        hspace=0.40,
        wspace=0.22
    )

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    plt.show()



def plot_confusion_matrix(
    y_true,
    y_pred,
    class_names,
    save_path=None,
    title="Confusion Matrix"
):

    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=range(len(class_names))
    )

    fig, ax = plt.subplots(
        figsize=(
            max(8, len(class_names) * 0.4),
            max(6, len(class_names) * 0.4)
        )
    )

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=class_names
    )

    disp.plot(
        cmap=plt.cm.Blues,
        ax=ax,
        xticks_rotation=45,
        colorbar=True
    )

    ax.set_title(title)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300)

    plt.show()



def summarize_cross_validation(base_dir, class_names=None):

    all_fold_stats = load_fold_stats(base_dir)

    print("\n========== CROSS-VALIDATION SUMMARY ==========\n")

    # Metrics to summarize at the final epoch
    metric_names = [
        'loss',
        'accuracy',
        'test_loss',
        'test_accuracy',
        'test_precision_macro',
        'test_precision_weighted',
        'test_recall_macro',
        'test_recall_weighted',
        'test_f1_macro',
        'test_f1_weighted',
        'test_roc_auc_macro'
    ]

    fold_metrics = {metric: [] for metric in metric_names}

    all_y_true = []
    all_y_pred = []

    # -----------------------------------------
    # INDIVIDUAL FOLD RESULTS
    # -----------------------------------------
    print("Individual Fold Results (Final Epoch):\n")

    for i, fold_stat in enumerate(all_fold_stats, 1):

        last_epoch = fold_stat[-1]

        print(
            f"Fold {i} -> "
            f"Test Loss: {last_epoch['test_loss']:.4f} | "
            f"Test Acc: {last_epoch['test_accuracy']:.2f}%"
        )

        # Collect final epoch metrics
        for metric in metric_names:

            value = last_epoch.get(metric)

            if value is not None:
                fold_metrics[metric].append(value)

        # Collect predictions if available
        if 'y_true' in last_epoch and 'y_pred' in last_epoch:
            all_y_true.extend(last_epoch['y_true'])
            all_y_pred.extend(last_epoch['y_pred'])

    # -----------------------------------------
    # OVERALL MEAN ± STANDARD DEVIATION
    # -----------------------------------------
    print("\n========== OVERALL MEAN ± STD ==========\n")

    summary_labels = {
        'loss': 'Training Loss',
        'accuracy': 'Training Accuracy',
        'test_loss': 'Test Loss',
        'test_accuracy': 'Test Accuracy',
        # 'test_precision_macro': 'Precision (Macro)',
        'test_precision_weighted': 'Precision',
        # 'test_recall_macro': 'Recall (Macro)',
        'test_recall_weighted': 'Recall',
        # 'test_f1_macro': 'F1-Score (Macro)',
        'test_f1_weighted': 'F1-Score',
        'test_roc_auc_macro': 'ROC AUC (Macro)'
    }

    for metric, label in summary_labels.items():

        values = fold_metrics[metric]

        if values:
            print(
                f"{label:<25}: "
                f"{np.mean(values):.4f} ± {np.std(values):.4f}"
            )

    # -----------------------------------------
    # LEARNING CURVES
    # -----------------------------------------
    plot_cv_learning_curves(
        all_fold_stats,
        save_path=os.path.join(
            base_dir,
            "cv_learning_curves.png"
        )
    )

    # -----------------------------------------
    # CONFUSION MATRIX
    # -----------------------------------------
    if all_y_true and all_y_pred:

        if class_names is None:

            num_classes = max(
                max(all_y_true),
                max(all_y_pred)
            ) + 1

            class_names = [
                f"Class_{i}"
                for i in range(num_classes)
            ]

        plot_confusion_matrix(
            y_true=all_y_true,
            y_pred=all_y_pred,
            class_names=class_names,
            save_path=os.path.join(
                base_dir,
                "cv_confusion_matrix.png"
            ),
            title="Overall Cross-Validation Confusion Matrix"
        )



if __name__ == '__main__':

    training_output_dir = "trainedModels/26_class_ac"

    class_names = [
        f"Class_{i}"
        for i in range(27)
    ]

    summarize_cross_validation(
        training_output_dir,
        class_names=class_names
    )
