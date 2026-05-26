import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AppState extends ChangeNotifier {
  // ─── Authentication States ──────────────────────────────────────────────────
  bool _isAuthenticated = false;
  String _username = '';
  String _role = '';
  bool _isAuthLoading = true;

  bool get isAuthenticated => _isAuthenticated;
  String get username => _username;
  String get role => _role;
  bool get isAuthLoading => _isAuthLoading;

  // ─── Data Clean States ──────────────────────────────────────────────────────
  bool _hasActiveDataset = false;
  Map<String, dynamic> _cleanStats = {};
  Map<String, dynamic> _origStats = {};
  List<String> _columns = [];
  Map<String, String> _dtypes = {};
  List<dynamic> _missingReport = [];
  List<dynamic> _previewRows = [];
  bool _isDataLoading = false;

  bool get hasActiveDataset => _hasActiveDataset;
  Map<String, dynamic> get cleanStats => _cleanStats;
  Map<String, dynamic> get origStats => _origStats;
  List<String> get columns => _columns;
  Map<String, String> get dtypes => _dtypes;
  List<dynamic> get missingReport => _missingReport;
  List<dynamic> get previewRows => _previewRows;
  bool get isDataLoading => _isDataLoading;

  // ─── Database States ────────────────────────────────────────────────────────
  bool _isDBConnected = false;
  Map<String, dynamic> _dbConfig = {};
  Map<String, dynamic> _dbKpis = {};
  List<dynamic> _dbRecentOrders = [];
  List<dynamic> _dbMonthlySales = [];
  List<dynamic> _dbRegionalSales = [];
  List<dynamic> _dbCategoryPerformance = [];
  
  List<String> _sqlColumns = [];
  List<dynamic> _sqlRows = [];
  bool _isSqlLoading = false;

  bool get isDBConnected => _isDBConnected;
  Map<String, dynamic> get dbConfig => _dbConfig;
  Map<String, dynamic> get dbKpis => _dbKpis;
  List<dynamic> get dbRecentOrders => _dbRecentOrders;
  List<dynamic> get dbMonthlySales => _dbMonthlySales;
  List<dynamic> get dbRegionalSales => _dbRegionalSales;
  List<dynamic> get dbCategoryPerformance => _dbCategoryPerformance;
  List<String> get sqlColumns => _sqlColumns;
  List<dynamic> get sqlRows => _sqlRows;
  bool get isSqlLoading => _isSqlLoading;

  // ─── Machine Learning States ────────────────────────────────────────────────
  bool _isMlLoading = false;
  bool get isMlLoading => _isMlLoading;

  // Sales
  double _salesR2 = 0.0;
  double _salesMae = 0.0;
  List<dynamic> _salesHistorical = [];
  List<dynamic> _salesForecast = [];

  double get salesR2 => _salesR2;
  double get salesMae => _salesMae;
  List<dynamic> get salesHistorical => _salesHistorical;
  List<dynamic> get salesForecast => _salesForecast;

  // Churn
  double _churnAccuracy = 0.0;
  double _churnRate = 0.0;
  int _churnTrainSize = 0;
  List<dynamic> _churnConfusionMatrix = [];
  List<dynamic> _churnFeatureImportance = [];
  List<double> _churnProbDistribution = [];

  double get churnAccuracy => _churnAccuracy;
  double get churnRate => _churnRate;
  int get churnTrainSize => _churnTrainSize;
  List<dynamic> get churnConfusionMatrix => _churnConfusionMatrix;
  List<dynamic> get churnFeatureImportance => _churnFeatureImportance;
  List<double> get churnProbDistribution => _churnProbDistribution;

  // Segmentation
  int _segNClusters = 0;
  int _segTotalSegmented = 0;
  List<dynamic> _segClusterDistribution = [];
  List<dynamic> _segScatterData = [];
  List<dynamic> _segSummary = [];

  int get segNClusters => _segNClusters;
  int get segTotalSegmented => _segTotalSegmented;
  List<dynamic> get segClusterDistribution => _segClusterDistribution;
  List<dynamic> get segScatterData => _segScatterData;
  List<dynamic> get segSummary => _segSummary;

  // ─── Reports States ─────────────────────────────────────────────────────────
  String _repPeriod = 'All Time';
  String _repRegion = 'All Regions';
  String _repCategory = 'All Categories';
  Map<String, dynamic> _repKpis = {};
  List<dynamic> _repMonthlySales = [];
  List<dynamic> _repCategoryPerf = [];
  List<String> _repFilterRegions = ['All Regions'];
  List<String> _repFilterCategories = ['All Categories'];
  bool _isRepLoading = false;

  String get repPeriod => _repPeriod;
  String get repRegion => _repRegion;
  String get repCategory => _repCategory;
  Map<String, dynamic> get repKpis => _repKpis;
  List<dynamic> get repMonthlySales => _repMonthlySales;
  List<dynamic> get repCategoryPerf => _repCategoryPerf;
  List<String> get repFilterRegions => _repFilterRegions;
  List<String> get repFilterCategories => _repFilterCategories;
  bool get isRepLoading => _isRepLoading;


  AppState() {
    _loadStoredAuth();
  }

  // ─── Auth Action Methods ────────────────────────────────────────────────────
  Future<void> _loadStoredAuth() async {
    final token = await ApiService.getToken();
    if (token != null) {
      try {
        final res = await ApiService.get('/auth/verify');
        if (res.statusCode == 200) {
          final data = jsonDecode(res.body);
          _isAuthenticated = true;
          _username = data['username'] ?? '';
          _role = data['role'] ?? 'Viewer';
        } else {
          await ApiService.clearAuth();
        }
      } catch (e) {
        // API offline, keep cached token but assume authenticated
        _isAuthenticated = false;
      }
    }
    _isAuthLoading = false;
    notifyListeners();
  }

  Future<bool> login(String username, String password) async {
    _isAuthLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/auth/login', {
        'username': username,
        'password': password,
      });

      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        await ApiService.saveToken(
          data['access_token'],
          data['username'],
          data['role'],
        );
        _isAuthenticated = true;
        _username = data['username'];
        _role = data['role'];
        _isAuthLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Login exception: $e');
    }
    _isAuthLoading = false;
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await ApiService.clearAuth();
    _isAuthenticated = false;
    _username = '';
    _role = '';
    _hasActiveDataset = false;
    _cleanStats = {};
    _origStats = {};
    notifyListeners();
  }

  // ─── File Upload & Cleaning Action Methods ──────────────────────────────────
  Future<bool> uploadDataset(Uint8List fileBytes, String fileName) async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.uploadFile('/data/upload', fileBytes, fileName);
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        _origStats = data['stats']; // Sets both on initial upload
        _columns = List<String>.from(data['columns']);
        _dtypes = Map<String, String>.from(data['dtypes']);
        _missingReport = data['missing_report'] ?? [];
        _previewRows = data['preview'] ?? [];
        _hasActiveDataset = true;
        _isDataLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Upload error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
    return false;
  }

  Future<void> fetchDatasetStats() async {
    if (!_hasActiveDataset) return;
    try {
      final res = await ApiService.get('/data/stats');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _origStats = data['original'];
        _cleanStats = data['clean'];
        _missingReport = data['missing_report'] ?? [];
        notifyListeners();
      }
    } catch (e) {
      debugPrint('Stats fetch error: $e');
    }
  }

  Future<bool> dropNullRows() async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/data/clean/nulls/drop', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        await _fetchPreview();
        await fetchDatasetStats();
        _isDataLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Drop nulls error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> fillNullRows(String strategy) async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/data/clean/nulls/fill?strategy=$strategy', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        await _fetchPreview();
        await fetchDatasetStats();
        _isDataLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Fill nulls error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> removeDuplicateRows() async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/data/clean/duplicates/remove', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        await _fetchPreview();
        await fetchDatasetStats();
        _isDataLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Remove duplicates error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> convertTypes(Map<String, String> conversions) async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/data/clean/types/convert', {'conversions': conversions});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        await _fetchPreview();
        await fetchDatasetStats();
        _isDataLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Convert types error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> selectFeatures(List<String> activeCols) async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/data/clean/features/select', {'columns': activeCols});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        _columns = List<String>.from(activeCols);
        await _fetchPreview();
        await fetchDatasetStats();
        _isDataLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Select columns error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
    return false;
  }

  Future<void> resetDataset() async {
    _isDataLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/data/clean/reset', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _cleanStats = data['stats'];
        await _fetchPreview();
        await fetchDatasetStats();
      }
    } catch (e) {
      debugPrint('Reset error: $e');
    }
    _isDataLoading = false;
    notifyListeners();
  }

  Future<void> _fetchPreview() async {
    try {
      final res = await ApiService.get('/data/preview');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _previewRows = data['preview'] ?? [];
        _dtypes = Map<String, String>.from(data['dtypes']);
      }
    } catch (e) {
      debugPrint('Preview fetch error: $e');
    }
  }

  // ─── Database Action Methods ────────────────────────────────────────────────
  Future<bool> testDatabaseConnection() async {
    try {
      final res = await ApiService.post('/database/connect', {});
      if (res.statusCode == 200) {
        _isDBConnected = true;
        await _fetchDBConfig();
        await fetchDBDashboardKPIs();
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('DB connect error: $e');
    }
    _isDBConnected = false;
    notifyListeners();
    return false;
  }

  Future<void> seedMockDBData() async {
    try {
      await ApiService.post('/database/load-mock-data', {});
      await fetchDBDashboardKPIs();
    } catch (e) {
      debugPrint('Seeding failed: $e');
    }
  }

  Future<void> _fetchDBConfig() async {
    try {
      final res = await ApiService.get('/database/config');
      if (res.statusCode == 200) {
        _dbConfig = jsonDecode(res.body);
      }
    } catch (e) {
      debugPrint('DB Config fetch failed: $e');
    }
  }

  Future<void> fetchDBDashboardKPIs() async {
    try {
      final res = await ApiService.get('/database/dashboard-kpis');
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _dbKpis = data['kpis'] ?? {};
        _dbRecentOrders = data['recent_orders'] ?? [];
        _dbMonthlySales = data['monthly_sales'] ?? [];
        _dbRegionalSales = data['regional_sales'] ?? [];
        _dbCategoryPerformance = data['category_performance'] ?? [];
        notifyListeners();
      }
    } catch (e) {
      debugPrint('DB KPIs failed: $e');
    }
  }

  Future<bool> executeSQL(String query) async {
    _isSqlLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/database/query', {'sql': query});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _sqlColumns = List<String>.from(data['columns'] ?? []);
        _sqlRows = data['rows'] ?? [];
        _isSqlLoading = false;
        notifyListeners();
        return true;
      } else {
        final err = jsonDecode(res.body);
        throw Exception(err['detail'] ?? 'Execution failed');
      }
    } catch (e) {
      _isSqlLoading = false;
      _sqlColumns = ['Error'];
      _sqlRows = [{'Error': e.toString().replaceAll('Exception:', '')}];
      notifyListeners();
    }
    return false;
  }

  // ─── Machine Learning Action Methods ────────────────────────────────────────
  Future<bool> trainSalesForecast(int forecastMonths) async {
    _isMlLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/ml/sales/train?forecast_months=$forecastMonths', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _salesR2 = (data['r2'] ?? 0.0).toDouble();
        _salesMae = (data['mae'] ?? 0.0).toDouble();
        _salesHistorical = data['historical'] ?? [];
        _salesForecast = data['forecast'] ?? [];
        _isMlLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Sales train error: $e');
    }
    _isMlLoading = false;
    notifyListeners();
    return false;
  }

  Future<bool> trainChurnModel(int trees) async {
    _isMlLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/ml/churn/train?n_estimators=$trees', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _churnAccuracy = (data['accuracy'] ?? 0.0).toDouble();
        _churnRate = (data['churn_rate'] ?? 0.0).toDouble();
        _churnTrainSize = data['train_size'] ?? 0;
        _churnConfusionMatrix = data['confusion_matrix'] ?? [];
        _churnFeatureImportance = data['feature_importances'] ?? [];
        _churnProbDistribution = List<double>.from((data['probability_distribution'] ?? []).map((e) => (e as num).toDouble()));
        _isMlLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Churn train error: $e');
    }
    _isMlLoading = false;
    notifyListeners();
    return false;
  }

  Future<Map<String, dynamic>?> predictSingleChurnRisk(
    double freq, double aov, double daysAgo, double tickets, double satisfaction, double spend
  ) async {
    try {
      final res = await ApiService.post('/ml/churn/predict', {
        'purchase_frequency': freq,
        'avg_order_value': aov,
        'last_purchase_days_ago': daysAgo,
        'support_tickets': tickets,
        'satisfaction_score': satisfaction,
        'total_spent': spend
      });
      if (res.statusCode == 200) {
        return jsonDecode(res.body);
      }
    } catch (e) {
      debugPrint('Single churn prediction failed: $e');
    }
    return null;
  }

  Future<bool> runCustomerSegmentation(int k) async {
    _isMlLoading = true;
    notifyListeners();
    try {
      final res = await ApiService.post('/ml/segmentation?n_clusters=$k', {});
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _segNClusters = data['n_clusters'] ?? 0;
        _segTotalSegmented = data['total_segmented'] ?? 0;
        _segClusterDistribution = data['cluster_distribution'] ?? [];
        _segScatterData = data['scatter_data'] ?? [];
        _segSummary = data['segment_summary'] ?? [];
        _isMlLoading = false;
        notifyListeners();
        return true;
      }
    } catch (e) {
      debugPrint('Clustering train error: $e');
    }
    _isMlLoading = false;
    notifyListeners();
    return false;
  }

  // ─── Reports Action Methods ─────────────────────────────────────────────────
  Future<void> fetchReportSummary({String? period, String? region, String? category}) async {
    _isRepLoading = true;
    notifyListeners();
    
    if (period != null) _repPeriod = period;
    if (region != null) _repRegion = region;
    if (category != null) _repCategory = category;

    try {
      final res = await ApiService.get(
        '/reports/summary?period=${Uri.encodeComponent(_repPeriod)}&region=${Uri.encodeComponent(_repRegion)}&category=${Uri.encodeComponent(_repCategory)}'
      );
      if (res.statusCode == 200) {
        final data = jsonDecode(res.body);
        _repKpis = data['kpis'] ?? {};
        _repMonthlySales = data['monthly_sales'] ?? [];
        _repCategoryPerf = data['category_performance'] ?? [];
        _repFilterRegions = List<String>.from(data['regions'] ?? ['All Regions']);
        _repFilterCategories = List<String>.from(data['categories'] ?? ['All Categories']);
      }
    } catch (e) {
      debugPrint('Report Summary failed: $e');
    }
    _isRepLoading = false;
    notifyListeners();
  }
}
