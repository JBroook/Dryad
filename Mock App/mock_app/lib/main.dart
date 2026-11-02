import 'dart:convert';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:http/http.dart' as http;
import 'package:mock_app/audio_model_runner.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'audio_listening_screen.dart';

const String _wifiHost = '192.168.100.7';
const String _hotspotHost = '10.111.194.78';
const String _deviceIdStorageKey = 'device_id';
const String _threatClassesStorageKey = 'threat_classes';
const String _networkModeStorageKey = 'network_mode_hotspot';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  FlutterForegroundTask.initCommunicationPort();
  FlutterForegroundTask.init(
    androidNotificationOptions: AndroidNotificationOptions(
      channelId: 'dryad_audio_listening',
      channelName: 'Dryad audio listening',
      channelDescription: 'Shows when Dryad is listening for sounds.',
      onlyAlertOnce: true,
    ),
    iosNotificationOptions: const IOSNotificationOptions(
      showNotification: false,
    ),
    foregroundTaskOptions: ForegroundTaskOptions(
      eventAction: ForegroundTaskEventAction.nothing(),
      allowWakeLock: true,
      stopWithTask: false,
    ),
  );
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Dryad',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2E7D32),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF07130D),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF0B1A12),
          foregroundColor: Color(0xFFE8F5E9),
        ),
        useMaterial3: true,
      ),
      home: const AppShell(),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _selectedPage = 0;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedPage,
        children: const [CodeRequestScreen(), AudioListeningScreen()],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedPage,
        onDestinationSelected: (index) {
          setState(() {
            _selectedPage = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.device_hub_outlined),
            selectedIcon: Icon(Icons.device_hub),
            label: 'Connection',
          ),
          NavigationDestination(
            icon: Icon(Icons.graphic_eq_outlined),
            selectedIcon: Icon(Icons.graphic_eq),
            label: 'Listen',
          ),
        ],
      ),
    );
  }
}

class CodeRequestScreen extends StatefulWidget {
  const CodeRequestScreen({super.key});

  @override
  State<CodeRequestScreen> createState() => _CodeRequestScreenState();
}

class _CodeRequestScreenState extends State<CodeRequestScreen> {
  final TextEditingController _codeController = TextEditingController();
  final ValueNotifier<String> _statusMessage = ValueNotifier('');
  final ValueNotifier<int?> _deviceId = ValueNotifier<int?>(null);
  final ValueNotifier<List<int>> _threatClasses = ValueNotifier<List<int>>([]);
  bool _isSendingCode = false;
  bool _isSendingReport = false;
  bool _isRunningModel = false;
  bool _isHotspotMode = false;

  bool get _isBusy => _isSendingCode || _isSendingReport || _isRunningModel;

  String get _apiHost => _isHotspotMode ? _hotspotHost : _wifiHost;

  String get _baseApiUrl => 'http://$_apiHost:8000';

  @override
  void initState() {
    super.initState();
    _restoreSavedDeviceData();
    _restoreNetworkMode();
  }

  Future<void> _restoreSavedDeviceData() async {
    final prefs = await SharedPreferences.getInstance();
    final savedDeviceId = prefs.getInt(_deviceIdStorageKey);
    final savedThreatClasses =
        prefs.getStringList(_threatClassesStorageKey) ?? const [];

    if (!mounted) {
      return;
    }

    _deviceId.value = savedDeviceId;
    _threatClasses.value = savedThreatClasses
        .map((entry) => int.tryParse(entry))
        .whereType<int>()
        .toList();

    setState(() {});
  }

  Future<void> _restoreNetworkMode() async {
    final prefs = await SharedPreferences.getInstance();
    final savedMode = prefs.getBool(_networkModeStorageKey);

    if (!mounted) {
      return;
    }

    _isHotspotMode = savedMode ?? false;
    setState(() {});
  }

  Future<void> _persistNetworkMode() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_networkModeStorageKey, _isHotspotMode);
  }

  Future<void> _persistDeviceData(Map<String, dynamic> payload) async {
    final prefs = await SharedPreferences.getInstance();

    final rawDeviceId = payload['device_id'];
    if (rawDeviceId != null) {
      final parsedDeviceId = int.tryParse(rawDeviceId.toString());
      if (parsedDeviceId != null) {
        _deviceId.value = parsedDeviceId;
        await prefs.setInt(_deviceIdStorageKey, parsedDeviceId);
      }
    }

    final rawThreatClasses = payload['threat_classes'];
    final parsedThreatClasses = <int>[];

    if (rawThreatClasses is List) {
      for (final item in rawThreatClasses) {
        final parsedThreatClass = int.tryParse(item.toString());
        if (parsedThreatClass != null) {
          parsedThreatClasses.add(parsedThreatClass);
        }
      }
    }

    _threatClasses.value = parsedThreatClasses;
    await prefs.setStringList(
      _threatClassesStorageKey,
      parsedThreatClasses.map((value) => value.toString()).toList(),
    );
  }

  Future<void> _sendCode() async {
    final code = _codeController.text.trim();
    if (code.isEmpty) {
      _statusMessage.value = 'Please enter a valid code.';
      return;
    }

    setState(() {
      _isSendingCode = true;
    });

    _statusMessage.value = 'Sending code...';

    try {
      final response = await http.post(
        Uri.parse('$_baseApiUrl/api/devices/connect'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'code': code,
          'battery': 87,
          'coordinate': {
            'type': 'Point',
            'coordinates': [100.195278, 5.458981],
          },
        }),
      );

      if (!mounted) {
        return;
      }

      final decoded = response.body.isNotEmpty ? jsonDecode(response.body) : {};

      if (response.statusCode >= 200 && response.statusCode < 300) {
        final payload = decoded is Map<String, dynamic>
            ? decoded
            : {'value': decoded};

        await _persistDeviceData(payload);
        _statusMessage.value = 'Device connected successfully.';
      } else {
        if (decoded is Map<String, dynamic> && decoded['detail'] != null) {
          _statusMessage.value = decoded['detail'].toString();
        } else {
          _statusMessage.value =
              'Request failed with status ${response.statusCode}.';
        }
      }
    } catch (error) {
      _statusMessage.value = 'Network error: $error';
    } finally {
      if (mounted) {
        setState(() {
          _isSendingCode = false;
        });
      }
    }
  }

  Future<void> _sendReport() async {
    final currentDeviceId = _deviceId.value;
    if (currentDeviceId == null) {
      _statusMessage.value = 'No device ID is available to send a report.';
      return;
    }

    if (_threatClasses.value.isEmpty) {
      _statusMessage.value = 'No threat classes are saved for this device.';
      return;
    }

    final random = Random();
    final confidence = random.nextInt(99) + 1;
    final threatClass =
        _threatClasses.value[random.nextInt(_threatClasses.value.length)];
    final timestamp = DateTime.now().toUtc().toIso8601String();

    setState(() {
      _isSendingReport = true;
    });

    _statusMessage.value = 'Sending report...';

    try {
      final reportUrl = '$_baseApiUrl/api/devices/$currentDeviceId/report';
      final response = await http.post(
        Uri.parse(reportUrl),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'timestamp': timestamp,
          'confidence': confidence,
          'threat_class': threatClass,
        }),
      );

      if (!mounted) {
        return;
      }

      final decoded = response.body.isNotEmpty ? jsonDecode(response.body) : {};

      if (response.statusCode >= 200 && response.statusCode < 300) {
        _statusMessage.value = 'Report sent successfully.';
      } else {
        if (decoded is Map<String, dynamic> && decoded['detail'] != null) {
          _statusMessage.value = decoded['detail'].toString();
        } else {
          _statusMessage.value =
              'Report request failed with status ${response.statusCode}.';
        }
      }
    } catch (error) {
      _statusMessage.value = 'Report error: $error';
    } finally {
      if (mounted) {
        setState(() {
          _isSendingReport = false;
        });
      }
    }
  }

  Future<void> _runModelDemo() async {
    setState(() {
      _isRunningModel = true;
    });
    _statusMessage.value = 'Running ONNX inference on a zero-valued example...';

    try {
      final result = await runExampleAudioInference();
      _statusMessage.value =
          'Inference succeeded: class ${result.predictedClass}, '
          'score ${result.confidence.toStringAsFixed(4)} '
          '(${result.outputNames.length} model outputs: '
          '${result.outputNames.join(', ')}).';
    } catch (error) {
      _statusMessage.value = 'ONNX inference failed: $error';
    } finally {
      if (mounted) {
        setState(() {
          _isRunningModel = false;
        });
      }
    }
  }

  Future<void> _toggleNetworkMode() async {
    setState(() {
      _isHotspotMode = !_isHotspotMode;
    });

    await _persistNetworkMode();
    _statusMessage.value = _isHotspotMode
        ? 'Network mode: Hotspot'
        : 'Network mode: Wi‑Fi';
  }

  Future<void> _resetDeviceState() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_deviceIdStorageKey);
    await prefs.remove(_threatClassesStorageKey);

    if (!mounted) {
      return;
    }

    _deviceId.value = null;
    _threatClasses.value = const [];
    _codeController.clear();
    _statusMessage.value = 'Device state reset.';
  }

  @override
  void dispose() {
    _codeController.dispose();
    _statusMessage.dispose();
    _deviceId.dispose();
    _threatClasses.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final hasStoredDeviceId = _deviceId.value != null;

    return Scaffold(
      appBar: AppBar(title: const Text('Dryad')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
          child: SingleChildScrollView(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 480),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    ValueListenableBuilder<int?>(
                      valueListenable: _deviceId,
                      builder: (context, deviceId, _) {
                        if (deviceId == null) {
                          return const SizedBox.shrink();
                        }

                        return Card(
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Text(
                              'Stored device ID: $deviceId',
                              style: const TextStyle(
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: _isBusy ? null : _toggleNetworkMode,
                            child: Text(
                              _isHotspotMode ? 'Mode: Hotspot' : 'Mode: Wi‑Fi',
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: ElevatedButton(
                            onPressed: _isBusy ? null : _resetDeviceState,
                            child: const Text('Reset state'),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    const Text(
                      'Code',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _codeController,
                      decoration: const InputDecoration(
                        border: OutlineInputBorder(),
                        hintText: 'Enter your code',
                      ),
                      textCapitalization: TextCapitalization.characters,
                    ),
                    const SizedBox(height: 20),
                    ElevatedButton(
                      onPressed: _isBusy || _isSendingCode ? null : _sendCode,
                      child: _isSendingCode
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Send code'),
                    ),
                    const SizedBox(height: 20),
                    if (hasStoredDeviceId)
                      ElevatedButton(
                        onPressed: _isBusy || _isSendingReport
                            ? null
                            : _sendReport,
                        child: _isSendingReport
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                ),
                              )
                            : const Text('Send report'),
                      ),
                    const SizedBox(height: 20),
                    ValueListenableBuilder<String>(
                      valueListenable: _statusMessage,
                      builder: (context, statusText, _) {
                        if (statusText.isEmpty) {
                          return const SizedBox.shrink();
                        }
                        return Card(
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Text(statusText),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
