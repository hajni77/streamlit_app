import 'package:flutter/material.dart';
import 'bathroom_layout_widget.dart';

/// A screen that displays detailed information about a generated bathroom layout
class BathroomLayoutDetailsScreen extends StatelessWidget {
  /// The layout data from the API
  final Map<String, dynamic> layoutData;

  /// Constructor
  const BathroomLayoutDetailsScreen({
    Key? key, 
    required this.layoutData,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Layout Details'),
        actions: [
          IconButton(
            icon: const Icon(Icons.save),
            tooltip: 'Save Layout',
            onPressed: () {
              // TODO: Implement save functionality
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Layout saved'))
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Layout information card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Layout Information', style: Theme.of(context).textTheme.headline6),
                    const SizedBox(height: 8),
                    _buildInfoRow('Room Dimensions', '${layoutData['room_width']}×${layoutData['room_depth']}×${layoutData['room_height']} cm'),
                    _buildInfoRow('Score', layoutData['score'].toString()),
                    _buildInfoRow('Processing Time', '${layoutData['processing_time'].toStringAsFixed(2)}s'),
                    _buildInfoRow('Layout ID', layoutData['layout_id']),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // Layout visualization
            Text('Layout Visualization', style: Theme.of(context).textTheme.headline6),
            const SizedBox(height: 8),
            Container(
              height: 400,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey),
              ),
              child: BathroomLayoutWidget(layoutData: layoutData),
            ),
            
            // Score breakdown
            if (layoutData['score_breakdown'] != null) ...[
              const SizedBox(height: 16),
              Text('Score Breakdown', style: Theme.of(context).textTheme.headline6),
              const SizedBox(height: 8),
              _buildScoreBreakdown(),
            ],
            
            // List of objects
            const SizedBox(height: 16),
            Text('Placed Objects', style: Theme.of(context).textTheme.headline6),
            const SizedBox(height: 8),
            _buildObjectsList(),
            
            const SizedBox(height: 24),
            
            // Action buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                ElevatedButton.icon(
                  icon: const Icon(Icons.refresh),
                  label: const Text('Generate New'),
                  onPressed: () {
                    Navigator.pop(context);
                  },
                ),
                ElevatedButton.icon(
                  icon: const Icon(Icons.share),
                  label: const Text('Share'),
                  onPressed: () {
                    // TODO: Implement share functionality
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Sharing not implemented yet'))
                    );
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
          Text(value),
        ],
      ),
    );
  }

  Widget _buildScoreBreakdown() {
    final scoreBreakdown = Map<String, dynamic>.from(layoutData['score_breakdown']);
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: scoreBreakdown.entries.map((entry) {
            final criterionName = entry.key;
            final score = entry.value is double ? entry.value.toDouble() : (entry.value as num).toDouble();
            
            return Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  _formatCriterionName(criterionName),
                  style: const TextStyle(fontSize: 14),
                ),
                Row(
                  children: [
                    Container(
                      width: 100,
                      height: 10,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(5),
                        color: Colors.grey[300],
                      ),
                      child: FractionallySizedBox(
                        alignment: Alignment.centerLeft,
                        widthFactor: score / 10.0, // Assuming scores are out of 10
                        child: Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(5),
                            color: _getScoreColor(score),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      score.toStringAsFixed(1),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildObjectsList() {
    final objects = List<Map<String, dynamic>>.from(layoutData['objects']);
    
    return Card(
      child: ListView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: objects.length,
        itemBuilder: (context, index) {
          final object = objects[index];
          return ListTile(
            title: Text(
              _formatCriterionName(object['object_type']),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            subtitle: Text(
              'Size: ${object['width']}×${object['depth']} cm, Position: [${object['position'][0]}, ${object['position'][1]}]',
            ),
            leading: Icon(_getObjectIcon(object['object_type'])),
          );
        },
      ),
    );
  }

  String _formatCriterionName(String name) {
    // Convert snake_case to Title Case
    return name.split('_').map((word) => word.substring(0, 1).toUpperCase() + word.substring(1)).join(' ');
  }

  Color _getScoreColor(double score) {
    if (score >= 8) return Colors.green;
    if (score >= 5) return Colors.orange;
    return Colors.red;
  }

  IconData _getObjectIcon(String objectType) {
    switch (objectType.toLowerCase()) {
      case 'toilet':
        return Icons.wc;
      case 'sink':
      case 'double_sink':
        return Icons.wash;
      case 'bathtub':
        return Icons.bathtub;
      case 'shower':
        return Icons.shower;
      case 'bidet':
        return Icons.water_drop;
      case 'washing_machine':
        return Icons.local_laundry_service;
      default:
        return Icons.square_foot;
    }
  }
}
