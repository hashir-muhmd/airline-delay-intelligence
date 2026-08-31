import 'package:flutter/material.dart';
import '../theme.dart';

class DelayStatsCard extends StatelessWidget {
  final Map<String, dynamic> stats;
  const DelayStatsCard({super.key, required this.stats});

  @override
  Widget build(BuildContext context) {
    final hasData = stats['median_minutes'] != null;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: navyCard,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
      ),
      child: hasData
          ? Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _statColumn('MEDIAN', '${stats['median_minutes']}m'),
                _statColumn('MEAN', '${stats['mean_minutes']}m'),
                _statColumn('SAMPLE', '${stats['count']}'),
              ],
            )
          : Text(stats['message'] ?? 'Not enough delay data yet.',
              style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 13)),
    );
  }

  Widget _statColumn(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, letterSpacing: 1)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(color: signalGreen, fontSize: 18, fontWeight: FontWeight.bold)),
      ],
    );
  }
}