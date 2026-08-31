import 'package:flutter/material.dart';
import '../theme.dart';

class TopBar extends StatelessWidget {
  final String title;
  final DateTime? lastUpdated;
  const TopBar({super.key, required this.title, this.lastUpdated});

  String _formatAgo(DateTime time) {
    final diff = DateTime.now().difference(time);
    if (diff.inSeconds < 60) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    return '${diff.inHours}h ago';
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      child: Row(
        children: [
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
          const Spacer(),
          if (lastUpdated != null) ...[
            Text(
              'Updated ${_formatAgo(lastUpdated!)}',
              style: TextStyle(color: Colors.white.withOpacity(0.35), fontSize: 10),
            ),
            const SizedBox(width: 10),
          ],
          Container(width: 8, height: 8, decoration: const BoxDecoration(color: signalGreen, shape: BoxShape.circle)),
          const SizedBox(width: 6),
          const Text('LIVE', style: TextStyle(color: signalGreen, fontSize: 12, letterSpacing: 1.5)),
        ],
      ),
    );
  }
}