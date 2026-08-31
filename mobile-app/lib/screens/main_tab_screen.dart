import 'dart:async';
import 'package:flutter/material.dart';
import '../theme.dart';
import '../api.dart';
import '../tabs/overview_tab.dart';
import '../tabs/flights_tab.dart';
import '../tabs/stats_tab.dart';

// Auto-refresh interval. Kept well above the ingestion scheduler's own
// polling cadence (daily) -- this doesn't cause extra backend load beyond
// a cheap read query, since the backend just re-reads whatever's currently
// in Postgres rather than hitting AviationStack itself.
const Duration _refreshInterval = Duration(seconds: 60);

class MainTabScreen extends StatefulWidget {
  const MainTabScreen({super.key});

  @override
  State<MainTabScreen> createState() => _MainTabScreenState();
}

class _MainTabScreenState extends State<MainTabScreen> {
  int _tabIndex = 0;
  List<dynamic>? flights;
  Map<String, dynamic>? delayStats;
  String? error;
  DateTime? lastUpdated;
  Timer? _autoRefreshTimer;

  @override
  void initState() {
    super.initState();
    _loadData();
    _autoRefreshTimer = Timer.periodic(_refreshInterval, (_) => _loadData());
  }

  @override
  void dispose() {
    _autoRefreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _loadData() async {
    try {
      final newFlights = await fetchFlights(limit: 30);
      final newStats = await fetchDelayStats();
      if (!mounted) return;
      setState(() {
        flights = newFlights;
        delayStats = newStats;
        error = null;
        lastUpdated = DateTime.now();
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => error = "Couldn't reach the API — is the backend running?");
    }
  }

  @override
  Widget build(BuildContext context) {
    final tabs = [
      OverviewTab(flights: flights, delayStats: delayStats, error: error, lastUpdated: lastUpdated, onRefresh: _loadData),
      FlightsTab(flights: flights, error: error, lastUpdated: lastUpdated, onRefresh: _loadData),
      StatsTab(delayStats: delayStats, error: error, lastUpdated: lastUpdated, onRefresh: _loadData),
    ];

    return Scaffold(
      body: SafeArea(child: tabs[_tabIndex]),
      bottomNavigationBar: NavigationBar(
        backgroundColor: navyCard,
        indicatorColor: signalGreen.withOpacity(0.15),
        selectedIndex: _tabIndex,
        onDestinationSelected: (i) => setState(() => _tabIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.track_changes_outlined), selectedIcon: Icon(Icons.track_changes, color: signalGreen), label: 'Overview'),
          NavigationDestination(icon: Icon(Icons.flight_outlined), selectedIcon: Icon(Icons.flight, color: signalGreen), label: 'Flights'),
          NavigationDestination(icon: Icon(Icons.bar_chart_outlined), selectedIcon: Icon(Icons.bar_chart, color: signalGreen), label: 'Stats'),
        ],
      ),
    );
  }
}