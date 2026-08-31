import 'dart:convert';
import 'package:http/http.dart' as http;

// Android emulators can't reach the host machine's localhost directly --
// 10.0.2.2 is the special alias the Android emulator provides for that.
// If testing on a physical phone instead, replace with your machine's
// real LAN IP (e.g. 192.168.x.x) and ensure the phone is on the same
// network. Mirrors the role of VITE_API_BASE in the web dashboard's api.js.
const String apiBase = 'http://10.0.2.2:8000';

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => message;
}

Future<List<dynamic>> fetchFlights({int limit = 30}) async {
  final res = await http
      .get(Uri.parse('$apiBase/flights/physical?limit=$limit'))
      .timeout(const Duration(seconds: 10));
  if (res.statusCode != 200) {
    throw ApiException('Backend returned status ${res.statusCode}');
  }
  return jsonDecode(res.body) as List<dynamic>;
}

Future<Map<String, dynamic>> fetchDelayStats() async {
  final res = await http
      .get(Uri.parse('$apiBase/stats/delays'))
      .timeout(const Duration(seconds: 10));
  if (res.statusCode != 200) {
    throw ApiException('Backend returned status ${res.statusCode}');
  }
  return jsonDecode(res.body) as Map<String, dynamic>;
}