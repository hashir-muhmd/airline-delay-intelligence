import 'package:flutter/material.dart';
import '../widgets/top_bar.dart';
import '../widgets/delay_stats_card.dart';
import '../widgets/error_banner.dart';

class StatsTab extends StatelessWidget {
  final Map<String, dynamic>? delayStats;
  final String? error;
  final DateTime? lastUpdated;
  final Future<void> Function() onRefresh;

  const StatsTab({
    super.key,
    required this.delayStats,
    required this.error,
    required this.lastUpdated,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: onRefresh,
      color: const Color(0xFF00D9A3),
      backgroundColor: const Color(0xFF131A2A),
      child: ListView(
        children: [
          TopBar(title: 'Delay Stats', lastUpdated: lastUpdated),
          if (error != null) ErrorBanner(message: error!),
          if (delayStats != null)
            DelayStatsCard(stats: delayStats!)
          else if (error == null)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator(color: Color(0xFF00D9A3))),
            ),
        ],
      ),
    );
  }
}