import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:syncfusion_flutter_charts/charts.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';

class ReportsScreen extends StatefulWidget {
  const ReportsScreen({super.key});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> with SingleTickerProviderStateMixin {
  TabController? _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AppState>().fetchReportSummary();
    });
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  void _triggerDownload(String target, String type, AppState state) {
    // Generate the exact backend download link
    final period = Uri.encodeComponent(state.repPeriod);
    final region = Uri.encodeComponent(state.repRegion);
    final category = Uri.encodeComponent(state.repCategory);
    
    final downloadUrl = '${ApiService.baseUrl}/reports/download/$type?target=$target&period=$period&region=$region&category=$category';
    
    // Show download link info to the user (highly reliable across Web, Mobile and Desktop targets)
    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Row(
            children: const [
              Icon(Icons.file_download_rounded, color: Color(0xFF2563EB)),
              SizedBox(width: 8),
              Text('Download Ready', style: TextStyle(fontWeight: FontWeight.bold)),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Your filtered $target ${type.toUpperCase()} file is ready for download.',
                style: const TextStyle(fontSize: 14),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: SelectableText(
                  downloadUrl,
                  style: const TextStyle(fontFamily: 'Courier', fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF334155)),
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final isDesktop = MediaQuery.of(context).size.width >= 1024;
    final kpis = state.repKpis;
    final totalRevenue = kpis['total_revenue'] ?? 0.0;
    final totalProfit = kpis['total_profit'] ?? 0.0;
    final totalOrders = kpis['total_orders'] ?? 0;
    final avgOrder = kpis['avg_order_value'] ?? 0.0;
    final margin = kpis['profit_margin_pct'] ?? 0.0;
    final customers = kpis['unique_customers'] ?? 0;

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
                '📄 Reports & Exports',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.w800,
                  color: Color(0xFF0F172A),
                  letterSpacing: -0.5,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                'Export tabular data sheets, compile dynamic reports, and download Excel archives.',
                style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 32),

              // Filter Configuration Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Filter Report Configuration', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 20,
                        runSpacing: 16,
                        children: [
                          // Period
                          SizedBox(
                            width: 200,
                            child: DropdownButtonFormField<String>(
                              value: state.repPeriod,
                              decoration: const InputDecoration(labelText: 'Period', contentPadding: EdgeInsets.symmetric(horizontal: 12)),
                              items: const [
                                DropdownMenuItem(value: 'All Time', child: Text('All Time')),
                                DropdownMenuItem(value: 'Last 30 Days', child: Text('Last 30 Days')),
                                DropdownMenuItem(value: 'Last 90 Days', child: Text('Last 90 Days')),
                                DropdownMenuItem(value: 'Last 6 Months', child: Text('Last 6 Months')),
                                DropdownMenuItem(value: 'Last 12 Months', child: Text('Last 12 Months')),
                                DropdownMenuItem(value: 'Year 2022', child: Text('Year 2022')),
                                DropdownMenuItem(value: 'Year 2023', child: Text('Year 2023')),
                                DropdownMenuItem(value: 'Year 2024', child: Text('Year 2024')),
                              ],
                              onChanged: (val) {
                                if (val != null) {
                                  state.fetchReportSummary(period: val);
                                }
                              },
                            ),
                          ),
                          // Region
                          SizedBox(
                            width: 200,
                            child: DropdownButtonFormField<String>(
                              value: state.repRegion,
                              decoration: const InputDecoration(labelText: 'Region', contentPadding: EdgeInsets.symmetric(horizontal: 12)),
                              items: state.repFilterRegions.map((r) => DropdownMenuItem(value: r, child: Text(r))).toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  state.fetchReportSummary(region: val);
                                }
                              },
                            ),
                          ),
                          // Category
                          SizedBox(
                            width: 200,
                            child: DropdownButtonFormField<String>(
                              value: state.repCategory,
                              decoration: const InputDecoration(labelText: 'Category', contentPadding: EdgeInsets.symmetric(horizontal: 12)),
                              items: state.repFilterCategories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  state.fetchReportSummary(category: val);
                                }
                              },
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 32),

              if (state.isRepLoading) ...[
                const Center(child: CircularProgressIndicator()),
              ] else ...[
                // Metrics dashboard mini rows
                Wrap(
                  spacing: 16,
                  runSpacing: 16,
                  children: [
                    _buildKPIMiniCard('Revenue', '\$${totalRevenue.toStringAsFixed(0)}'),
                    _buildKPIMiniCard('Profit', '\$${totalProfit.toStringAsFixed(0)}'),
                    _buildKPIMiniCard('Orders count', totalOrders.toString()),
                    _buildKPIMiniCard('Customers', customers.toString()),
                    _buildKPIMiniCard('Avg Order', '\$${avgOrder.toStringAsFixed(2)}'),
                    _buildKPIMiniCard('Margin %', '${margin.toStringAsFixed(1)}%'),
                  ],
                ),
                
                const SizedBox(height: 32),

                // Charts
                if (isDesktop) ...[
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(flex: 3, child: _buildMonthlyAggregatedChart(state)),
                      const SizedBox(width: 24),
                      Expanded(flex: 2, child: _buildCategoryDoughnut(state)),
                    ],
                  ),
                ] else ...[
                  _buildMonthlyAggregatedChart(state),
                  const SizedBox(height: 24),
                  _buildCategoryDoughnut(state),
                ],
                
                const SizedBox(height: 32),

                // Exporter Cockpit Tabs
                const Text('Download Data Center', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
                const SizedBox(height: 16),
                
                TabBar(
                  controller: _tabController,
                  isScrollable: true,
                  tabs: const [
                    Tab(icon: Icon(Icons.shopping_bag_rounded, size: 16), text: 'Orders Sheet'),
                    Tab(icon: Icon(Icons.people_rounded, size: 16), text: 'Customers Directory'),
                    Tab(icon: Icon(Icons.storefront_rounded, size: 16), text: 'Products Catalog'),
                    Tab(icon: Icon(Icons.analytics_rounded, size: 16), text: 'Excel Summary Report'),
                  ],
                ),
                const SizedBox(height: 24),
                
                SizedBox(
                  height: 200,
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: TabBarView(
                        controller: _tabController,
                        children: [
                          _buildDownloadTab('orders', 'Download active filtered orders dataset.', state),
                          _buildDownloadTab('customers', 'Download complete customer directories.', state),
                          _buildDownloadTab('products', 'Download products pricing catalog.', state),
                          _buildDownloadTab('analytics_report', 'Download multi-sheet compiled Excel report (KPI summaries, region sales, monthly aggregation, product rating matrices).', state, isReport: true),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildKPIMiniCard(String label, String value) {
    final double cardWidth = (MediaQuery.of(context).size.width >= 1024) 
        ? (MediaQuery.of(context).size.width - 144) / 6 
        : (MediaQuery.of(context).size.width - 96) / 3;

    return SizedBox(
      width: cardWidth,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Color(0xFF64748B)),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMonthlyAggregatedChart(AppState state) {
    final List<_ChartPoint> data = state.repMonthlySales.map<_ChartPoint>((e) {
      return _ChartPoint(e['month'] ?? '', (e['revenue'] ?? 0.0).toDouble());
    }).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Filtered Monthly Sales Revenue', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            SizedBox(
              height: 280,
              child: SfCartesianChart(
                primaryXAxis: CategoryAxis(majorGridLines: const MajorGridLines(width: 0)),
                primaryYAxis: NumericAxis(labelFormat: '\${value}', majorGridLines: const MajorGridLines(color: Color(0xFFF1F5F9))),
                series: <CartesianSeries>[
                  ColumnSeries<_ChartPoint, String>(
                    dataSource: data,
                    xValueMapper: (_ChartPoint p, _) => p.x,
                    yValueMapper: (_ChartPoint p, _) => p.y,
                    color: const Color(0xFF2563EB).withOpacity(0.3),
                    borderColor: const Color(0xFF2563EB),
                    borderWidth: 1,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCategoryDoughnut(AppState state) {
    final List<_ChartPoint> data = state.repCategoryPerf.map<_ChartPoint>((e) {
      return _ChartPoint(e['category'] ?? '', (e['revenue'] ?? 0.0).toDouble());
    }).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Category Performance Shares', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            SizedBox(
              height: 280,
              child: SfCircularChart(
                palette: const [
                  Color(0xFF2563EB),
                  Color(0xFF10B981),
                  Color(0xFFF59E0B),
                  Color(0xFF8B5CF6),
                ],
                legend: Legend(isVisible: true, position: LegendPosition.bottom, overflowMode: LegendItemOverflowMode.wrap),
                series: <CircularSeries>[
                  DoughnutSeries<_ChartPoint, String>(
                    dataSource: data,
                    xValueMapper: (_ChartPoint p, _) => p.x,
                    yValueMapper: (_ChartPoint p, _) => p.y,
                    innerRadius: '60%',
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDownloadTab(String target, String description, AppState state, {bool isReport = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          description,
          style: const TextStyle(fontSize: 14, color: Color(0xFF475569)),
        ),
        const SizedBox(height: 24),
        Row(
          children: [
            if (!isReport) ...[
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2563EB),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  elevation: 0,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                ),
                icon: const Icon(Icons.file_download_outlined, size: 18),
                label: const Text('Download CSV', style: TextStyle(fontWeight: FontWeight.bold)),
                onPressed: () => _triggerDownload(target, 'csv', state),
              ),
              const SizedBox(width: 16),
            ],
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF10B981),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                elevation: 0,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              ),
              icon: const Icon(Icons.table_view_rounded, size: 18),
              label: Text(isReport ? 'Generate Excel Analytics Report' : 'Download Excel', style: const TextStyle(fontWeight: FontWeight.bold)),
              onPressed: () => _triggerDownload(target, 'excel', state),
            ),
          ],
        ),
      ],
    );
  }
}

class _ChartPoint {
  _ChartPoint(this.x, this.y);
  final String x;
  final double y;
}
