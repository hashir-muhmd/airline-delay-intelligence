import 'package:flutter/material.dart';
import 'radar_painter.dart';

class RadarHero extends StatefulWidget {
  final double size;
  final bool showPings;
  const RadarHero({super.key, this.size = 200, this.showPings = true});

  @override
  State<RadarHero> createState() => _RadarHeroState();
}

class _RadarHeroState extends State<RadarHero> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(vsync: this, duration: const Duration(seconds: 4))..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: widget.size + 20,
      child: Center(
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) => CustomPaint(
            size: Size(widget.size, widget.size),
            painter: RadarPainter(sweepAngle: _controller.value * 2 * 3.14159, showPings: widget.showPings),
          ),
        ),
      ),
    );
  }
}