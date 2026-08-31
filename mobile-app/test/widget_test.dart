// Basic smoke test: confirms the app builds without crashing and shows
// the splash screen's real content (not the default Flutter counter-app
// template this file originally tested against).
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:skypulse_mobile/main.dart';

void main() {
  testWidgets('App launches and shows splash screen', (WidgetTester tester) async {
    await tester.pumpWidget(const SkyPulseApp());

    // Splash screen should be visible immediately on launch.
    expect(find.text('SkyPulse'), findsOneWidget);
    expect(find.text('Live delay intelligence for DOH'), findsOneWidget);

    // Unmount the widget tree so SplashScreen's dispose() runs and cancels
    // its pending navigation timer, rather than leaking past test end.
    await tester.pumpWidget(const SizedBox.shrink());
  });
}