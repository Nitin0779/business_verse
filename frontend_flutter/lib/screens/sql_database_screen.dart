import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';

class SQLDatabaseScreen extends StatefulWidget {
  const SQLDatabaseScreen({super.key});

  @override
  State<SQLDatabaseScreen> createState() => _SQLDatabaseScreenState();
}

class _SQLDatabaseScreenState extends State<SQLDatabaseScreen> {
  final _sqlController = TextEditingController(text: 'SELECT * FROM customers LIMIT 10;');

  Widget _buildDatabaseConnectionStatus(AppState state) {
    final statusColor = state.isDBConnected ? Colors.green : Colors.red;
    final statusText = state.isDBConnected ? 'CONNECTED' : 'DISCONNECTED';
    final dbType = state.dbConfig['type'] ?? 'sqlite';
    final dbName = state.dbConfig['database'] ?? 'businessverse';

    return Card(
      color: state.isDBConnected ? const Color(0xFFECFDF5) : const Color(0xFFFEF2F2),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: state.isDBConnected ? const Color(0xFFA7F3D0) : const Color(0xFFFCA5A5)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Row(
          children: [
            Icon(state.isDBConnected ? Icons.cloud_done_rounded : Icons.cloud_off_rounded, color: statusColor, size: 24),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text(
                        'Database Engine: ',
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF64748B)),
                      ),
                      Text(
                        statusText,
                        style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: statusColor),
                      ),
                    ],
                  ),
                  const SizedBox(height: 2),
                  Text(
                    state.isDBConnected ? 'Connection Type: ${dbType.toUpperCase()} | Base Database: $dbName' : 'Database connection has not been verified yet.',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF0F172A)),
                  ),
                ],
              ),
            ),
            if (!state.isDBConnected)
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2563EB),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  elevation: 0,
                ),
                onPressed: () async {
                  final ok = await state.testDatabaseConnection();
                  if (ok && mounted) {
                    await state.seedMockDBData();
                  }
                },
                child: const Text('Connect Engine', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickQueryButton(String label, String sql) {
    return Padding(
      padding: const EdgeInsets.only(right: 12, bottom: 8),
      child: ActionChip(
        avatar: const Icon(Icons.code_rounded, size: 14, color: Color(0xFF2563EB)),
        label: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8), side: const BorderSide(color: Color(0xFFE2E8F0))),
        backgroundColor: Colors.white,
        onPressed: () {
          _sqlController.text = sql;
        },
      ),
    );
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
              '🛢️ SQL Database Playground',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.w800,
                color: Color(0xFF0F172A),
                letterSpacing: -0.5,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Direct read-only SQL relational console. Write custom queries to explore the schema.',
              style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 24),

            // Connection card
            _buildDatabaseConnectionStatus(state),
            const SizedBox(height: 24),

            // Quick templates
            const Text('Quick Query Templates:', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Color(0xFF475569))),
            const SizedBox(height: 8),
            Wrap(
              children: [
                _buildQuickQueryButton('Customers List', 'SELECT customer_id, name, age, region, total_spent FROM customers LIMIT 10;'),
                _buildQuickQueryButton('Top Revenue Products', 'SELECT product_name, category, price, stock_quantity FROM products ORDER BY price DESC LIMIT 5;'),
                _buildQuickQueryButton('Cancelled Orders Breakdown', "SELECT order_id, product_name, region, total_amount, status FROM orders WHERE status = 'Cancelled' LIMIT 5;"),
                _buildQuickQueryButton('Region Spending Summary', "SELECT region, COUNT(order_id) as orders, SUM(total_amount) as sales FROM orders GROUP BY region ORDER BY sales DESC;"),
              ],
            ),
            const SizedBox(height: 20),

            // SQL editor input card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Draft SELECT Query', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _sqlController,
                      maxLines: 4,
                      style: const TextStyle(fontFamily: 'Courier', fontSize: 13, fontWeight: FontWeight.bold),
                      decoration: InputDecoration(
                        hintText: 'SELECT * FROM customers...',
                        filled: true,
                        fillColor: const Color(0xFFF8FAFC),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: 16),
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
                          icon: const Icon(Icons.play_arrow_rounded),
                          label: const Text('Execute SQL', style: TextStyle(fontWeight: FontWeight.bold)),
                          onPressed: !state.isDBConnected || state.isSqlLoading
                              ? null
                              : () async {
                                  await state.executeSQL(_sqlController.text);
                                },
                        ),
                        if (state.isSqlLoading) ...[
                          const SizedBox(width: 16),
                          const CircularProgressIndicator(),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Result set list
            if (state.sqlColumns.isNotEmpty) ...[
              const Text('Query Results', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: SingleChildScrollView(
                        child: DataTable(
                          headingRowColor: MaterialStateProperty.all(const Color(0xFFF8FAFC)),
                          columns: state.sqlColumns.map((col) => DataColumn(label: Text(col, style: const TextStyle(fontWeight: FontWeight.bold)))).toList(),
                          rows: state.sqlRows.map<DataRow>((row) {
                            return DataRow(
                              cells: state.sqlColumns.map<DataCell>((col) {
                                final val = row[col];
                                return DataCell(Text(val == null ? 'Null' : val.toString()));
                              }).toList(),
                            );
                          }).toList(),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
