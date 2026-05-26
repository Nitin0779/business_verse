import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';

class DataCleaningScreen extends StatefulWidget {
  const DataCleaningScreen({super.key});

  @override
  State<DataCleaningScreen> createState() => _DataCleaningScreenState();
}

class _DataCleaningScreenState extends State<DataCleaningScreen> with SingleTickerProviderStateMixin {
  TabController? _tabController;
  
  // Missing Tab States
  String _missingStrategy = 'mean';

  // Type Conversion Tab States
  String? _selectedConvertCol;
  String _selectedConvertType = 'numeric';

  // Feature Selection Tab States
  final List<String> _selectedFeatures = [];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 5, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final state = context.read<AppState>();
      if (state.hasActiveDataset) {
        state.fetchDatasetStats();
        _resetFeatureSelectionList(state);
      }
    });
  }

  void _resetFeatureSelectionList(AppState state) {
    setState(() {
      _selectedFeatures.clear();
      _selectedFeatures.addAll(state.columns);
      if (state.columns.isNotEmpty) {
        _selectedConvertCol = state.columns.first;
      }
    });
  }

  @override
  void dispose() {
    _tabController?.dispose();
    super.dispose();
  }

  Widget _buildBeforeAfterStatRow(AppState state) {
    final before = state.origStats;
    final after = state.cleanStats;
    
    return Row(
      children: [
        // Original Dataset Card
        Expanded(
          child: Card(
            color: const Color(0xFFF8FAFC),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('ORIGINAL DATASET', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildMetricMini('Rows', before['rows']?.toString() ?? '0'),
                      _buildMetricMini('Cols', before['columns']?.toString() ?? '0'),
                      _buildMetricMini('Nulls', before['missing']?.toString() ?? '0'),
                      _buildMetricMini('Dups', before['duplicates']?.toString() ?? '0'),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(width: 16),
        // Cleaned Dataset Card
        Expanded(
          child: Card(
            color: const Color(0xFFF0FDF4),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: const BorderSide(color: Color(0xFFBBF7D0)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('CLEANED DATASET', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Color(0xFF15803D))),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildMetricMini('Rows', after['rows']?.toString() ?? '0', isGreen: true),
                      _buildMetricMini('Cols', after['columns']?.toString() ?? '0', isGreen: true),
                      _buildMetricMini('Nulls', after['missing']?.toString() ?? '0', isGreen: true),
                      _buildMetricMini('Dups', after['duplicates']?.toString() ?? '0', isGreen: true),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMetricMini(String label, String val, {bool isGreen = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
        Text(val, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: isGreen ? const Color(0xFF16A34A) : const Color(0xFF0F172A))),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    
    // ─── If no dataset loaded, prompt to load first ─────────────────────────
    if (!state.hasActiveDataset) {
      return Scaffold(
        backgroundColor: const Color(0xFFF8FAFC),
        body: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.warning_amber_rounded, size: 64, color: Color(0xFFF59E0B)),
                const SizedBox(height: 20),
                const Text('No dataset loaded yet', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
                const SizedBox(height: 8),
                const Text('Please navigate to 📤 Data Upload and import your spreadsheets first.', style: TextStyle(color: Color(0xFF64748B))),
              ],
            ),
          ),
        ),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('🧹 Data Cleaning', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: Color(0xFF0F172A), letterSpacing: -0.5)),
                    const SizedBox(height: 4),
                    const Text('Clean, format, and prepare your spreadsheet columns for ML modeling.', style: TextStyle(fontSize: 14, color: Color(0xFF64748B))),
                  ],
                ),
                
                // Actions Row Reset/Save
                Row(
                  children: [
                    OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF64748B),
                        side: const BorderSide(color: Color(0xFFCBD5E1)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      icon: const Icon(Icons.refresh_rounded, size: 16),
                      label: const Text('Reset', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: () async {
                        await state.resetDataset();
                        _resetFeatureSelectionList(state);
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Dataset reset to original state.')));
                      },
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 24),

            // Statistics Row Original vs Cleaned
            _buildBeforeAfterStatRow(state),
            const SizedBox(height: 24),

            // Tab bar cleaner
            TabBar(
              controller: _tabController,
              isScrollable: true,
              tabs: const [
                Tab(icon: Icon(Icons.help_outline_rounded, size: 18), text: 'Handle Missing'),
                Tab(icon: Icon(Icons.difference_rounded, size: 18), text: 'Duplicates'),
                Tab(icon: Icon(Icons.swap_horiz_rounded, size: 18), text: 'Type Conversion'),
                Tab(icon: Icon(Icons.content_cut_rounded, size: 18), text: 'Feature Selection'),
                Tab(icon: Icon(Icons.remove_red_eye_rounded, size: 18), text: 'Preview'),
              ],
            ),
            const SizedBox(height: 24),

            // Tab contents
            Expanded(
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: state.isDataLoading
                      ? const Center(child: CircularProgressIndicator())
                      : TabBarView(
                          controller: _tabController,
                          children: [
                            _buildTabMissingValues(state),
                            _buildTabDuplicates(state),
                            _buildTabTypeConversion(state),
                            _buildTabFeatureSelection(state),
                            _buildTabPreview(state),
                          ],
                        ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ─── TAB 1: Handle Missing Values ──────────────────────────────────────────
  Widget _buildTabMissingValues(AppState state) {
    final list = state.missingReport;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (list.isEmpty) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFECFDF5),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFA7F3D0)),
            ),
            child: const Row(
              children: [
                Icon(Icons.check_circle_rounded, color: Colors.green),
                SizedBox(width: 12),
                Text('No missing values found in the active dataset!', style: TextStyle(color: Color(0xFF15803D), fontWeight: FontWeight.bold)),
              ],
            ),
          ),
        ] else ...[
          Text('Missing Values Report (${list.length} column(s)):', style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          Expanded(
            child: SingleChildScrollView(
              child: Table(
                border: TableBorder.all(color: const Color(0xFFE2E8F0)),
                columnWidths: const {
                  0: FlexColumnWidth(2),
                  1: FlexColumnWidth(1),
                  2: FlexColumnWidth(1),
                },
                children: [
                  TableRow(
                    decoration: const BoxDecoration(color: Color(0xFFF8FAFC)),
                    children: const [
                      Padding(padding: EdgeInsets.all(10), child: Text('Column', style: TextStyle(fontWeight: FontWeight.bold))),
                      Padding(padding: EdgeInsets.all(10), child: Text('Missing Count', style: TextStyle(fontWeight: FontWeight.bold))),
                      Padding(padding: EdgeInsets.all(10), child: Text('Percentage %', style: TextStyle(fontWeight: FontWeight.bold))),
                    ],
                  ),
                  ...list.map((item) {
                    return TableRow(
                      children: [
                        Padding(padding: const EdgeInsets.all(10), child: Text(item['Column']?.toString() ?? '')),
                        Padding(padding: const EdgeInsets.all(10), child: Text(item['Missing Count']?.toString() ?? '')),
                        Padding(padding: const EdgeInsets.all(10), child: Text('${item['Missing %']?.toString() ?? ''}%')),
                      ],
                    );
                  }).toList(),
                ],
              ),
            ),
          ),
        ],
        
        const Divider(height: 48),
        
        Row(
          children: [
            // Left Drop all nulls
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Drop row nulls', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    height: 44,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFFEF4444),
                        side: const BorderSide(color: Color(0xFFFCA5A5)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      icon: const Icon(Icons.delete_outline_rounded),
                      label: const Text('Drop All Null Rows', style: TextStyle(fontWeight: FontWeight.bold)),
                      onPressed: () async {
                        final success = await state.dropNullRows();
                        if (success && mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Dropped rows successfully.')));
                        }
                      },
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 32),
            // Right Fill Null Strategy
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Fill null strategy', style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<String>(
                          value: _missingStrategy,
                          decoration: InputDecoration(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 12),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                          items: const [
                            DropdownMenuItem(value: 'mean', child: Text('Mean')),
                            DropdownMenuItem(value: 'median', child: Text('Median')),
                            DropdownMenuItem(value: 'mode', child: Text('Mode')),
                            DropdownMenuItem(value: 'zero', child: Text('Zero')),
                          ],
                          onChanged: (val) {
                            if (val != null) {
                              setState(() {
                                _missingStrategy = val;
                              });
                            }
                          },
                        ),
                      ),
                      const SizedBox(width: 12),
                      SizedBox(
                        height: 44,
                        child: ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF2563EB),
                            foregroundColor: Colors.white,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            elevation: 0,
                          ),
                          onPressed: () async {
                            final success = await state.fillNullRows(_missingStrategy);
                            if (success && mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Filled nulls with $_missingStrategy.')));
                            }
                          },
                          child: const Text('Fill Nulls', style: TextStyle(fontWeight: FontWeight.bold)),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ─── TAB 2: Duplicates ─────────────────────────────────────────────────────
  Widget _buildTabDuplicates(AppState state) {
    final dupCount = state.cleanStats['duplicates'] ?? 0;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (dupCount == 0) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFECFDF5),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFA7F3D0)),
            ),
            child: const Row(
              children: [
                Icon(Icons.check_circle_rounded, color: Colors.green),
                SizedBox(width: 12),
                Text('No duplicate rows found!', style: TextStyle(color: Color(0xFF15803D), fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ] else ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFFFEF3C7),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFFCD34D)),
            ),
            child: Row(
              children: [
                const Icon(Icons.warning_amber_rounded, color: Color(0xFFD97706)),
                const SizedBox(width: 12),
                Text('Found $dupCount duplicate rows in the cleaned dataset.', style: const TextStyle(color: Color(0xFF92400E), fontWeight: FontWeight.bold)),
              ],
            ),
          ),
          const SizedBox(height: 24),
        ],

        Row(
          children: [
            ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFEF4444),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                elevation: 0,
              ),
              icon: const Icon(Icons.cleaning_services_rounded, size: 18),
              label: const Text('Clean Duplicates', style: TextStyle(fontWeight: FontWeight.bold)),
              onPressed: dupCount == 0
                  ? null
                  : () async {
                      final success = await state.removeDuplicateRows();
                      if (success && mounted) {
                        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Duplicates removed!')));
                      }
                    },
            ),
          ],
        ),
      ],
    );
  }

  // ─── TAB 3: Type Conversion ────────────────────────────────────────────────
  Widget _buildTabTypeConversion(AppState state) {
    if (state.columns.isEmpty) return const SizedBox();
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Select column to convert data type:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 20),
        
        Row(
          children: [
            // Col picker
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _selectedConvertCol,
                decoration: InputDecoration(
                  labelText: 'Select Column',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                items: state.columns.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                onChanged: (val) {
                  setState(() {
                    _selectedConvertCol = val;
                  });
                },
              ),
            ),
            const SizedBox(width: 24),
            // Datatype picker
            Expanded(
              child: DropdownButtonFormField<String>(
                value: _selectedConvertType,
                decoration: InputDecoration(
                  labelText: 'Target Type',
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                ),
                items: const [
                  DropdownMenuItem(value: 'numeric', child: Text('Numeric (Float)')),
                  DropdownMenuItem(value: 'int', child: Text('Integer')),
                  DropdownMenuItem(value: 'str', child: Text('String (Text)')),
                  DropdownMenuItem(value: 'datetime', child: Text('DateTime')),
                ],
                onChanged: (val) {
                  if (val != null) {
                    setState(() {
                      _selectedConvertType = val;
                    });
                  }
                },
              ),
            ),
          ],
        ),
        
        const SizedBox(height: 32),
        
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF2563EB),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            elevation: 0,
          ),
          icon: const Icon(Icons.swap_horiz_rounded),
          label: const Text('Convert Column Type', style: TextStyle(fontWeight: FontWeight.bold)),
          onPressed: () async {
            if (_selectedConvertCol == null) return;
            final conversions = {_selectedConvertCol!: _selectedConvertType};
            final success = await state.convertTypes(conversions);
            if (success && mounted) {
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Converted $_selectedConvertCol to $_selectedConvertType.')));
            }
          },
        ),
      ],
    );
  }

  // ─── TAB 4: Feature Selection ──────────────────────────────────────────────
  Widget _buildTabFeatureSelection(AppState state) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Select spreadsheet columns to KEEP in the final dataset:', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 16),
        
        Expanded(
          child: Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: const BorderSide(color: Color(0xFFE2E8F0)),
            ),
            child: ListView(
              children: state.columns.map((col) {
                final isChecked = _selectedFeatures.contains(col);
                return CheckboxListTile(
                  title: Text(col, style: const TextStyle(fontWeight: FontWeight.bold)),
                  value: isChecked,
                  onChanged: (bool? checked) {
                    setState(() {
                      if (checked == true) {
                        _selectedFeatures.add(col);
                      } else {
                        if (_selectedFeatures.length > 1) {
                          _selectedFeatures.remove(col);
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('You must keep at least 1 column!')),
                          );
                        }
                      }
                    });
                  },
                );
              }).toList(),
            ),
          ),
        ),
        
        const SizedBox(height: 24),
        
        ElevatedButton.icon(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF2563EB),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            elevation: 0,
          ),
          icon: const Icon(Icons.content_cut_rounded),
          label: const Text('Apply Column Selection', style: TextStyle(fontWeight: FontWeight.bold)),
          onPressed: () async {
            final success = await state.selectFeatures(_selectedFeatures);
            if (success && mounted) {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Columns updated successfully.')));
            }
          },
        ),
      ],
    );
  }

  // ─── TAB 5: Preview ────────────────────────────────────────────────────────
  Widget _buildTabPreview(AppState state) {
    if (state.previewRows.isEmpty) {
      return const Center(child: Text('No preview rows available.'));
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SingleChildScrollView(
              child: DataTable(
                headingRowColor: MaterialStateProperty.all(const Color(0xFFF8FAFC)),
                columns: state.columns.map((c) => DataColumn(label: Text(c, style: const TextStyle(fontWeight: FontWeight.bold)))).toList(),
                rows: state.previewRows.map<DataRow>((row) {
                  return DataRow(
                    cells: state.columns.map<DataCell>((col) {
                      final val = row[col];
                      return DataCell(Text(val == null ? 'Null' : val.toString()));
                    }).toList(),
                  );
                }).toList(),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
