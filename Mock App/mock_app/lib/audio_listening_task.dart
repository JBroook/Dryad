import 'dart:async';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:record/record.dart';

import 'audio_model_runner.dart';

@pragma('vm:entry-point')
void startAudioListeningTask() {
  FlutterForegroundTask.setTaskHandler(AudioListeningTaskHandler());
}

class AudioListeningTaskHandler extends TaskHandler {
  final AudioModelRunner _model = AudioModelRunner();
  final Float32List _audioWindow = Float32List(audioWindowSampleCount);

  AudioRecorder? _recorder;
  StreamSubscription<Uint8List>? _audioSubscription;
  Future<void>? _inference;
  int _writePosition = 0;
  int _samplesWritten = 0;
  DateTime? _lastInferenceAt;
  DateTime? _lastVolumeUpdateAt;
  bool _stopping = false;
  bool _errorReported = false;

  @override
  Future<void> onStart(DateTime timestamp, TaskStarter starter) async {
    try {
      await _model.initialize();
      _recorder = AudioRecorder();

      final stream = await _recorder!.startStream(
        const RecordConfig(
          encoder: AudioEncoder.pcm16bits,
          sampleRate: audioSampleRate,
          numChannels: 1,
          androidConfig: AndroidRecordConfig(
            audioSource: AndroidAudioSource.mic,
          ),
          streamBufferSize: 4096,
        ),
      );
      _audioSubscription = stream.listen(
        _processAudioChunk,
        onError: (Object error, StackTrace stackTrace) {
          _fail('Microphone stream error: $error');
        },
        onDone: () {
          if (!_stopping) {
            _fail('The microphone audio stream ended.');
          }
        },
      );
      _sendState('listening');
    } catch (error) {
      _fail('Unable to start audio inference: $error');
    }
  }

  void _processAudioChunk(Uint8List bytes) {
    if (_stopping) {
      return;
    }

    final byteData = ByteData.sublistView(bytes);
    final sampleCount = bytes.length ~/ 2;
    var sumOfSquares = 0.0;
    for (var index = 0; index < sampleCount; index++) {
      final sample = byteData.getInt16(index * 2, Endian.little) / 32768.0;
      sumOfSquares += sample * sample;
      _audioWindow[_writePosition] = sample;
      _writePosition = (_writePosition + 1) % _audioWindow.length;
      if (_samplesWritten < _audioWindow.length) {
        _samplesWritten++;
      }
    }

    final now = DateTime.now();
    if (sampleCount > 0 &&
        (_lastVolumeUpdateAt == null ||
            now.difference(_lastVolumeUpdateAt!) >=
                const Duration(milliseconds: 100))) {
      _lastVolumeUpdateAt = now;
      final rms = math.sqrt(sumOfSquares / sampleCount);
      final decibels = rms == 0
          ? -60.0
          : (20 * math.log(rms) / math.ln10).clamp(-60.0, 0.0);
      FlutterForegroundTask.sendDataToMain({
        'type': 'volume',
        'decibels': decibels,
      });
    }

    if (_samplesWritten == _audioWindow.length &&
        _inference == null &&
        (_lastInferenceAt == null ||
            now.difference(_lastInferenceAt!) >= const Duration(seconds: 1))) {
      _lastInferenceAt = now;
      _inference = _runInference();
    }

  }

  Future<void> _runInference() async {
    try {
      final orderedWindow = Float32List(_audioWindow.length);
      for (var index = 0; index < orderedWindow.length; index++) {
        orderedWindow[index] =
            _audioWindow[(_writePosition + index) % _audioWindow.length];
      }

      final result = await _model.run(orderedWindow);
      if (!_stopping) {
        FlutterForegroundTask.sendDataToMain({
          'type': 'scores',
          'scores': result.classScores,
        });
      }
    } catch (error) {
      _fail('Audio inference failed: $error');
    } finally {
      _inference = null;
    }
  }

  void _fail(String message) {
    if (_errorReported) {
      return;
    }
    _errorReported = true;
    FlutterForegroundTask.sendDataToMain({'type': 'error', 'message': message});
    unawaited(FlutterForegroundTask.stopService());
  }

  void _reportCleanupError(String action, Object error) {
    FlutterForegroundTask.sendDataToMain({
      'type': 'error',
      'message': 'Could not $action audio cleanly: $error',
    });
  }

  void _sendState(String state) {
    FlutterForegroundTask.sendDataToMain({'type': 'state', 'state': state});
  }

  @override
  void onRepeatEvent(DateTime timestamp) {}

  @override
  Future<void> onDestroy(DateTime timestamp, bool isTimeout) async {
    _stopping = true;
    try {
      await _audioSubscription?.cancel();
    } catch (error) {
      _reportCleanupError('stop the microphone stream', error);
    }
    _audioSubscription = null;

    final recorder = _recorder;
    _recorder = null;
    if (recorder != null) {
      try {
        await recorder.stop();
      } catch (error) {
        _reportCleanupError('stop microphone capture', error);
      }
      try {
        await recorder.dispose();
      } catch (error) {
        _reportCleanupError('release the microphone', error);
      }
    }

    try {
      await _inference;
    } finally {
      await _model.close();
    }
    _sendState('stopped');
  }

  @override
  void onNotificationButtonPressed(String id) {
    if (id == 'stop_listening') {
      unawaited(FlutterForegroundTask.stopService());
    }
  }
}
