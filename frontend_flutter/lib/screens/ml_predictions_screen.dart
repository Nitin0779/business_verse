import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:syncfusion_flutter_charts/charts.dart';
import '../providers/app_state.dart';

class MLPredictionsScreen extends StatefulWidget {
  const MLPredictionsScreen({super.key});

  @override
  State<MLPredictionsScreen> createState() => _MLPredictionsScreenState();
}

class _MLPredictionsScreenState extends State<MLPredictionsScreen> with SingleTickerProviderStateMixin {
  TabController? _tabController;

  // Forecasting states
  double _forecastMonths = 6.0;

  // Churn states
  double _churnTrees = 100.0;
  // Single customer inputs
  final _freqController = TextEditingController(text: '5');
  final _aovController = TextEditingController(text: '200');
  final _daysController = TextEditingController(text: '60');
  final _ticketsController = TextEditingController(text: '1');
  double _satisfaction = 7.0;
  final _spendController = TextEditingController(text: '1000');

  bool _isSinglePredicting = false;
  Map<String, dynamic>? _singleChurnResult;

  // Segmentation states
  double _segmentK = 4.0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController?.dispose();
    _freqController.dispose();
    _aovController.dispose();
    _daysController.dispose();
    _ticketsController.dispose();
    _spendController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final isDesktop = MediaQuery.of(context).size.width >= 1024;

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            const Text(
              '🤖 ML Predictions',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w800,
                color: Color(0xFF0F172A),
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Machine learning models for forecasting sales, classifying churn, and customer profiling.',
              style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 24),

            // Tab navigation bar
            TabBar(
              controller: _tabController,
              tabs: const [
                Tab(icon: Icon(Icons.trending_up_rounded, size: 18), text: 'Sales Prediction'),
                Tab(icon: Icon(Icons.warning_amber_rounded, size: 18), text: 'Churn Prediction'),
                Tab(icon: Icon(Icons.donut_large_rounded, size: 18), text: 'Segmentation'),
              ],
            ),
            const SizedBox(height: 24),

            // Tab contents
            Expanded(
              child: state.isMlLoading
                  ? const Center(child: CircularProgressIndicator())
                  : TabBarView(
                      controller: _tabController,
                      children: [
                        _buildTabSalesForecasting(state, isDesktop),
                        _buildTabChurnClassifier(state, isDesktop),
                        _buildTabSegmentation(state, isDesktop),
                      ],
                    ),
            ),
          ],
        ),
      ),
    );
  }

  // ─── TAB 1: SALES FORECASTING ──────────────────────────────────────────────
  Widget _buildTabSalesForecasting(AppState state, bool isDesktop) {
    final hist = state.salesHistorical;
    final fore = state.salesForecast;
    
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Info Card
              Expanded(
                flex: 3,
                child: Card(
                  color: const Color(0xFFF8FAFC),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Model Overview', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A))),
                        const SizedBox(height: 12),
                        _buildOverviewRow('Algorithm', 'Linear Regression'),
                        _buildOverviewRow('Target', 'Monthly Sales Revenue'),
                        _buildOverviewRow('Features', 'Month, Quarter, Year, Shift Lags'),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 24),
              // Forecast parameters
              Expanded(
                flex: 2,
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Months to Forecast: ${_forecastMonths.toInt()}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5)),
                        Slider(
                          min: 1, max: 12, divisions: 11,
                          value: _forecastMonths,
                          onChanged: (val) {
                            setState(() {
                              _forecastMonths = val;
                            });
                          },
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          height: 40,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF2563EB),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              elevation: 0,
                            ),
                            icon: const Icon(Icons.flash_on_rounded, size: 16),
                            label: const Text('Train & Forecast', style: TextStyle(fontWeight: FontWeight.bold)),
                            onPressed: () async {
                              final ok = await state.trainSalesForecast(_forecastMonths.toInt());
                              if (ok && mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Linear regression forecasting trained!')));
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
          
          if (hist.isNotEmpty) ...[
            const SizedBox(height: 24),
            // R2 / MAE displays
            Row(
              children: [
                _buildStatMetricDisplay('R² Model Score', state.salesR2.toStringAsFixed(3)),
                const SizedBox(width: 20),
                _buildStatMetricDisplay('Mean Absolute Error (MAE)', '\$${state.salesMae.toStringAsFixed(0)}'),
              ],
            ),
            const SizedBox(height: 24),
            
            // Syncfusion Forecast Area Chart
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Revenue Forecasting Visualization', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    SizedBox(
                      height: 320,
                      child: SfCartesianChart(
                        primaryXAxis: CategoryAxis(majorGridLines: const MajorGridLines(width: 0)),
                        primaryYAxis: NumericAxis(labelFormat: '\${value}', majorGridLines: const MajorGridLines(color: Color(0xFFF1F5F9))),
                        legend: Legend(isVisible: true, position: LegendPosition.bottom),
                        series: <CartesianSeries>[
                          LineSeries<_SalesPoint, String>(
                            dataSource: hist.map<_SalesPoint>((e) => _SalesPoint(e['period'], e['revenue'].toDouble())).toList(),
                            xValueMapper: (_SalesPoint s, _) => s.period,
                            yValueMapper: (_SalesPoint s, _) => s.revenue,
                            name: 'Historical Revenue',
                            color: const Color(0xFF2563EB),
                            width: 2.5,
                          ),
                          LineSeries<_SalesPoint, String>(
                            dataSource: fore.map<_SalesPoint>((e) => _SalesPoint(e['period'], e['revenue'].toDouble())).toList(),
                            xValueMapper: (_SalesPoint s, _) => s.period,
                            yValueMapper: (_SalesPoint s, _) => s.revenue,
                            name: 'Forecast Prediction',
                            color: const Color(0xFFF59E0B),
                            width: 2.5,
                            dashArray: const [5, 5],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  // ─── TAB 2: CHURN PREDICTION ──────────────────────────────────────────────
  Widget _buildTabChurnClassifier(AppState state, bool isDesktop) {
    final fi = state.churnFeatureImportance;
    
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Info Card
              Expanded(
                flex: 3,
                child: Card(
                  color: const Color(0xFFF8FAFC),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Model Overview', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A))),
                        const SizedBox(height: 12),
                        _buildOverviewRow('Algorithm', 'Random Forest Classifier'),
                        _buildOverviewRow('Target', 'Churn Label (0 = Retained, 1 = Churned)'),
                        _buildOverviewRow('Features', 'Frequency, Avg Spend, Inactivity Days, Support tickets, Satisfaction score'),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 24),
              // Parameters
              Expanded(
                flex: 2,
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Random Forest Trees: ${_churnTrees.toInt()}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5)),
                        Slider(
                          min: 50, max: 300, divisions: 5,
                          value: _churnTrees,
                          onChanged: (val) {
                            setState(() {
                              _churnTrees = val;
                            });
                          },
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          height: 40,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF2563EB),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              elevation: 0,
                            ),
                            icon: const Icon(Icons.flash_on_rounded, size: 16),
                            label: const Text('Train Classifier', style: TextStyle(fontWeight: FontWeight.bold)),
                            onPressed: () async {
                              final ok = await state.trainChurnModel(_churnTrees.toInt());
                              if (ok && mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Random forest churn model successfully trained!')));
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
          
          if (fi.isNotEmpty) ...[
            const SizedBox(height: 24),
            Row(
              children: [
                _buildStatMetricDisplay('Accuracy Score', '${(state.churnAccuracy * 100).toStringAsFixed(1)}%'),
                const SizedBox(width: 20),
                _buildStatMetricDisplay('Historical Churn Rate', '${(state.churnRate * 100).toStringAsFixed(1)}%'),
              ],
            ),
            const SizedBox(height: 24),
            
            // Feature Importance horizontal Bar Chart
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Random Forest Feature Importance Breakdown', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 16),
                    SizedBox(
                      height: 280,
                      child: SfCartesianChart(
                        primaryXAxis: CategoryAxis(majorGridLines: const MajorGridLines(width: 0)),
                        primaryYAxis: NumericAxis(labelFormat: '{value}', title: AxisTitle(text: 'Importance Score')),
                        series: <CartesianSeries>[
                          BarSeries<_FeaturePoint, String>(
                            dataSource: fi.map<_FeaturePoint>((e) => _FeaturePoint(e['feature'], e['importance'].toDouble())).toList(),
                            xValueMapper: (_FeaturePoint f, _) => f.feature.replaceAll('_', ' '),
                            yValueMapper: (_FeaturePoint f, _) => f.score,
                            color: const Color(0xFF2563EB),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Churn predictor for a single customer inputs
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Predict Churn for a Single Customer Profile', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
                    const SizedBox(height: 20),
                    
                    Row(
                      children: [
                        Expanded(child: _buildTextField('Purchase Frequency', _freqController)),
                        const SizedBox(width: 16),
                        Expanded(child: _buildTextField('Avg Order Value (\$)', _aovController)),
                        const SizedBox(width: 16),
                        Expanded(child: _buildTextField('Days since last order', _daysController)),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(child: _buildTextField('Support Tickets opened', _ticketsController)),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Satisfaction Score (1-10): ${_satisfaction.toInt()}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                              Slider(
                                min: 1, max: 10, divisions: 9,
                                value: _satisfaction,
                                onChanged: (val) {
                                  setState(() {
                                    _satisfaction = val;
                                  });
                                },
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(child: _buildTextField('Total Spent (\$)', _spendController)),
                      ],
                    ),
                    const SizedBox(height: 24),
                    
                    // Trigger
                    Row(
                      children: [
                        ElevatedButton.icon(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF2563EB),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                            elevation: 0,
                          ),
                          icon: const Icon(Icons.search_rounded),
                          label: const Text('Calculate Churn Risk', style: TextStyle(fontWeight: FontWeight.bold)),
                          onPressed: () async {
                            setState(() {
                              _isSinglePredicting = true;
                              _singleChurnResult = null;
                            });
                            final res = await state.predictSingleChurnRisk(
                              double.tryParse(_freqController.text) ?? 5,
                              double.tryParse(_aovController.text) ?? 200,
                              double.tryParse(_daysController.text) ?? 60,
                              double.tryParse(_ticketsController.text) ?? 1,
                              _satisfaction,
                              double.tryParse(_spendController.text) ?? 1000,
                            );
                            setState(() {
                              _isSinglePredicting = false;
                              _singleChurnResult = res;
                            });
                          },
                        ),
                        
                        if (_isSinglePredicting) ...[
                          const SizedBox(width: 24),
                          const CircularProgressIndicator(),
                        ],
                        
                        if (_singleChurnResult != null) ...[
                          const SizedBox(width: 32),
                          Icon(
                            _singleChurnResult!['churn_prediction'] == 1
                                ? Icons.warning_amber_rounded
                                : Icons.check_circle_outline_rounded,
                            color: _singleChurnResult!['churn_prediction'] == 1 ? Colors.red : Colors.green,
                            size: 28,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            _singleChurnResult!['churn_prediction'] == 1
                                ? 'HIGH RISK OF CHURN'
                                : 'LOW CHURN RISK',
                            style: TextStyle(
                              color: _singleChurnResult!['churn_prediction'] == 1 ? Colors.red : Colors.green,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                          const SizedBox(width: 24),
                          Text(
                            'Churn Probability: ${(_singleChurnResult!['churn_probability'] * 100).toStringAsFixed(1)}%',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildTextField(String label, TextEditingController controller) {
    return TextFormField(
      controller: controller,
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(fontSize: 12),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      ),
      keyboardType: TextInputType.number,
    );
  }

  // ─── TAB 3: CUSTOMER SEGMENTATION ──────────────────────────────────────────
  Widget _buildTabSegmentation(AppState state, bool isDesktop) {
    final dist = state.segClusterDistribution;
    final scatter = state.segScatterData;
    final summary = state.segSummary;
    
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Info Card
              Expanded(
                flex: 3,
                child: Card(
                  color: const Color(0xFFF8FAFC),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Model Overview', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0F172A))),
                        const SizedBox(height: 12),
                        _buildOverviewRow('Algorithm', 'K-Means Clustering'),
                        _buildOverviewRow('Features', 'Total Spent, Frequency, Avg Order, Inactivity Days, Satisfaction'),
                        _buildOverviewRow('Output', 'Named customer profile segments (Loyals, Champions, Dormant)'),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 24),
              // Parameters
              Expanded(
                flex: 2,
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Target Segments (K): ${_segmentK.toInt()}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5)),
                        Slider(
                          min: 2, max: 8, divisions: 6,
                          value: _segmentK,
                          onChanged: (val) {
                            setState(() {
                              _segmentK = val;
                            });
                          },
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          height: 40,
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF2563EB),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                              elevation: 0,
                            ),
                            icon: const Icon(Icons.flash_on_rounded, size: 16),
                            label: const Text('Run Segmentation', style: TextStyle(fontWeight: FontWeight.bold)),
                            onPressed: () async {
                              final ok = await state.runCustomerSegmentation(_segmentK.toInt());
                              if (ok && mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('K-Means customer profile clusters run!')));
                              }
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
          
          if (dist.isNotEmpty) ...[
            const SizedBox(height: 24),
            
            // pie / doughnut sizes vs spend scatter row
            if (isDesktop) ...[
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    flex: 2,
                    child: _buildSegmentationPieDoughnut(dist),
                  ),
                  const SizedBox(width: 24),
                  Expanded(
                    flex: 3,
                    child: _buildSegmentationScatterPlot(scatter),
                  ),
                ],
              ),
            ] else ...[
              _buildSegmentationPieDoughnut(dist),
              const SizedBox(height: 24),
              _buildSegmentationScatterPlot(scatter),
            ],
            const SizedBox(height: 24),
            
            // Segment summary table
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Segment Clusters Statistical Summary', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
                    const SizedBox(height: 16),
                    
                    SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: DataTable(
                        headingRowColor: MaterialStateProperty.all(const Color(0xFFF8FAFC)),
                        columns: const [
                          DataColumn(label: Text('Segment Group', style: TextStyle(fontWeight: FontWeight.bold))),
                          DataColumn(label: Text('Customer Count', style: TextStyle(fontWeight: FontWeight.bold))),
                          DataColumn(label: Text('Avg Spend (\$)', style: TextStyle(fontWeight: FontWeight.bold))),
                          DataColumn(label: Text('Avg Purchase Freq', style: TextStyle(fontWeight: FontWeight.bold))),
                          DataColumn(label: Text('Avg Inactivity Days', style: TextStyle(fontWeight: FontWeight.bold))),
                          DataColumn(label: Text('Avg Satisfaction (1-10)', style: TextStyle(fontWeight: FontWeight.bold))),
                        ],
                        rows: summary.map<DataRow>((seg) {
                          return DataRow(cells: [
                            DataCell(Text(seg['segment'] ?? '', style: const TextStyle(fontWeight: FontWeight.bold))),
                            DataCell(Text(seg['customers']?.toString() ?? '')),
                            DataCell(Text('\$${(seg['avg_spend'] ?? 0.0).toStringAsFixed(0)}')),
                            DataCell(Text(seg['avg_frequency']?.toString() ?? '')),
                            DataCell(Text(seg['avg_days_inactive']?.toString() ?? '')),
                            DataCell(Text(seg['avg_satisfaction']?.toString() ?? '')),
                          ]);
                        }).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSegmentationPieDoughnut(List<dynamic> dist) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Segment Cluster Distribution', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            SizedBox(
              height: 280,
              child: SfCircularChart(
                palette: const [
                  Color(0xFF2563EB),
                  Color(0xFF10B981),
                  Color(0xFFF59E0B),
                  Color(0xFF8B5CF6),
                  Color(0xFFEC4899),
                ],
                legend: Legend(isVisible: true, position: LegendPosition.bottom, overflowMode: LegendItemOverflowMode.wrap),
                series: <CircularSeries>[
                  DoughnutSeries<_PiePoint, String>(
                    dataSource: dist.map<_PiePoint>((e) => _PiePoint(e['Segment'], e['count'].toDouble())).toList(),
                    xValueMapper: (_PiePoint p, _) => p.name,
                    yValueMapper: (_PiePoint p, _) => p.value,
                    dataLabelSettings: const DataLabelSettings(isVisible: true),
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

  Widget _buildSegmentationScatterPlot(List<dynamic> scatter) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Spend vs Frequency Scatter Plot', style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            SizedBox(
              height: 280,
              child: SfCartesianChart(
                primaryXAxis: NumericAxis(
                  title: AxisTitle(text: 'Total Spent (\$)'),
                  labelFormat: '\${value}',
                  majorGridLines: const MajorGridLines(color: Color(0xFFF1F5F9)),
                ),
                primaryYAxis: NumericAxis(
                  title: AxisTitle(text: 'Purchase Frequency'),
                  majorGridLines: const MajorGridLines(color: Color(0xFFF1F5F9)),
                ),
                series: <CartesianSeries>[
                  ScatterSeries<_ScatterPoint, double>(
                    dataSource: scatter.map<_ScatterPoint>((e) {
                      return _ScatterPoint(
                        (e['total_spent'] ?? 0.0).toDouble(),
                        (e['purchase_frequency'] ?? 0.0).toDouble(),
                        e['segment'] ?? '',
                      );
                    }).toList(),
                    xValueMapper: (_ScatterPoint s, _) => s.spent,
                    yValueMapper: (_ScatterPoint s, _) => s.freq,
                    pointColorMapper: (_ScatterPoint s, _) {
                      // Harmonize color with segment name
                      if (s.segment.contains('Champions')) return const Color(0xFF2563EB);
                      if (s.segment.contains('Loyal')) return const Color(0xFF10B981);
                      if (s.segment.contains('Promising')) return const Color(0xFFF59E0B);
                      if (s.segment.contains('Risk')) return const Color(0xFF8B5CF6);
                      return const Color(0xFFEC4899);
                    },
                    markerSettings: const MarkerSettings(width: 8, height: 8, shape: DataMarkerType.circle),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Helper row builder
  Widget _buildOverviewRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('$label: ', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF475569))),
          Expanded(child: Text(value, style: const TextStyle(fontSize: 13, color: Color(0xFF64748B)))),
        ],
      ),
    );
  }

  Widget _buildStatMetricDisplay(String label, String value) {
    return Expanded(
      child: Card(
        color: Colors.white,
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
              const SizedBox(height: 4),
              Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
            ],
          ),
        ),
      ),
    );
  }
}

class _SalesPoint {
  _SalesPoint(this.period, this.revenue);
  final String period;
  final double revenue;
}

class _FeaturePoint {
  _FeaturePoint(this.feature, this.score);
  final String feature;
  final double score;
}

class _PiePoint {
  _PiePoint(this.name, this.value);
  final String name;
  final double value;
}

class _ScatterPoint {
  _ScatterPoint(this.spent, this.freq, this.segment);
  final double spent;
  final double freq;
  final String segment;
}
