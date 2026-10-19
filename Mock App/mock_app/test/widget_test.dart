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

  testWidgets('shows code entry and hides report until device exists', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Code'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('Send code'), findsOneWidget);
    expect(find.text('Send report'), findsNothing);
    // expect(find.text('Run ONNX model demo'), findsOneWidget);
    expect(find.text('Connection'), findsOneWidget);
    expect(find.text('Listen'), findsOneWidget);
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
    expect(find.text('--'), findsWidgets);
    await tester.scrollUntilVisible(
      find.text('Squirrel'),
      300,
      scrollable: find.byType(Scrollable).last,
    );
    expect(find.text('Squirrel'), findsOneWidget);
  });

  testWidgets('shows stored device id and send report button when available', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues({
      'device_id': 10,
      'threat_classes': ['1', '3', '9'],
    });

    await tester.pumpWidget(const MyApp());
    await tester.pumpAndSettle();

    expect(find.textContaining('Stored device ID'), findsOneWidget);
    expect(find.text('Send report'), findsOneWidget);
  });
}
