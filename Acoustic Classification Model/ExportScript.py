import torch
import onnx
import onnxruntime as ort
from torch import nn

from models import Cnn10

MODEL_PATH = "trainedModels/26_class_ac_real/fold_4/checkpoint_epoch50.pth"
OUTPUT_PATH = "trainedModels/26_class_ac_real/dryad_audio_model.onnx"

model = Cnn10(
        sample_rate=32000,
        window_size=1024,
        hop_size=320,
        mel_bins=64,
        fmin=50,
        fmax=14000,
        classes_num=50
    )
model.fc_audioset = nn.Linear(512, 26, bias=True)

checkpoint = torch.load(MODEL_PATH, map_location="cpu")
model.load_state_dict(checkpoint["model_state_dict"])

model.eval()

# [batch_size, number_of_audio_samples]
sample_rate = 32000
duration_seconds = 5

example_input = torch.randn(1, sample_rate * duration_seconds)

input_data = example_input.cpu().numpy().astype("float32")

with torch.inference_mode():
    pytorch_output = model(example_input)

torch.onnx.export(
    model,
    (example_input,),
    OUTPUT_PATH,
    input_names=["waveform"],
    output_names=["scores"],
    opset_version=17,
    dynamo=False,
)

onnx_model = onnx.load(OUTPUT_PATH)
onnx.checker.check_model(onnx_model)

session = ort.InferenceSession(
    OUTPUT_PATH,
    providers=["CPUExecutionProvider"],
)

onnx_output = session.run(
    None,
    {"waveform": input_data}
)

print("PyTorch output type:", type(pytorch_output))
print("PyTorch output keys:", pytorch_output.keys())

for key, value in pytorch_output.items():
    if isinstance(value, torch.Tensor):
        print(f"PyTorch '{key}' shape:", tuple(value.shape))
    else:
        print(f"PyTorch '{key}' type:", type(value))

print("ONNX output count:", len(onnx_output))

for i, value in enumerate(onnx_output):
    print(f"ONNX output {i} shape:", value.shape)

print("Export and inference completed.")

import numpy as np

output_keys = [
    "clipwise_output",
    "embedding",
    "logits",
]

for i, key in enumerate(output_keys):
    pytorch_array = (
        pytorch_output[key]
        .detach()
        .cpu()
        .numpy()
    )

    onnx_array = onnx_output[i]

    max_diff = np.max(
        np.abs(pytorch_array - onnx_array)
    )

    mean_diff = np.mean(
        np.abs(pytorch_array - onnx_array)
    )

    print(f"\n{key}:")
    print("  Maximum absolute difference:", max_diff)
    print("  Mean absolute difference:", mean_diff)
    print(
        "  Numerically close:",
        np.allclose(
            pytorch_array,
            onnx_array,
            rtol=1e-3,
            atol=1e-5,
        ),
    )