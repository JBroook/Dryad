# mock_app

A new Flutter project.

## ONNX audio model demo

Tap **Run ONNX model demo** in the app to run one inference with
`models/dryad_audio_model.onnx`. The demo passes a zero-valued mono waveform
of 160,000 samples (5 seconds at 32 kHz) to the model's `waveform` input and
shows the highest-scoring output class and score. This verifies model loading
and inference; it does not yet capture microphone audio.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
