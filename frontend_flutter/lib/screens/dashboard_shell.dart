import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import 'home_screen.dart';
import 'data_upload_screen.dart';
import 'data_cleaning_screen.dart';
import 'ml_predictions_screen.dart';
import 'sql_database_screen.dart';
import 'reports_screen.dart';

class DashboardShell extends StatefulWidget {
  const DashboardShell({super.key});

  @override
  State<DashboardShell> createState() => _DashboardShellState();
}

class _DashboardShellState extends State<DashboardShell> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const HomeScreen(),
    const DataUploadScreen(),
    const DataCleaningScreen(),
    const MLPredictionsScreen(),
    const SQLDatabaseScreen(),
    const ReportsScreen(),
  ];

  final List<Map<String, dynamic>> _navItems = [
    {'title': 'Dashboard Home', 'icon': Icons.space_dashboard_rounded},
    {'title': 'Data Upload', 'icon': Icons.cloud_upload_rounded},
    {'title': 'Data Cleaning', 'icon': Icons.cleaning_services_rounded},
    {'title': 'ML Predictions', 'icon': Icons.psychology_rounded},
    {'title': 'SQL Database', 'icon': Icons.storage_rounded},
    {'title': 'Reports & Exports', 'icon': Icons.description_rounded},
  ];

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final isDesktop = MediaQuery.of(context).size.width >= 1024;
    
    final sidebarContent = Container(
      width: 260,
      color: const Color(0xFF0F172A), // Premium Dark Slate
      child: Column(
        children: [
          // Sidebar Header Brand
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: Row(
              children: [
                const Icon(
                  Icons.bar_chart_rounded,
                  color: Color(0xFF3B82F6),
                  size: 32,
                ),
                const SizedBox(width: 12),
                const Text(
                  'BusinessVerse',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    letterSpacing: -0.5,
                  ),
                ),
              ],
            ),
          ),
          
          // Navigation Items
          Expanded(
            child: ListView.builder(
              itemCount: _navItems.length,
              itemBuilder: (context, index) {
                final item = _navItems[index];
                final isSelected = _selectedIndex == index;
                
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: ListTile(
                    dense: true,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                    tileColor: isSelected ? const Color(0xFF1E293B) : Colors.transparent,
                    leading: Icon(
                      item['icon'],
                      color: isSelected ? const Color(0xFF3B82F6) : const Color(0xFF94A3B8),
                      size: 20,
                    ),
                    title: Text(
                      item['title'],
                      style: TextStyle(
                        color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        fontSize: 13.5,
                      ),
                    ),
                    onTap: () {
                      setState(() {
                        _selectedIndex = index;
                      });
                      if (!isDesktop) {
                        Navigator.pop(context); // Close drawer on mobile
                      }
                    },
                  ),
                );
              },
            ),
          ),
          
          // User profile card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              border: Border(
                top: BorderSide(color: Color(0xFF1E293B)),
              ),
            ),
            child: Column(
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: const Color(0xFF3B82F6).withOpacity(0.1),
                      radius: 18,
                      child: Text(
                        state.username.isNotEmpty ? state.username[0].toUpperCase() : 'U',
                        style: const TextStyle(
                          color: Color(0xFF3B82F6),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            state.username,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.bold,
                              fontSize: 13,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          Text(
                            state.role,
                            style: const TextStyle(
                              color: Color(0xFF64748B),
                              fontSize: 11,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 36,
                  child: OutlinedButton.icon(
                    style: OutlinedButton.styleFrom(
                      foregroundColor: const Color(0xFFEF4444),
                      side: const BorderSide(color: Color(0xFFEF4444), width: 1),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    icon: const Icon(Icons.logout_rounded, size: 16),
                    label: const Text('Log Out', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                    onPressed: () => state.logout(),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );

    return Scaffold(
      appBar: isDesktop
          ? null
          : AppBar(
              backgroundColor: Colors.white,
              elevation: 0,
              iconTheme: const IconThemeData(color: Color(0xFF0F172A)),
              title: Row(
                children: [
                  const Icon(
                    Icons.bar_chart_rounded,
                    color: Color(0xFF2563EB),
                    size: 24,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _navItems[_selectedIndex]['title'],
                    style: const TextStyle(
                      color: Color(0xFF0F172A),
                      fontWeight: FontWeight.bold,
                      fontSize: 18,
                    ),
                  ),
                ],
              ),
              bottom: const PreferredSize(
                preferredSize: Size.fromHeight(1),
                child: Divider(color: Color(0xFFE2E8F0), height: 1),
              ),
            ),
      drawer: isDesktop ? null : Drawer(child: sidebarContent),
      body: Row(
        children: [
          if (isDesktop) sidebarContent,
          Expanded(
            child: SafeArea(
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 200),
                child: _screens[_selectedIndex],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
