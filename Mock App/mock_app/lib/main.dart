import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:battery_plus/battery_plus.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/material.dart';
import 'package:flutter_foreground_task/flutter_foreground_task.dart';
import 'package:http/http.dart' as http;
import 'package:mock_app/audio_model_runner.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'audio_classes.dart';
import 'audio_listening_screen.dart';

const String _wifiHost = '192.168.100.7';
const String _hotspotHost = '10.111.194.78';
const String _deviceIdStorageKey = 'device_id';
const String _threatClassesStorageKey = 'threat_classes';
const String _networkModeStorageKey = 'network_mode_hotspot';
const String _sentIncidentsStorageKey = 'sent_incidents';
const String _pendingReportsStorageKey = 'pending_reports';
const String _threatClassNamesStorageKey = 'threat_class_names';
const String _confidenceThresholdStorageKey = 'confidence_threshold';
const String _reportCooldownStorageKey = 'report_cooldown_seconds';
const String _lastReportAtStorageKey = 'last_report_at';
const String _lastReportDeliveredAtStorageKey = 'last_report_delivered_at';
const int _defaultConfidenceThreshold = 75;
const int _defaultReportCooldownSeconds = 5;

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
  final GlobalKey<_CodeRequestScreenState> _connectionScreenKey =
      GlobalKey<_CodeRequestScreenState>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedPage == 1 ? 1 : 0,
        children: [
          CodeRequestScreen(
            key: _connectionScreenKey,
            showSettings: _selectedPage == 2,
          ),
          AudioListeningScreen(
            onScores: (scores) =>
                _connectionScreenKey.currentState?._handleAudioScores(scores),
          ),
        ],
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
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}

class CodeRequestScreen extends StatefulWidget {
  const CodeRequestScreen({super.key, this.showSettings = false});

  final bool showSettings;

  @override
  State<CodeRequestScreen> createState() => _CodeRequestScreenState();
}

class _CodeRequestScreenState extends State<CodeRequestScreen>
    with WidgetsBindingObserver {
  final TextEditingController _codeController = TextEditingController();
  final ValueNotifier<String> _statusMessage = ValueNotifier('');
  final ValueNotifier<int?> _deviceId = ValueNotifier<int?>(null);
  final ValueNotifier<List<int>> _threatClasses = ValueNotifier<List<int>>([]);
  bool _isSendingCode = false;
  bool _isSendingReport = false;
  bool _isRunningModel = false;
  bool _isHotspotMode = false;
  List<Map<String, dynamic>> _sentIncidents = [];
  List<Map<String, dynamic>> _pendingReports = [];
  Map<int, String> _threatClassNames = {};
  int _confidenceThreshold = _defaultConfidenceThreshold;
  int _reportCooldownSeconds = _defaultReportCooldownSeconds;
  DateTime? _lastReportAt;
  DateTime? _lastReportDeliveredAt;
  final Connectivity _connectivity = Connectivity();
  StreamSubscription<List<ConnectivityResult>>? _connectivitySubscription;
  Timer? _queueRetryTimer;
  bool _isDrainingReportQueue = false;
  bool _pendingReportsRestored = false;
  Future<void> _pendingQueueWrite = Future<void>.value();

  bool get _isBusy => _isSendingCode || _isSendingReport || _isRunningModel;

  String get _apiHost => _isHotspotMode ? _hotspotHost : _wifiHost;

  String get _baseApiUrl => 'http://$_apiHost:8000';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _listenForConnectivityChanges();
    unawaited(_restoreStartupState());
  }

  void _listenForConnectivityChanges() {
    try {
      _connectivitySubscription = _connectivity.onConnectivityChanged.listen(
        (results) {
          if (results.any((result) => result != ConnectivityResult.none)) {
            unawaited(_drainReportQueue());
          } else {
            _scheduleQueueRetry();
          }
        },
        onError: (Object error) {
          if (mounted && _pendingReports.isNotEmpty) {
            _statusMessage.value = 'Could not monitor connectivity: $error';
          }
          _scheduleQueueRetry();
        },
      );
    } catch (error) {
      if (mounted) {
        _statusMessage.value = 'Could not monitor connectivity: $error';
      }
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(_checkConnectionAndDrainQueue());
    }
  }

  Future<void> _checkConnectionAndDrainQueue() async {
    if (_pendingReports.isEmpty) {
      return;
    }
    try {
      final results = await _connectivity.checkConnectivity();
      if (results.any((result) => result != ConnectivityResult.none)) {
        await _drainReportQueue();
      } else {
        _scheduleQueueRetry();
      }
    } catch (error) {
      if (mounted) {
        _statusMessage.value = 'Could not check connectivity: $error';
      }
      _scheduleQueueRetry();
    }
  }

  void _scheduleQueueRetry() {
    if (!mounted ||
        _pendingReports.isEmpty ||
        _queueRetryTimer?.isActive == true) {
      return;
    }
    _queueRetryTimer = Timer(
      const Duration(seconds: 30),
      () => unawaited(_drainReportQueue()),
    );
  }

  Future<void> _restoreStartupState() async {
    try {
      await _restoreNetworkMode();
      await Future.wait([
        _restoreSavedDeviceData(),
        _restoreIncidentHistory(),
        _restorePendingReports(),
      ]);
    } catch (error) {
      if (mounted) {
        _statusMessage.value = 'Could not restore saved app state: $error';
      }
      return;
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _pendingReportsRestored = true;
    });
    final deviceId = _deviceId.value;
    if (deviceId != null) {
      await _refreshDeviceConfiguration(deviceId);
    }
    await _checkConnectionAndDrainQueue();
  }

  Future<void> _restoreSavedDeviceData() async {
    final prefs = await SharedPreferences.getInstance();
    final savedDeviceId = prefs.getInt(_deviceIdStorageKey);
    final savedThreatClasses =
        prefs.getStringList(_threatClassesStorageKey) ?? const [];
    final savedThreatClassNames = prefs.getString(_threatClassNamesStorageKey);
    final savedConfidenceThreshold = prefs.getInt(
      _confidenceThresholdStorageKey,
    );
    final savedCooldownSeconds = prefs.getInt(_reportCooldownStorageKey);
    final savedLastReportAt = prefs.getInt(_lastReportAtStorageKey);
    final savedLastReportDeliveredAt = prefs.getInt(
      _lastReportDeliveredAtStorageKey,
    );
    final threatClassNames = <int, String>{};
    if (savedThreatClassNames != null) {
      final decoded = jsonDecode(savedThreatClassNames);
      if (decoded is Map<String, dynamic>) {
        for (final entry in decoded.entries) {
          final classId = int.tryParse(entry.key);
          if (classId != null && entry.value is String) {
            threatClassNames[classId] = entry.value as String;
          }
        }
      }
    }

    if (!mounted) {
      return;
    }

    _deviceId.value = savedDeviceId;
    _threatClasses.value = savedThreatClasses
        .map((entry) => int.tryParse(entry))
        .whereType<int>()
        .toList();
    _threatClassNames = threatClassNames;
    if (savedConfidenceThreshold != null &&
        savedConfidenceThreshold >= 0 &&
        savedConfidenceThreshold <= 100) {
      _confidenceThreshold = savedConfidenceThreshold;
    }
    if (savedCooldownSeconds != null &&
        savedCooldownSeconds >= 1 &&
        savedCooldownSeconds <= 60) {
      _reportCooldownSeconds = savedCooldownSeconds;
    }
    if (savedLastReportAt != null) {
      _lastReportAt = DateTime.fromMillisecondsSinceEpoch(savedLastReportAt);
    }
    if (savedLastReportDeliveredAt != null) {
      _lastReportDeliveredAt = DateTime.fromMillisecondsSinceEpoch(
        savedLastReportDeliveredAt,
      );
    }

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

  Future<void> _restoreIncidentHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final storedIncidents =
        prefs.getStringList(_sentIncidentsStorageKey) ?? const [];
    final incidents = <Map<String, dynamic>>[];

    for (final entry in storedIncidents) {
      final decoded = jsonDecode(entry);
      if (decoded is Map<String, dynamic>) {
        incidents.add(decoded);
      }
    }

    if (mounted) {
      setState(() {
        _sentIncidents = incidents;
      });
    }
  }

  Future<void> _restorePendingReports() async {
    final prefs = await SharedPreferences.getInstance();
    final storedReports =
        prefs.getStringList(_pendingReportsStorageKey) ?? const [];
    final reports = <Map<String, dynamic>>[];

    for (final entry in storedReports) {
      final decoded = jsonDecode(entry);
      if (decoded is Map<String, dynamic>) {
        reports.add(decoded);
      }
    }

    if (mounted) {
      setState(() {
        _pendingReports = reports;
      });
    }
  }

  Future<void> _updatePendingReports(
    List<Map<String, dynamic>> Function(List<Map<String, dynamic>> reports)
    update,
  ) {
    final completer = Completer<void>();
    _pendingQueueWrite = _pendingQueueWrite.then((_) async {
      try {
        final updatedReports = update(List.of(_pendingReports));
        await _persistPendingReports(updatedReports);
        if (mounted) {
          setState(() {
            _pendingReports = updatedReports;
          });
        }
        completer.complete();
      } catch (error, stackTrace) {
        completer.completeError(error, stackTrace);
      }
    });
    return completer.future;
  }

  Future<void> _persistPendingReports(
    List<Map<String, dynamic>> reports,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    final saved = await prefs.setStringList(
      _pendingReportsStorageKey,
      reports.map(jsonEncode).toList(),
    );
    if (!saved) {
      throw StateError('Shared preferences did not save the report queue.');
    }
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

    final rawThreatClassNames = payload['threat_class_names'];
    if (rawThreatClassNames is Map) {
      final parsedNames = <int, String>{};
      for (final entry in rawThreatClassNames.entries) {
        final classId = int.tryParse(entry.key.toString());
        if (classId != null && entry.value is String) {
          parsedNames[classId] = entry.value as String;
        }
      }
      _threatClassNames = parsedNames;
      await prefs.setString(
        _threatClassNamesStorageKey,
        jsonEncode({
          for (final entry in parsedNames.entries)
            entry.key.toString(): entry.value,
        }),
      );
    }

    final rawConfidenceThreshold = payload['confidence_threshold'];
    if (rawConfidenceThreshold is num &&
        rawConfidenceThreshold >= 0 &&
        rawConfidenceThreshold <= 100) {
      _confidenceThreshold = rawConfidenceThreshold.round();
      await prefs.setInt(_confidenceThresholdStorageKey, _confidenceThreshold);
    }
  }

  Future<void> _refreshDeviceConfiguration(int deviceId) async {
    try {
      final response = await http.get(
        Uri.parse('$_baseApiUrl/api/devices/$deviceId/report'),
      );
      if (!mounted) {
        return;
      }

      final decoded = response.body.isNotEmpty ? jsonDecode(response.body) : {};
      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (decoded is Map<String, dynamic> &&
            decoded['threat_classes'] is List &&
            decoded['threat_class_names'] is Map &&
            decoded['confidence_threshold'] is num) {
          await _persistDeviceData(decoded);
          if (mounted) {
            setState(() {});
          }
        } else {
          _statusMessage.value =
              'The backend returned incomplete device detection settings.';
        }
      } else {
        _statusMessage.value =
            'Could not refresh device detection settings '
            '(status ${response.statusCode}).';
      }
    } catch (error) {
      if (mounted) {
        _statusMessage.value =
            'Could not refresh device detection settings: $error';
      }
    }
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
      final batteryLevel = await Battery().batteryLevel;
      final response = await http.post(
        Uri.parse('$_baseApiUrl/api/devices/connect'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'code': code,
          'battery': batteryLevel,
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
    if (_threatClasses.value.isEmpty) {
      _statusMessage.value = 'No threat classes are saved for this device.';
      return;
    }

    final random = Random();
    final confidence = random.nextInt(99) + 1;
    final threatClassId =
        _threatClasses.value[random.nextInt(_threatClasses.value.length)];

    await _submitIncident(
      threatClassId: threatClassId,
      confidence: confidence,
      threatName: _threatClassNames[threatClassId],
      isTest: true,
    );
  }

  void _handleAudioScores(List<double> scores) {
    if (_deviceId.value == null ||
        !_pendingReportsRestored ||
        _reportCooldownRemaining > Duration.zero ||
        scores.length != audioClassNames.length) {
      return;
    }

    final detection = selectThreatDetection(
      scores: scores,
      configuredThreatClassIds: _threatClasses.value,
      threatClassNames: _threatClassNames,
      confidenceThreshold: _confidenceThreshold,
    );
    if (detection != null) {
      unawaited(
        _submitIncident(
          threatClassId: detection.threatClassId,
          confidence: detection.confidence,
          threatName: detection.threatClassName,
          isTest: false,
        ),
      );
    }
  }

  Duration get _reportCooldownRemaining {
    final lastReportAt = _lastReportAt;
    if (lastReportAt == null) {
      return Duration.zero;
    }
    return lastReportAt
        .add(Duration(seconds: _reportCooldownSeconds))
        .difference(DateTime.now());
  }

  Duration get _deliveryCooldownRemaining {
    final lastReportDeliveredAt = _lastReportDeliveredAt;
    if (lastReportDeliveredAt == null) {
      return Duration.zero;
    }
    return lastReportDeliveredAt
        .add(Duration(seconds: _reportCooldownSeconds))
        .difference(DateTime.now());
  }

  Future<void> _submitIncident({
    required int threatClassId,
    required int confidence,
    required String? threatName,
    required bool isTest,
  }) async {
    final currentDeviceId = _deviceId.value;
    if (currentDeviceId == null) {
      _statusMessage.value = 'No device ID is available to send a report.';
      return;
    }
    if (!_pendingReportsRestored) {
      _statusMessage.value = 'Report queue is still loading. Please try again.';
      return;
    }

    final cooldownRemaining = _reportCooldownRemaining;
    if (cooldownRemaining > Duration.zero) {
      final secondsRemaining = (cooldownRemaining.inMilliseconds + 999) ~/ 1000;
      _statusMessage.value =
          'Report cooldown active. Try again in $secondsRemaining seconds.';
      return;
    }

    final reportedAt = DateTime.now();
    final displayName =
        threatName ??
        _threatClassNames[threatClassId] ??
        'Threat class $threatClassId';
    final report = <String, dynamic>{
      'report_id': reportedAt.microsecondsSinceEpoch.toString(),
      'device_id': currentDeviceId,
      'timestamp': reportedAt.toUtc().toIso8601String(),
      'confidence': confidence,
      'threat_class': threatClassId,
      'threat_name': displayName,
      'is_test': isTest,
    };
    setState(() {
      _lastReportAt = reportedAt;
    });
    _statusMessage.value = isTest
        ? 'Adding test incident to the send queue...'
        : 'Adding detected incident to the send queue...';

    try {
      await _updatePendingReports((reports) => [...reports, report]);
    } catch (error) {
      _statusMessage.value = 'Could not save report in send queue: $error';
      return;
    }

    String? cooldownSaveError;
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = await prefs.setInt(
        _lastReportAtStorageKey,
        reportedAt.millisecondsSinceEpoch,
      );
      if (!saved) {
        cooldownSaveError = 'The report cooldown could not be saved.';
      }
    } catch (error) {
      cooldownSaveError = 'The report cooldown could not be saved: $error';
    }

    await _drainReportQueue();
    if (cooldownSaveError != null && mounted) {
      _statusMessage.value = '${_statusMessage.value}\n$cooldownSaveError';
    }
  }

  Future<void> _drainReportQueue() async {
    if (!mounted ||
        !_pendingReportsRestored ||
        _isDrainingReportQueue ||
        _pendingReports.isEmpty) {
      return;
    }

    setState(() {
      _isDrainingReportQueue = true;
      _isSendingReport = true;
    });
    _queueRetryTimer?.cancel();
    _queueRetryTimer = null;
    var deliveryFailed = false;
    try {
      while (mounted && _pendingReports.isNotEmpty) {
        final deliveryCooldown = _deliveryCooldownRemaining;
        if (deliveryCooldown > Duration.zero) {
          await Future<void>.delayed(deliveryCooldown);
          if (!mounted) {
            return;
          }
        }
        final queuedReport = _pendingReports.first;
        var backendAccepted = false;
        try {
          final report = await _sendQueuedReport(queuedReport);
          backendAccepted = true;
          final deliveryStateError = await _markReportDelivered();
          final reportId = report['report_id'];
          await _updatePendingReports(
            (reports) =>
                reports.where((item) => item['report_id'] != reportId).toList(),
          );
          final historyError = await _recordSentIncident(report);
          final isTest = report['is_test'] == true;
          final threatName = report['threat_name'] as String;
          final confidence = report['confidence'];
          final successMessage = isTest
              ? 'Test incident sent successfully.'
              : '$threatName detected at $confidence%. Incident sent successfully.';
          final errors = <String>[];
          if (historyError != null) {
            errors.add('History could not be saved: $historyError');
          }
          if (deliveryStateError != null) {
            errors.add(deliveryStateError);
          }
          _statusMessage.value = errors.isEmpty
              ? successMessage
              : '$successMessage ${errors.join(' ')}';
          if (!mounted) {
            return;
          }
        } catch (error) {
          deliveryFailed = true;
          _scheduleQueueRetry();
          _statusMessage.value = backendAccepted
              ? 'Report was accepted, but queue cleanup failed; it may be retried: $error'
              : 'Report remains queued and will retry when connection is available: $error';
          break;
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isDrainingReportQueue = false;
          _isSendingReport = false;
        });
      }
    }

    if (!deliveryFailed && mounted && _pendingReports.isNotEmpty) {
      unawaited(_drainReportQueue());
    } else if (_pendingReports.isEmpty) {
      _queueRetryTimer?.cancel();
      _queueRetryTimer = null;
    }
  }

  Future<String?> _markReportDelivered() async {
    final deliveredAt = DateTime.now();
    if (mounted) {
      setState(() {
        _lastReportAt = deliveredAt;
        _lastReportDeliveredAt = deliveredAt;
      });
    }

    try {
      final prefs = await SharedPreferences.getInstance();
      final lastReportSaved = await prefs.setInt(
        _lastReportAtStorageKey,
        deliveredAt.millisecondsSinceEpoch,
      );
      final deliverySaved = await prefs.setInt(
        _lastReportDeliveredAtStorageKey,
        deliveredAt.millisecondsSinceEpoch,
      );
      if (!lastReportSaved || !deliverySaved) {
        return 'The report cooldown could not be saved.';
      }
      return null;
    } catch (error) {
      return 'The report cooldown could not be saved: $error';
    }
  }

  Future<Map<String, dynamic>> _sendQueuedReport(
    Map<String, dynamic> queuedReport,
  ) async {
    final report = Map<String, dynamic>.from(queuedReport);
    if (report['battery'] is! num) {
      final batteryLevel = await Battery().batteryLevel;
      report['battery'] = batteryLevel;
      final reportId = report['report_id'];
      await _updatePendingReports(
        (reports) => reports
            .map((item) => item['report_id'] == reportId ? report : item)
            .toList(),
      );
    }

    final deviceId = report['device_id'] as int;
    final response = await http
        .post(
          Uri.parse('$_baseApiUrl/api/devices/$deviceId/report'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'timestamp': report['timestamp'],
            'confidence': report['confidence'],
            'threat_class': report['threat_class'],
            'battery': report['battery'],
          }),
        )
        .timeout(const Duration(seconds: 15));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = response.body.isEmpty ? '' : ': ${response.body}';
      throw StateError(
        'Report request failed with status ${response.statusCode}$detail',
      );
    }
    return report;
  }

  Future<String?> _recordSentIncident(Map<String, dynamic> report) async {
    final incident = <String, dynamic>{
      'timestamp': report['timestamp'],
      'confidence': report['confidence'],
      'threat_class': report['threat_class'],
      'threat_name': report['threat_name'],
      'battery': report['battery'],
    };
    final updatedIncidents = [incident, ..._sentIncidents];
    if (mounted) {
      setState(() {
        _sentIncidents = updatedIncidents;
      });
    }

    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = await prefs.setStringList(
        _sentIncidentsStorageKey,
        updatedIncidents.map(jsonEncode).toList(),
      );
      if (!saved) {
        throw StateError('Shared preferences did not save incident history.');
      }
      return null;
    } catch (error) {
      return error.toString();
    }
  }

  Future<void> _setReportCooldown(int seconds) async {
    setState(() {
      _reportCooldownSeconds = seconds;
    });
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = await prefs.setInt(_reportCooldownStorageKey, seconds);
      if (!saved) {
        throw StateError('Shared preferences did not save the cooldown.');
      }
    } catch (error) {
      _statusMessage.value = 'Could not save report cooldown: $error';
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
    unawaited(_checkConnectionAndDrainQueue());
  }

  Future<void> _resetDeviceState() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_deviceIdStorageKey);
    await prefs.remove(_threatClassesStorageKey);
    await prefs.remove(_threatClassNamesStorageKey);
    await prefs.remove(_confidenceThresholdStorageKey);
    await prefs.remove(_lastReportAtStorageKey);
    await prefs.remove(_lastReportDeliveredAtStorageKey);

    if (!mounted) {
      return;
    }

    _deviceId.value = null;
    _threatClasses.value = const [];
    _threatClassNames = {};
    _confidenceThreshold = _defaultConfidenceThreshold;
    _lastReportAt = null;
    _lastReportDeliveredAt = null;
    _codeController.clear();
    _statusMessage.value = 'Device state reset.';
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _queueRetryTimer?.cancel();
    final connectivitySubscription = _connectivitySubscription;
    if (connectivitySubscription != null) {
      unawaited(connectivitySubscription.cancel());
    }
    _codeController.dispose();
    _statusMessage.dispose();
    _deviceId.dispose();
    _threatClasses.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
                  children: widget.showSettings
                      ? _buildSettingsContent()
                      : _buildConnectionContent(),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  List<Widget> _buildConnectionContent() {
    return [
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
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ),
          );
        },
      ),
      const SizedBox(height: 20),
      const Text(
        'Code',
        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
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
      _buildStatusMessage(),
    ];
  }

  List<Widget> _buildSettingsContent() {
    return [
      Row(
        children: [
          Expanded(
            child: ElevatedButton(
              onPressed: _isBusy ? null : _toggleNetworkMode,
              child: Text(_isHotspotMode ? 'Mode: Hotspot' : 'Mode: Wi‑Fi'),
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
      Text(
        'Detection confidence threshold: $_confidenceThreshold%',
        style: Theme.of(context).textTheme.titleSmall,
      ),
      const SizedBox(height: 16),
      Text(
        'Report cooldown: $_reportCooldownSeconds seconds',
        style: Theme.of(context).textTheme.titleSmall,
      ),
      Slider(
        min: 1,
        max: 60,
        divisions: 59,
        value: _reportCooldownSeconds.toDouble(),
        label: '$_reportCooldownSeconds seconds',
        onChanged: (value) {
          setState(() {
            _reportCooldownSeconds = value.round();
          });
        },
        onChangeEnd: (value) => unawaited(_setReportCooldown(value.round())),
      ),
      const SizedBox(height: 8),
      ValueListenableBuilder<int?>(
        valueListenable: _deviceId,
        builder: (context, deviceId, _) {
          if (deviceId == null) {
            return const SizedBox.shrink();
          }

          return ElevatedButton(
            onPressed: _isBusy || !_pendingReportsRestored ? null : _sendReport,
            child: _isSendingReport
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Text('Test Incident'),
          );
        },
      ),
      if (_pendingReports.isNotEmpty) ...[
        const SizedBox(height: 12),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              '${_pendingReports.length} report(s) queued and waiting to send.',
            ),
          ),
        ),
      ],
      const SizedBox(height: 16),
      _buildStatusMessage(),
      const SizedBox(height: 12),
      Text('Sent incidents', style: Theme.of(context).textTheme.titleMedium),
      const SizedBox(height: 8),
      if (_sentIncidents.isEmpty)
        const Card(
          child: Padding(
            padding: EdgeInsets.all(12),
            child: Text('No incidents sent yet.'),
          ),
        )
      else
        ..._sentIncidents.map((incident) {
          final timestamp = DateTime.parse(incident['timestamp'] as String)
              .toLocal();
          final threatName =
              incident['threat_name'] ??
              _threatClassNames[incident['threat_class']] ??
              'Threat class ${incident['threat_class']}';
          final confidence = incident['confidence'];
          final battery = incident['battery'];

          return Card(
            child: ListTile(
              leading: const Icon(Icons.warning_amber_outlined),
              title: Text(threatName.toString()),
              subtitle: Text('${timestamp.toString()} · Battery $battery%'),
              trailing: Text('$confidence%'),
            ),
          );
        }),
    ];
  }

  Widget _buildStatusMessage() {
    return ValueListenableBuilder<String>(
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
    );
  }
}
