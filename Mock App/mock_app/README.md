# mock_app

A new Flutter project.

## Audio listening

On Android, open the **Listen** tab and tap **Start Listening**. The app
requests microphone and notification permission, then starts a microphone
foreground service with a persistent notification. Audio is processed locally
in overlapping 5-second windows at 32 kHz; the page displays all 27 model
classes and their current confidence scores, along with a live microphone
volume meter in dBFS. Use **Stop Listening** on the page or in the
foreground-service notification to stop capture.

The foreground service is Android-only. Microphone audio is not saved or sent
over the network. Initial results appear after the first 5 seconds of capture.

## ONNX audio model demo

The **Run ONNX model demo** button on the Connection page runs one inference
with a zero-valued mono waveform of 160,000 samples (5 seconds at 32 kHz) and
shows the highest-scoring output class and score.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Learn Flutter](https://docs.flutter.dev/get-started/learn-flutter)
- [Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Flutter learning resources](https://docs.flutter.dev/reference/learning-resources)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
