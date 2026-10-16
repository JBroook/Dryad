import 'dart:typed_data';

import 'package:flutter_onnxruntime/flutter_onnxruntime.dart';

import 'audio_classes.dart';

const String audioModelAssetPath = 'models/dryad_audio_model.onnx';
const int audioSampleRate = 32000;
const int audioWindowSeconds = 5;
const int audioWindowSampleCount = audioSampleRate * audioWindowSeconds;

class AudioInferenceResult {
  const AudioInferenceResult({
    required this.classScores,
    required this.outputNames,
  });

  final List<double> classScores;
  final List<String> outputNames;

  int get predictedClass {
    var result = 0;
    for (var index = 1; index < classScores.length; index++) {
      if (classScores[index] > classScores[result]) {
        result = index;
      }
    }
    return result;
  }

  double get confidence => classScores[predictedClass];
}

class AudioModelRunner {
  final OnnxRuntime _runtime = OnnxRuntime();
  OrtSession? _session;

  List<String> get outputNames {
    final session = _session;
    if (session == null) {
      throw StateError('The audio model is not initialized.');
    }
    return session.outputNames;
  }

  Future<void> initialize() async {
    if (_session != null) {
      return;
    }

    final session = await _runtime.createSessionFromAsset(audioModelAssetPath);
    if (!session.inputNames.contains('waveform')) {
      await session.close();
      throw StateError(
        'Expected model input "waveform", found ${session.inputNames}.',
      );
    }
    if (session.outputNames.isEmpty) {
      await session.close();
      throw StateError('The audio model has no outputs.');
    }
    _session = session;
  }

  Future<AudioInferenceResult> run(Float32List waveform) async {
    final session = _session;
    if (session == null) {
      throw StateError('The audio model is not initialized.');
    }
    if (waveform.length != audioWindowSampleCount) {
      throw ArgumentError.value(
        waveform.length,
        'waveform.length',
        'Expected $audioWindowSampleCount mono samples.',
      );
    }

    OrtValue? input;
    Map<String, OrtValue>? outputs;
    try {
      input = await OrtValue.fromList(waveform, [1, audioWindowSampleCount]);
      outputs = await session.run({'waveform': input});
      if (outputs.isEmpty) {
        throw StateError('The audio model returned no output tensors.');
      }

      final scoreEntry = await _findClassScoreOutput(outputs);
      final scores = scoreEntry.value
          .map((value) => (value as num).toDouble())
          .toList(growable: false);
      if (scores.length != audioClassNames.length) {
        throw StateError(
          'Expected ${audioClassNames.length} class scores, '
          'received ${scores.length} from "${scoreEntry.key}".',
        );
      }
      if (scores.any((score) => !score.isFinite)) {
        throw StateError('The audio model returned non-finite class scores.');
      }

      return AudioInferenceResult(
        classScores: List.unmodifiable(scores),
        outputNames: List.unmodifiable(session.outputNames),
      );
    } finally {
      if (input != null) {
        await input.dispose();
      }
      for (final output in outputs?.values ?? const <OrtValue>[]) {
        await output.dispose();
      }
    }
  }

  Future<MapEntry<String, List<dynamic>>> _findClassScoreOutput(
    Map<String, OrtValue> outputs,
  ) async {
    final candidates = <MapEntry<String, OrtValue>>[];
    for (final preferredName in ['clipwise_output', 'scores']) {
      final output = outputs[preferredName];
      if (output != null) {
        candidates.add(MapEntry(preferredName, output));
      }
    }
    candidates.addAll(
      outputs.entries.where(
        (entry) => !candidates.any((candidate) => candidate.key == entry.key),
      ),
    );

    for (final candidate in candidates) {
      final values = await candidate.value.asFlattenedList();
      if (values.length == audioClassNames.length) {
        return MapEntry(candidate.key, values);
      }
    }

    throw StateError(
      'The audio model did not return a tensor with '
      '${audioClassNames.length} class scores.',
    );
  }

  Future<void> close() async {
    final session = _session;
    _session = null;
    await session?.close();
  }
}

Future<AudioInferenceResult> runExampleAudioInference() async {
  final runner = AudioModelRunner();
  try {
    await runner.initialize();
    return await runner.run(Float32List(audioWindowSampleCount));
  } finally {
    await runner.close();
  }
}
