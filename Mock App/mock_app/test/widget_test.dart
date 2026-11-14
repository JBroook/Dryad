// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:mock_app/audio_classes.dart';
import 'package:mock_app/main.dart';

void main() {
  test('model labels cover all 27 output classes', () {
    expect(audioClassNames, hasLength(27));
  });

  test('selects the highest configured threat above threshold except Axe', () {
    final scores = List<double>.filled(audioClassNames.length, 0);
    scores[audioClassNames.indexOf('Axe')] = 0.99;
    scores[audioClassNames.indexOf('Chainsaw')] = 0.75;
    final threatClassNames = {1: 'Chainsaw', 2: 'Gun Shot'};

    expect(
      selectThreatDetection(
        scores: scores,
        configuredThreatClassIds: [1, 2],
        threatClassNames: threatClassNames,
        confidenceThreshold: 75,
      ),
      isNull,
    );

    scores[audioClassNames.indexOf('Chainsaw')] = 0.76;
    scores[audioClassNames.indexOf('Gunshot')] = 0.90;
    final detection = selectThreatDetection(
      scores: scores,
      configuredThreatClassIds: [1, 2],
      threatClassNames: threatClassNames,
      confidenceThreshold: 75,
    );

    expect(detection?.threatClassId, 2);
    expect(detection?.threatClassName, 'Gun Shot');
    expect(detection?.confidence, 90);
  });

  testWidgets('shows code entry and hides report until device exists', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Code'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('Send code'), findsOneWidget);
    expect(find.text('Test Incident'), findsNothing);
    expect(find.text('Reset state'), findsNothing);
    expect(find.text('Mode: Wi‑Fi'), findsNothing);
    expect(find.text('Connection'), findsOneWidget);
    expect(find.text('Listen'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
  });

  testWidgets('shows listening controls and all model classes', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());
    await tester.tap(find.text('Listen'));
    await tester.pumpAndSettle();

    expect(find.text('Start Listening'), findsOneWidget);
    expect(find.text('Class confidence'), findsOneWidget);
    expect(find.text('Microphone volume'), findsOneWidget);
    expect(find.text('-- dBFS'), findsOneWidget);
    expect(find.text('Dryad'), findsOneWidget);
    expect(find.text('Fire'), findsOneWidget);
    expect(find.text('Axe'), findsNothing);
    expect(find.text('--'), findsWidgets);
    await tester.scrollUntilVisible(
      find.text('Squirrel'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Squirrel'), findsOneWidget);
  });

  testWidgets('shows report controls and sent incident history in settings', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({
      'device_id': 10,
      'threat_classes': ['1', '3', '9'],
      'sent_incidents': [
        '{"timestamp":"2026-01-01T00:00:00.000Z","confidence":95,'
            '"threat_class":3,"battery":64}',
      ],
    });

    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    expect(find.textContaining('Stored device ID'), findsOneWidget);
    expect(find.text('Test Incident'), findsNothing);

    await tester.tap(find.text('Settings'));
    await tester.pumpAndSettle();

    expect(find.text('Mode: Wi‑Fi'), findsOneWidget);
    expect(find.text('Reset state'), findsOneWidget);
    expect(find.text('Report cooldown: 5 seconds'), findsOneWidget);
    expect(find.text('Test Incident'), findsOneWidget);
    expect(find.text('Send report'), findsNothing);
    expect(find.text('Sent incidents'), findsOneWidget);
    expect(find.text('Threat class 3'), findsOneWidget);
    expect(find.textContaining('Battery 64%'), findsOneWidget);
  });

  testWidgets('restores queued reports and shows the pending count', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({
      'pending_reports': [
        '{"report_id":"pending-1","device_id":10,'
            '"timestamp":"2026-01-01T00:00:00.000Z","confidence":90,'
            '"threat_class":1,"threat_name":"Chainsaw","is_test":false,'
            '"battery":80}',
      ],
    });

    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();
    await tester.tap(find.text('Settings'));
    await tester.pumpAndSettle();

    expect(
      find.text('1 report(s) queued and waiting to send.'),
      findsOneWidget,
    );
  });
}
