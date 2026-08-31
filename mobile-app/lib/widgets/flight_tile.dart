import 'package:flutter/material.dart';
import '../theme.dart';

class FlightTile extends StatelessWidget {
  final dynamic flight;
  const FlightTile({super.key, required this.flight});

  Color _statusColor(String status, dynamic delay) {
    if (status == 'cancelled') return Colors.redAccent;
    if (delay != null && delay is num) {
      if (delay > 60) return Colors.redAccent;
      if (delay > 15) return amber;
    }
    return signalGreen;
  }

  @override
  Widget build(BuildContext context) {
    final origin = flight['origin'] ?? '—';
    final destination = flight['destination'] ?? '—';
    final flightNumbers = flight['flight_numbers'] ?? '—';
    final airline = flight['airline_primary'] ?? '';
    final status = flight['status'] ?? 'unknown';
    final delay = flight['delay_minutes'];

    final color = _statusColor(status, delay);
    final label = delay != null ? '+${delay}m' : status;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(color: navyCard, borderRadius: BorderRadius.circular(10)),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('$origin → $destination',
                    style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w600)),
                const SizedBox(height: 2),
                Text('$flightNumbers · $airline',
                    style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 11)),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(color: color.withOpacity(0.15), borderRadius: BorderRadius.circular(6)),
            child: Text(label, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600)),
          ),
        ],
      ),
    );
  }
}