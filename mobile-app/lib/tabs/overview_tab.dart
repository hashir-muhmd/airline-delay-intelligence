import 'package:flutter/material.dart';
import '../widgets/top_bar.dart';
import '../widgets/radar_hero.dart';
import '../widgets/delay_stats_card.dart';
import '../widgets/error_banner.dart';

class OverviewTab extends StatelessWidget {
  final List<dynamic>? flights;
  final Map<String, dynamic>? delayStats;
  final String? error;
  final DateTime? lastUpdated;
  final Future<void> Function() onRefresh;

  const OverviewTab({
    super.key,
    required this.flights,
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
          TopBar(title: 'SkyPulse', lastUpdated: lastUpdated),
          const RadarHero(),
          if (error != null) ErrorBanner(message: error!),
          if (delayStats != null) DelayStatsCard(stats: delayStats!),
          if (flights != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              child: Text(
                '${flights!.length} flights tracked at DOH',
                style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 12),
              ),
            ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}