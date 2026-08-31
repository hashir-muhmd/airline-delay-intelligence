import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../theme.dart';

class RadarPainter extends CustomPainter {
  final double sweepAngle;
  final bool showPings;
  RadarPainter({required this.sweepAngle, required this.showPings});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final maxRadius = size.width / 2;

    final ringPaint = Paint()
      ..color = signalGreen.withOpacity(0.25)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;
    for (final fraction in [0.35, 0.6, 0.85, 1.0]) {
      canvas.drawCircle(center, maxRadius * fraction, ringPaint);
    }

    final crosshairPaint = Paint()
      ..color = signalGreen.withOpacity(0.2)
      ..strokeWidth = 1;
    canvas.drawLine(Offset(center.dx - maxRadius, center.dy),
        Offset(center.dx + maxRadius, center.dy), crosshairPaint);
    canvas.drawLine(Offset(center.dx, center.dy - maxRadius),
        Offset(center.dx, center.dy + maxRadius), crosshairPaint);

    final sweepPaint = Paint()
      ..shader = SweepGradient(
        startAngle: sweepAngle,
        endAngle: sweepAngle + math.pi / 2.5,
        colors: [signalGreen.withOpacity(0.35), signalGreen.withOpacity(0.0)],
      ).createShader(Rect.fromCircle(center: center, radius: maxRadius));
    canvas.drawCircle(center, maxRadius, sweepPaint);

    if (showPings) {
      _drawPing(canvas, center, maxRadius * 0.5, 0.9);
      _drawPing(canvas, center, maxRadius * 0.75, 2.4);
    }

    final hubPaint = Paint()..color = navyBg;
    final hubBorder = Paint()
      ..color = signalGreen
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(center, 26, hubPaint);
    canvas.drawCircle(center, 26, hubBorder);

    final textPainter = TextPainter(
      text: const TextSpan(
        text: 'DOH',
        style: TextStyle(color: signalGreen, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(canvas, center - Offset(textPainter.width / 2, textPainter.height / 2));
  }

  void _drawPing(Canvas canvas, Offset center, double radius, double angle) {
    final dot = center + Offset(radius * math.cos(angle), radius * math.sin(angle));
    canvas.drawCircle(dot, 4, Paint()..color = amber);
  }

  @override
  bool shouldRepaint(covariant RadarPainter oldDelegate) => oldDelegate.sweepAngle != sweepAngle;
}