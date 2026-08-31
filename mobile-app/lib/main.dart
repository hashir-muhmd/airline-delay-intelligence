import 'package:flutter/material.dart';
import 'theme.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const SkyPulseApp());
}

class SkyPulseApp extends StatelessWidget {
  const SkyPulseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SkyPulse',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        scaffoldBackgroundColor: navyBg,
        colorScheme: const ColorScheme.dark(primary: signalGreen, surface: navyCard),
        cardColor: navyCard,
        fontFamily: 'monospace',
      ),
      home: const SplashScreen(),
    );
  }
}