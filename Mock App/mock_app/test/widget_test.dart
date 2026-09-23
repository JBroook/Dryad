// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:mock_app/main.dart';

void main() {
  testWidgets('shows code entry and hides report until device exists',
      (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Code'), findsOneWidget);
    expect(find.byType(TextField), findsOneWidget);
    expect(find.text('Send code'), findsOneWidget);
    expect(find.text('Send report'), findsNothing);
  });

  testWidgets('shows stored device id and send report button when available',
      (WidgetTester tester) async {
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
