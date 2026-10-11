import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:record/record.dart';

import 'audio_classes.dart';
import 'audio_listening_task.dart';

class AudioListeningScreen extends StatefulWidget {
  const AudioListeningScreen({super.key});

  @override
  State<AudioListeningScreen> createState() => _AudioListeningScreenState();
}

class _AudioListeningScreenState extends State<AudioListeningScreen> {
  List<double> _scores = List<double>.filled(audioClassNames.length, 0);
  bool _hasScores = false;
  double _volumeDecibels = -60;
  bool _hasVolume = false;
  String _status = 'Not listening';
  String? _error;
  bool _isStarting = false;
  bool _isListening = false;

  @override
  void initState() {
    super.initState();
    FlutterForegroundTask.addTaskDataCallback(_onTaskData);
    _restoreServiceState();
  }

  Future<void> _restoreServiceState() async {
    if (kIsWeb || !Platform.isAndroid) {
      return;
    }
    final isRunning = await FlutterForegroundTask.isRunningService;
    if (mounted && isRunning) {
      setState(() {
        _isListening = true;
        _status = 'Listening in the background';
      });
    }
  }

  void _onTaskData(Object data) {
    if (data is! Map) {
      return;
    }

    final type = data['type'];
    if (type == 'volume') {
      final value = data['decibels'];
      if (value is! num || !value.isFinite || !mounted) {
        return;
      }
      setState(() {
        _volumeDecibels = value.toDouble().clamp(-60.0, 0.0);
        _hasVolume = true;
      });
    } else if (type == 'scores') {
      final values = data['scores'];
      if (values is! List || values.length != audioClassNames.length) {
        return;
      }
      final scores = values.map((value) => (value as num).toDouble()).toList();
      if (!mounted) {
        return;
      }
      setState(() {
        _scores = scores;
        _hasScores = true;
        _error = null;
        _status = 'Listening in the background';
        _isListening = true;
      });
    } else if (type == 'state') {
      final state = data['state']?.toString();
      if (!mounted || state == null) {
        return;
      }
      setState(() {
        _isListening = state == 'listening';
        if (state != 'listening') {
          _volumeDecibels = -60;
          _hasVolume = false;
        }
        _status = state == 'listening'
            ? 'Listening in the background'
            : 'Not listening';
      });
    } else if (type == 'error') {
      final message = data['message']?.toString();
      if (!mounted || message == null) {
        return;
      }
      setState(() {
        _isListening = false;
        _status = 'Listening stopped';
        _error = message;
      });
    }
  }

  Future<void> _startListening() async {
    if (kIsWeb || !Platform.isAndroid) {
      setState(() {
        _error = 'Background microphone listening is currently supported on Android.';
      });
      return;
    }

    setState(() {
      _isStarting = true;
      _error = null;
      _status = 'Requesting permissions...';
    });

    try {
      final permissionRecorder = AudioRecorder();
      bool microphoneGranted;
      try {
        microphoneGranted = await permissionRecorder.hasPermission();
      } finally {
        await permissionRecorder.dispose();
      }
      if (!microphoneGranted) {
        setState(() {
          _status = 'Microphone permission required';
          _error =
              'Microphone permission is required. If you denied the request, '
              'enable it in Android settings.';
        });
        return;
      }

      var notificationPermission =
          await FlutterForegroundTask.checkNotificationPermission();
      if (notificationPermission != NotificationPermission.granted) {
        notificationPermission =
            await FlutterForegroundTask.requestNotificationPermission();
      }
      if (notificationPermission != NotificationPermission.granted) {
        setState(() {
          _status = 'Notification permission required';
          _error =
              notificationPermission ==
                  NotificationPermission.permanently_denied
              ? 'Enable notifications in Android settings to show the active microphone service.'
              : 'Allow notifications so Android can show the active microphone service.';
        });
        return;
      }

      final result = await FlutterForegroundTask.startService(
        serviceId: 121,
        serviceTypes: [ForegroundServiceTypes.microphone],
        notificationTitle: 'Dryad is listening',
        notificationText: 'Audio is analyzed on this device',
        notificationButtons: const [
          NotificationButton(id: 'stop_listening', text: 'Stop'),
        ],
        callback: startAudioListeningTask,
      );

      if (result is ServiceRequestFailure) {
        throw StateError(
          'Could not start the listening service: ${result.error}',
        );
      }
      if (mounted) {
        setState(() {
          _isListening = true;
          _status = 'Starting microphone...';
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _status = 'Listening stopped';
          _error = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isStarting = false;
        });
      }
    }
  }

  Future<void> _stopListening() async {
    setState(() {
      _isStarting = true;
    });
    try {
      final result = await FlutterForegroundTask.stopService();
      if (result is ServiceRequestFailure) {
        throw StateError(
          'Could not stop the listening service: ${result.error}',
        );
      }
      if (mounted) {
        setState(() {
          _isListening = false;
          _status = 'Not listening';
          _error = null;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isStarting = false;
        });
      }
    }
  }

  @override
  void dispose() {
    FlutterForegroundTask.removeTaskDataCallback(_onTaskData);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rankedScores = List<int>.generate(audioClassNames.length, (i) => i)
      ..sort((left, right) => _scores[right].compareTo(_scores[left]));

    return Scaffold(
      appBar: AppBar(title: const Text('Dryad')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                'On-device sound classification',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 4),
              Text(
                'Analyzes rolling 5-second audio windows at 32 kHz. '
                'Listening continues while this Android app is in the background.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _isStarting
                    ? null
                    : _isListening
                    ? _stopListening
                    : _startListening,
                icon: _isStarting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Icon(_isListening ? Icons.stop : Icons.mic),
                label: Text(
                  _isStarting
                      ? 'Please wait...'
                      : _isListening
                      ? 'Stop Listening'
                      : 'Start Listening',
                ),
              ),
              const SizedBox(height: 8),
              Text(_status, textAlign: TextAlign.center),
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.mic_none),
                  const SizedBox(width: 8),
                  const Expanded(child: Text('Microphone volume')),
                  Text(
                    _hasVolume
                        ? '${_volumeDecibels.toStringAsFixed(0)} dBFS'
                        : '-- dBFS',
                  ),
                ],
              ),
              const SizedBox(height: 6),
              LinearProgressIndicator(
                value: _hasVolume
                    ? ((_volumeDecibels + 60) / 60).clamp(0.0, 1.0)
                    : 0,
                minHeight: 8,
                borderRadius: BorderRadius.circular(8),
                color: Theme.of(context).colorScheme.tertiary,
                backgroundColor: Theme.of(context)
                    .colorScheme
                    .surfaceContainerHighest,
              ),
              const SizedBox(height: 12),
              Text(
                'Class confidence',
                style: Theme.of(context).textTheme.titleSmall,
              ),
              const SizedBox(height: 4),
              Expanded(
                child: ListView.separated(
                  itemCount: rankedScores.length,
                  separatorBuilder: (context, index) =>
                      const SizedBox(height: 2),
                  itemBuilder: (context, index) {
                    final classIndex = rankedScores[index];
                    final score = _scores[classIndex].clamp(0.0, 1.0);
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 5),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(audioClassNames[classIndex]),
                              ),
                              Text(
                                _hasScores
                                    ? '${(score * 100).toStringAsFixed(1)}%'
                                    : '--',
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          LinearProgressIndicator(value: score),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
