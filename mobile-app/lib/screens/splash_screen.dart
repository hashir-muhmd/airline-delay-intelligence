import 'dart:async';
import 'package:flutter/material.dart';
import '../theme.dart';
import '../widgets/radar_hero.dart';
import 'main_tab_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  late final AnimationController _fadeController;
  Timer? _navigateTimer;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(vsync: this, duration: const Duration(milliseconds: 600))..forward();

    _navigateTimer = Timer(const Duration(milliseconds: 1600), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => const MainTabScreen()),
        );
      }
    });
  }

  @override
  void dispose() {
    _navigateTimer?.cancel();
    _fadeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: navyBg,
      body: FadeTransition(
        opacity: _fadeController,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const RadarHero(size: 90, showPings: false),
              const SizedBox(height: 20),
              const Text('SkyPulse',
                  style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.bold, letterSpacing: 1)),
              const SizedBox(height: 8),
              Text('Live delay intelligence for DOH',
                  style: TextStyle(color: Colors.white.withOpacity(0.5), fontSize: 13)),
            ],
          ),
        ),
      ),
    );
  }
}