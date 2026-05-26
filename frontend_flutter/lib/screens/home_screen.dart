import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:syncfusion_flutter_charts/charts.dart';
import '../providers/app_state.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final state = context.read<AppState>();
      if (state.isDBConnected) {
        state.fetchDBDashboardKPIs();
      }
    });
  }

  Widget _buildKPICard({
    required String label,
    required String value,
    required IconData icon,
    required Color iconColor,
    required Color bgColor,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: bgColor,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: iconColor, size: 24),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF64748B),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final isDesktop = MediaQuery.of(context).size.width >= 1024;
    
    // ─── If DB not connected, show welcome seed state ─────────────────────────
    if (!state.isDBConnected) {
      return Scaffold(
        backgroundColor: const Color(0xFFF8FAFC),
        body: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(40),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 64),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 540),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(24),
                          decoration: BoxDecoration(
                            color: const Color(0xFFEFF6FF),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.bar_chart_rounded,
                            color: Color(0xFF2563EB),
                            size: 64,
                          ),
                        ),
                        const SizedBox(height: 32),
                        const Text(
                          'Welcome to BusinessVerse',
                          style: TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.w800,
                            color: Color(0xFF0F172A),
                            letterSpacing: -0.5,
                          ),
                          textAlign: Center,
                        ),
                        const SizedBox(height: 12),
                        const Text(
                          'A professional business analytics platform. Connect your database to visualize live metrics, or proceed to upload raw CSV/Excel datasets.',
                          style: TextStyle(
                            fontSize: 14,
                            color: Color(0xFF64748B),
                            height: 1.5,
                          ),
                          textAlign: Center,
                        ),
                        const SizedBox(height: 36),
                        
                        // Seed Actions
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF2563EB),
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                elevation: 0,
                              ),
                              icon: const Icon(Icons.flash_on_rounded, size: 18),
                              label: const Text('Connect to Local DB', style: TextStyle(fontWeight: FontWeight.bold)),
                              onPressed: () async {
                                final success = await state.testDatabaseConnection();
                                if (success && context.mounted) {
                                  // Seed mock data if database is empty
                                  await state.seedMockDBData();
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(content: Text('Connected to database and seeded sample datasets!')),
                                  );
                                }
                              },
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      );
    }

    // ─── If DB connected, show beautiful financial metrics dashboard ─────────
    final kpis = state.dbKpis;
    final totalRevenue = kpis['total_revenue'] ?? 0.0;
    final totalProfit = kpis['total_profit'] ?? 0.0;
    final totalOrders = kpis['total_orders'] ?? 0;
    final avgOrder = kpis['avg_order_value'] ?? 0.0;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              const Text(
                '📊 Live Dashboard',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF0F172A),
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Connected to ${state.dbConfig['type'] ?? 'SQLite'} database — real-time sales performance metrics',
                style: const TextStyle(fontSize: 14, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 32),

              // KPI Metric Cards Grid
              LayoutBuilder(
                builder: (context, constraints) {
                  final double cardWidth = isDesktop 
                      ? (constraints.maxWidth - 48) / 4 
                      : (constraints.maxWidth - 16) / 2;
                  
                  return Wrap(
                    spacing: 16,
                    runSpacing: 16,
                    children: [
                      SizedBox(
                        width: cardWidth,
                        child: _buildKPICard(
                          label: 'TOTAL REVENUE',
                          value: '\$${totalRevenue.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}',
                          icon: Icons.monetization_on_rounded,
                          iconColor: const Color(0xFF2563EB),
                          bgColor: const Color(0xFFEFF6FF),
                        ),
                      ),
                      SizedBox(
                        width: cardWidth,
                        child: _buildKPICard(
                          label: 'TOTAL PROFIT',
                          value: '\$${totalProfit.toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}',
                          icon: Icons.trending_up_rounded,
                          iconColor: const Color(0xFF10B981),
                          bgColor: const Color(0xFFECFDF5),
                        ),
                      ),
                      SizedBox(
                        width: cardWidth,
                        child: _buildKPICard(
                          label: 'TOTAL ORDERS',
                          value: totalOrders.toString(),
                          icon: Icons.shopping_bag_rounded,
                          iconColor: const Color(0xFFF59E0B),
                          bgColor: const Color(0xFFFEF3C7),
                        ),
                      ),
                      SizedBox(
                        width: cardWidth,
                        child: _buildKPICard(
                          label: 'AVG ORDER VALUE',
                          value: '\$${avgOrder.toStringAsFixed(2)}',
                          icon: Icons.shopping_cart_rounded,
                          iconColor: const Color(0xFF8B5CF6),
                          bgColor: const Color(0xFFF5F3FF),
                        ),
                      ),
                    ],
                  );
                },
              ),
              const SizedBox(height: 32),

              // Charts Layout Row
              if (isDesktop) ...[
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      flex: 3,
                      child: _buildRevenueTrendChart(state),
                    ),
                    const SizedBox(width: 24),
                    Expanded(
                      flex: 2,
                      child: _buildRegionalPieChart(state),
                    ),
                  ],
                ),
              ] else ...[
                _buildRevenueTrendChart(state),
                const SizedBox(height: 24),
                _buildRegionalPieChart(state),
              ],
              const SizedBox(height: 24),

              // Recent Transactions Table Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Recent Transactions',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      const SizedBox(height: 20),
                      
                      // Transactions Scrollable Table
                      SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: ConstrainedBox(
                          constraints: BoxConstraints(
                            minWidth: isDesktop ? MediaQuery.of(context).size.width - 340 : 800,
                          ),
                          child: DataTable(
                            headingRowColor: MaterialStateProperty.all(const Color(0xFFF8FAFC)),
                            horizontalMargin: 12,
                            columnSpacing: 24,
                            columns: const [
                              DataColumn(label: Text('Order ID', style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text('Customer', style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text('Product Name', style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text('Region', style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text('Date', style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text('Amount', style: TextStyle(fontWeight: FontWeight.bold))),
                              DataColumn(label: Text('Status', style: TextStyle(fontWeight: FontWeight.bold))),
                            ],
                            rows: state.dbRecentOrders.map<DataRow>((order) {
                              final amount = order['total_amount'] ?? 0.0;
                              final status = order['status'] ?? 'Delivered';
                              final statusColor = status == 'Cancelled' ? Colors.red : Colors.green;
                              final statusBg = status == 'Cancelled' ? const Color(0xFFFEF2F2) : const Color(0xFFECFDF5);
                              
                              return DataRow(cells: [
                                DataCell(Text(order['order_id'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold))),
                                DataCell(Text(order['customer_name'] ?? '')),
                                DataCell(Text(order['product_name'] ?? '')),
                                DataCell(Text(order['region'] ?? '')),
                                DataCell(Text((order['order_date'] ?? '').toString().split(' ')[0])),
                                DataCell(Text('\$${amount.toStringAsFixed(2)}')),
                                DataCell(
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: statusBg,
                                      borderRadius: BorderRadius.circular(20),
                                    ),
                                    child: Text(
                                      status,
                                      style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                                    ),
                                  ),
                                ),
                              ]);
                            }).toList(),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildRevenueTrendChart(AppState state) {
    // Generate clean line chart items
    final List<_SalesData> data = state.dbMonthlySales.map<_SalesData>((e) {
      return _SalesData(e['month'] ?? '', (e['revenue'] ?? 0.0).toDouble());
    }).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Monthly Revenue Trends',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 280,
              child: SfCartesianChart(
                primaryXAxis: CategoryAxis(
                  majorGridLines: const MajorGridLines(width: 0),
                  labelStyle: const TextStyle(fontSize: 10),
                ),
                primaryYAxis: NumericAxis(
                  axisLine: const AxisLine(width: 0),
                  majorTickLines: const MajorTickLines(size: 0),
                  gridLines: const MajorGridLines(color: Color(0xFFF1F5F9)),
                  labelFormat: '\${value}',
                ),
                tooltipBehavior: TooltipBehavior(enable: true),
                series: <CartesianSeries<_SalesData, String>>[
                  AreaSeries<_SalesData, String>(
                    dataSource: data,
                    xValueMapper: (_SalesData sales, _) => sales.month,
                    yValueMapper: (_SalesData sales, _) => sales.revenue,
                    name: 'Revenue',
                    color: const Color(0xFF2563EB).withOpacity(0.08),
                    borderColor: const Color(0xFF2563EB),
                    borderWidth: 2.5,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRegionalPieChart(AppState state) {
    // Pie slices
    final List<_RegionData> data = state.dbRegionalSales.map<_RegionData>((e) {
      return _RegionData(e['region'] ?? '', (e['revenue'] ?? 0.0).toDouble());
    }).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Sales distribution by Region',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 280,
              child: SfCircularChart(
                legend: Legend(
                  isVisible: true,
                  overflowMode: LegendItemOverflowMode.wrap,
                  position: LegendPosition.bottom,
                ),
                tooltipBehavior: TooltipBehavior(enable: true),
                series: <CircularSeries<_RegionData, String>>[
                  DoughnutSeries<_RegionData, String>(
                    dataSource: data,
                    xValueMapper: (_RegionData r, _) => r.region,
                    yValueMapper: (_RegionData r, _) => r.revenue,
                    dataLabelSettings: const DataLabelSettings(isVisible: true),
                    innerRadius: '60%',
                    palette: const [
                      Color(0xFF2563EB), // Royal Blue
                      Color(0xFF10B981), // Emerald
                      Color(0xFFF59E0B), // Amber
                      Color(0xFF8B5CF6), // Purple
                      Color(0xFFEC4899), // Pink
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SalesData {
  _SalesData(this.month, this.revenue);
  final String month;
  final double revenue;
}

class _RegionData {
  _RegionData(this.region, this.revenue);
  final String region;
  final double revenue;
}
