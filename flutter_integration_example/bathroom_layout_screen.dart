import 'package:flutter/material.dart';
import 'dart:convert';
import 'bathroom_api_client.dart';
import 'bathroom_layout_widget.dart';
import 'bathroom_layout_details_screen.dart';

/// A screen that demonstrates generating and displaying bathroom layouts
class BathroomLayoutScreen extends StatefulWidget {
  const BathroomLayoutScreen({Key? key}) : super(key: key);

  @override
  _BathroomLayoutScreenState createState() => _BathroomLayoutScreenState();
}

class _BathroomLayoutScreenState extends State<BathroomLayoutScreen> {
  // API client
  final BathroomApiClient _apiClient = BathroomApiClient(
    baseUrl: 'http://localhost:8000', // Change this to your API URL
  );
  
  // Form values
  final _formKey = GlobalKey<FormState>();
  double _roomWidth = 300;
  double _roomDepth = 240;
  double _roomHeight = 280;
  final List<String> _selectedObjects = ['toilet', 'sink', 'shower'];
  final List<Map<String, dynamic>> _windowsDoors = [];
  
  // State variables
  bool _isLoading = false;
  Map<String, dynamic>? _layoutData;
  String? _errorMessage;
  
  @override
  void initState() {
    super.initState();
    _checkApiHealth();
  }
  
  Future<void> _checkApiHealth() async {
    try {
      final isHealthy = await _apiClient.checkHealth();
      if (!isHealthy) {
        setState(() {
          _errorMessage = 'API server is not responding correctly';
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Could not connect to API server';
      });
    }
  }
  
  Future<void> _generateLayout() async {
    // Add null check to avoid _TypeError when form state is null
    if (_formKey.currentState == null || !_formKey.currentState!.validate()) {
      return;
    }
    
    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _layoutData = null;
    });
    
    try {
      final layout = await _apiClient.generateLayout(
        roomWidth: _roomWidth,
        roomDepth: _roomDepth,
        roomHeight: _roomHeight,
        objectsToPlace: _selectedObjects,
        windowsDoors: _windowsDoors,
      );
      
      setState(() {
        _layoutData = layout;
        _isLoading = false;
      });
      
      // Navigate to the details screen with the layout data
      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (context) => BathroomLayoutDetailsScreen(
            layoutData: layout,
          ),
        ),
      );
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Bathroom Layout Generator'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_errorMessage != null)
              Container(
                padding: const EdgeInsets.all(16.0),
                color: Colors.red[100],
                child: Text(
                  _errorMessage!,
                  style: TextStyle(color: Colors.red[900]),
                ),
              ),
              
            Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Room Dimensions', style: Theme.of(context).textTheme.headline6),
                  SizedBox(height: 8),
                  
                  // Room width input
                  TextFormField(
                    decoration: InputDecoration(
                      labelText: 'Room Width (cm)',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                    initialValue: _roomWidth.toString(),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter room width';
                      }
                      final width = double.tryParse(value);
                      if (width == null || width <= 0) {
                        return 'Please enter a valid room width';
                      }
                      return null;
                    },
                    onChanged: (value) {
                      _roomWidth = double.tryParse(value) ?? _roomWidth;
                    },
                  ),
                  SizedBox(height: 8),
                  
                  // Room depth input
                  TextFormField(
                    decoration: InputDecoration(
                      labelText: 'Room Depth (cm)',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                    initialValue: _roomDepth.toString(),
                    validator: (value) {
                      if (value == null || value.isEmpty) {
                        return 'Please enter room depth';
                      }
                      final depth = double.tryParse(value);
                      if (depth == null || depth <= 0) {
                        return 'Please enter a valid room depth';
                      }
                      return null;
                    },
                    onChanged: (value) {
                      _roomDepth = double.tryParse(value) ?? _roomDepth;
                    },
                  ),
                  SizedBox(height: 16),
                  
                  Text('Objects to Place', style: Theme.of(context).textTheme.headline6),
                  SizedBox(height: 8),
                  
                  // Object selection checkboxes
                  _buildObjectSelectionCheckboxes(),
                  SizedBox(height: 16),
                  
                  // Add door/window button
                  ElevatedButton.icon(
                    icon: Icon(Icons.add),
                    label: Text('Add Door/Window'),
                    onPressed: _showAddWindowDoorDialog,
                  ),
                  
                  if (_windowsDoors.isNotEmpty) ...[
                    SizedBox(height: 8),
                    Text('Windows and Doors', style: Theme.of(context).textTheme.subtitle1),
                    SizedBox(height: 8),
                    Column(children: _buildWindowsDoorsList()),
                  ],
                  
                  SizedBox(height: 24),
                  
                  // Generate layout button
                  ElevatedButton(
                    onPressed: _isLoading ? null : () => _generateLayout(),
                    child: _isLoading
                        ? CircularProgressIndicator()
                        : Text('Generate Layout'),
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      minimumSize: Size(double.infinity, 50),
                    ),
                  ),
                ],
              ),
            ),
            
            // Layout display
            if (_layoutData != null) ...[
              SizedBox(height: 24),
              Text('Generated Layout', style: Theme.of(context).textTheme.headline6),
              SizedBox(height: 8),
              Text('Score: ${_layoutData!['score']}'),
              Text('Processing Time: ${_layoutData!['processing_time'].toStringAsFixed(2)}s'),
              SizedBox(height: 16),
              
              // Layout visualization
              Container(
                height: 400,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                ),
                child: BathroomLayoutWidget(layoutData: _layoutData!),
              ),
              
              // Score breakdown
              if (_layoutData!['score_breakdown'] != null) ...[
                SizedBox(height: 16),
                Text('Score Breakdown', style: Theme.of(context).textTheme.subtitle1),
                SizedBox(height: 8),
                _buildScoreBreakdown(),
              ],
              
              // Layout ID
              SizedBox(height: 8),
              Text('Layout ID: ${_layoutData!['layout_id']}', style: TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ],
        ),
      ),
    );
  }
  
  Widget _buildObjectSelectionCheckboxes() {
    // List of available objects
    final availableObjects = [
      'toilet',
      'sink',
      'double_sink',
      'bathtub',
      'shower',
      'bidet',
      'washing_machine',
    ];
    
    return Wrap(
      spacing: 8,
      runSpacing: 4,
      children: availableObjects.map((object) {
        return FilterChip(
          label: Text(object),
          selected: _selectedObjects.contains(object),
          onSelected: (selected) {
            setState(() {
              if (selected) {
                _selectedObjects.add(object);
              } else {
                _selectedObjects.remove(object);
              }
            });
          },
        );
      }).toList(),
    );
  }
  
  List<Widget> _buildWindowsDoorsList() {
    return _windowsDoors.asMap().entries.map((entry) {
      final index = entry.key;
      final item = entry.value;
      
      return ListTile(
        title: Text('${item['name']} (${item['width']} x ${item['depth']} cm)'),
        subtitle: Text('Position: [${item['position'][0]}, ${item['position'][1]}], Wall: ${item['wall']}'),
        trailing: IconButton(
          icon: Icon(Icons.delete),
          onPressed: () {
            setState(() {
              _windowsDoors.removeAt(index);
            });
          },
        ),
      );
    }).toList();
  }
  
  Widget _buildScoreBreakdown() {
    final scoreBreakdown = Map<String, dynamic>.from(_layoutData!['score_breakdown']);
    
    return Container(
      padding: EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
      ),
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
                style: TextStyle(fontSize: 14),
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
                  SizedBox(width: 8),
                  Text(
                    score.toStringAsFixed(1),
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ],
          );
        }).toList(),
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
  
  Future<void> _showAddWindowDoorDialog() async {
    String name = 'door';
    double width = 80;
    double depth = 5;
    double x = 0;
    double y = 0;
    String wall = 'left';
    String? hinge;
    
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Add Window/Door'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Type selection
              DropdownButtonFormField<String>(
                decoration: InputDecoration(labelText: 'Type'),
                value: name,
                items: ['door', 'window'].map((item) {
                  return DropdownMenuItem<String>(
                    value: item,
                    child: Text(item),
                  );
                }).toList(),
                onChanged: (value) {
                  name = value ?? name;
                  // Reset hinge if window is selected
                  if (value == 'window') {
                    hinge = null;
                  }
                },
              ),
              
              // Dimensions
              TextFormField(
                decoration: InputDecoration(labelText: 'Width (cm)'),
                keyboardType: TextInputType.number,
                initialValue: width.toString(),
                onChanged: (value) {
                  width = double.tryParse(value) ?? width;
                },
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Depth (cm)'),
                keyboardType: TextInputType.number,
                initialValue: depth.toString(),
                onChanged: (value) {
                  depth = double.tryParse(value) ?? depth;
                },
              ),
              
              // Position
              TextFormField(
                decoration: InputDecoration(labelText: 'Position X (cm)'),
                keyboardType: TextInputType.number,
                initialValue: x.toString(),
                onChanged: (value) {
                  x = double.tryParse(value) ?? x;
                },
              ),
              TextFormField(
                decoration: InputDecoration(labelText: 'Position Y (cm)'),
                keyboardType: TextInputType.number,
                initialValue: y.toString(),
                onChanged: (value) {
                  y = double.tryParse(value) ?? y;
                },
              ),
              
              // Wall
              DropdownButtonFormField<String>(
                decoration: InputDecoration(labelText: 'Wall'),
                value: wall,
                items: ['left', 'right', 'top', 'bottom'].map((item) {
                  return DropdownMenuItem<String>(
                    value: item,
                    child: Text(item),
                  );
                }).toList(),
                onChanged: (value) {
                  wall = value ?? wall;
                },
              ),
              
              // Hinge (only for doors)
              if (name == 'door')
                DropdownButtonFormField<String>(
                  decoration: InputDecoration(labelText: 'Hinge Side'),
                  value: hinge ?? 'left',
                  items: ['left', 'right', 'top', 'bottom'].map((item) {
                    return DropdownMenuItem<String>(
                      value: item,
                      child: Text(item),
                    );
                  }).toList(),
                  onChanged: (value) {
                    hinge = value;
                  },
                ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              final windowDoor = {
                'name': name,
                'position': [x, y],
                'width': width,
                'depth': depth,
                'height': name == 'door' ? 210.0 : 120.0,
                'wall': wall,
              };
              
              if (name == 'door' && hinge != null) {
                windowDoor['hinge'] = hinge;
              }
              
              setState(() {
                _windowsDoors.add(windowDoor);
              });
              
              Navigator.pop(context);
            },
            child: Text('Add'),
          ),
        ],
      ),
    );
  }
}
