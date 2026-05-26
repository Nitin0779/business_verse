import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // Configured default local API port
  static const String baseUrl = 'http://localhost:8000';

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<void> saveToken(String token, String username, String role) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
    await prefs.setString('username', username);
    await prefs.setString('role', role);
  }

  static Future<void> clearAuth() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('username');
    await prefs.remove('role');
  }

  static Future<Map<String, String>> get _headers async {
    final token = await getToken();
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // HTTP GET Request Helper
  static Future<http.Response> get(String endpoint) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final headers = await _headers;
    return await http.get(url, headers: headers);
  }

  // HTTP POST Request Helper
  static Future<http.Response> post(String endpoint, Map<String, dynamic> body) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final headers = await _headers;
    return await http.post(url, headers: headers, body: jsonEncode(body));
  }

  // HTTP Multipart POST Request Helper (used for CSV/Excel File Uploads)
  static Future<http.Response> uploadFile(String endpoint, Uint8List fileBytes, String fileName) async {
    final url = Uri.parse('$baseUrl$endpoint');
    final token = await getToken();
    
    final request = http.MultipartRequest('POST', url);
    if (token != null) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    
    final multipartFile = http.MultipartFile.fromBytes(
      'file',
      fileBytes,
      filename: fileName,
    );
    request.files.add(multipartFile);
    
    final streamedResponse = await request.send();
    return await http.Response.fromStream(streamedResponse);
  }
}
