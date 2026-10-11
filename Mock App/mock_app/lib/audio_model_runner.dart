import 'dart:typed_data';

import 'package:flutter_onnxruntime/flutter_onnxruntime.dart';

const String _modelAssetPath = 'models/dryad_audio_model.onnx';
const int _sampleRate = 32000;
const int _windowSeconds = 5;
const int _sampleCount = _sampleRate * _windowSeconds;

class AudioInferenceResult {
  const AudioInferenceResult({
    required this.predictedClass,
    required this.confidence,
    required this.outputNames,
  });

  final int predictedClass;
  final double confidence;
  final List<String> outputNames;
}

Future<AudioInferenceResult> runExampleAudioInference() async {
  final runtime = OnnxRuntime();
  OrtSession? session;
  OrtValue? input;
  Map<String, OrtValue>? outputs;

  try {
    session = await runtime.createSessionFromAsset(_modelAssetPath);

    if (!session.inputNames.contains('waveform')) {
      throw StateError(
        'Expected model input "waveform", found ${session.inputNames}.',
      );
    }
    if (session.outputNames.isEmpty) {
      throw StateError('The audio model has no outputs.');
    }

    final waveform = Float32List(_sampleCount);
    input = await OrtValue.fromList(waveform, [1, _sampleCount]);
    outputs = await session.run({'waveform': input});

    if (outputs.isEmpty) {
      throw StateError('The audio model returned no output tensors.');
    }
    final scoreName = session.outputNames.first;
    final scoresTensor = outputs[scoreName];
    if (scoresTensor == null) {
      throw StateError('The audio model did not return "$scoreName".');
    }

    final scores = (await scoresTensor.asFlattenedList())
        .map((value) => (value as num).toDouble())
        .toList();
    if (scores.isEmpty) {
      throw StateError('The audio model returned an empty score tensor.');
    }

    var predictedClass = 0;
    for (var index = 1; index < scores.length; index++) {
      if (scores[index] > scores[predictedClass]) {
        predictedClass = index;
      }
    }

    return AudioInferenceResult(
      predictedClass: predictedClass,
      confidence: scores[predictedClass],
      outputNames: List.unmodifiable(session.outputNames),
    );
  } finally {
    if (input != null) {
      await input.dispose();
    }
    for (final output in outputs?.values ?? const <OrtValue>[]) {
      await output.dispose();
    }
    if (session != null) {
      await session.close();
    }
  }
}
