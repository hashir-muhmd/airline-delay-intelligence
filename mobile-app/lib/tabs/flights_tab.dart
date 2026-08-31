import 'package:flutter/material.dart';
import '../widgets/top_bar.dart';
import '../widgets/flight_tile.dart';
import '../widgets/error_banner.dart';

class FlightsTab extends StatelessWidget {
  final List<dynamic>? flights;
  final String? error;
  final DateTime? lastUpdated;
  final Future<void> Function() onRefresh;

  const FlightsTab({
    super.key,
    required this.flights,
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
          TopBar(title: 'Live Flights', lastUpdated: lastUpdated),
          if (error != null) ErrorBanner(message: error!),
          if (flights != null)
            ...flights!.map((f) => FlightTile(flight: f))
          else if (error == null)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator(color: Color(0xFF00D9A3))),
            ),
          const SizedBox(height: 24),
        ],
      ),
    );
  }
}