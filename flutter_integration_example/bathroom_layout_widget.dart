import 'package:flutter/material.dart';
import 'dart:math' as math;

/// A widget that displays a bathroom layout
class BathroomLayoutWidget extends StatelessWidget {
  /// The layout data from the API
  final Map<String, dynamic> layoutData;
  
  /// Optional color scheme
  final Map<String, Color>? objectColors;
  
  /// Constructor
  const BathroomLayoutWidget({
    Key? key,
    required this.layoutData,
    this.objectColors,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final roomWidth = layoutData['room_width'].toDouble();
    final roomDepth = layoutData['room_depth'].toDouble();
    final objects = List<Map<String, dynamic>>.from(layoutData['objects']);
    
    return LayoutBuilder(
      builder: (context, constraints) {
        // Calculate the scale factor to fit the room in the available space
        final scale = math.min(
          constraints.maxWidth / roomWidth,
          constraints.maxHeight / roomDepth
        );
        
        // Calculate the size of the room in pixels
        final roomWidthPx = roomWidth * scale;
        final roomDepthPx = roomDepth * scale;
        
        return Container(
          width: roomWidthPx,
          height: roomDepthPx,
          decoration: BoxDecoration(
            color: Colors.grey[200],
            border: Border.all(color: Colors.black),
          ),
          child: Stack(
            children: [
              // Draw the room boundary
              Positioned.fill(
                child: CustomPaint(
                  painter: RoomPainter(
                    roomWidth: roomWidth,
                    roomDepth: roomDepth,
                    scale: scale,
                  ),
                ),
              ),
              
              // Draw each object
              ...objects.map((object) {
                final x = object['position'][0].toDouble();
                final y = object['position'][1].toDouble();
                final width = object['width'].toDouble();
                final depth = object['depth'].toDouble();
                final objectType = object['object_type'];
                
                // Scale the coordinates and size
                final scaledX = x * scale;
                final scaledY = y * scale;
                final scaledWidth = width * scale;
                final scaledDepth = depth * scale;
                
                // Get the color for this object type
                final color = objectColors != null && objectColors!.containsKey(objectType) 
                    ? objectColors![objectType]! 
                    : getDefaultColor(objectType);
                
                return Positioned(
                  left: scaledX,
                  top: scaledY,
                  child: ObjectWidget(
                    objectType: objectType,
                    width: scaledWidth,
                    depth: scaledDepth,
                    color: color,
                  ),
                );
              }).toList(),
              
              // Draw labels for objects if needed
              if (layoutData['show_labels'] == true) 
                ...objects.map((object) {
                  final x = object['position'][0].toDouble();
                  final y = object['position'][1].toDouble();
                  final width = object['width'].toDouble();
                  final depth = object['depth'].toDouble();
                  final objectType = object['object_type'];
                  
                  final scaledX = x * scale;
                  final scaledY = y * scale;
                  final scaledWidth = width * scale;
                  final scaledDepth = depth * scale;
                  
                  return Positioned(
                    left: scaledX + scaledWidth / 2,
                    top: scaledY + scaledDepth / 2,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      color: Colors.white.withOpacity(0.7),
                      child: Text(
                        objectType,
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  );
                }).toList(),
            ],
          ),
        );
      },
    );
  }
  
  /// Get a default color based on object type
  Color getDefaultColor(String objectType) {
    switch (objectType.toLowerCase()) {
      case 'toilet':
        return Colors.white;
      case 'sink':
      case 'double_sink':
        return Colors.lightBlue[100]!;
      case 'bathtub':
        return Colors.blue[200]!;
      case 'shower':
        return Colors.blue[300]!;
      case 'bidet':
        return Colors.grey[300]!;
      case 'washing_machine':
        return Colors.grey[400]!;
      default:
        return Colors.amber[100]!;
    }
  }
}

/// Custom painter for the room outline
class RoomPainter extends CustomPainter {
  final double roomWidth;
  final double roomDepth;
  final double scale;
  
  RoomPainter({
    required this.roomWidth, 
    required this.roomDepth,
    required this.scale,
  });
  
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;
    
    // Draw the room outline
    canvas.drawRect(
      Rect.fromLTWH(0, 0, roomWidth * scale, roomDepth * scale),
      paint,
    );
    
    // Optional: Draw a grid
    final gridPaint = Paint()
      ..color = Colors.grey[300]!
      ..strokeWidth = 0.5;
    
    final gridSize = 50.0; // Grid size in cm
    final scaledGridSize = gridSize * scale;
    
    // Draw vertical grid lines
    for (double x = scaledGridSize; x < roomWidth * scale; x += scaledGridSize) {
      canvas.drawLine(
        Offset(x, 0),
        Offset(x, roomDepth * scale),
        gridPaint,
      );
    }
    
    // Draw horizontal grid lines
    for (double y = scaledGridSize; y < roomDepth * scale; y += scaledGridSize) {
      canvas.drawLine(
        Offset(0, y),
        Offset(roomWidth * scale, y),
        gridPaint,
      );
    }
  }
  
  @override
  bool shouldRepaint(RoomPainter oldDelegate) {
    return oldDelegate.roomWidth != roomWidth || 
           oldDelegate.roomDepth != roomDepth ||
           oldDelegate.scale != scale;
  }
}

/// Widget to draw a bathroom object
class ObjectWidget extends StatelessWidget {
  final String objectType;
  final double width;
  final double depth;
  final Color color;
  
  const ObjectWidget({
    Key? key,
    required this.objectType,
    required this.width,
    required this.depth,
    required this.color,
  }) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      height: depth,
      decoration: BoxDecoration(
        color: color,
        border: Border.all(color: Colors.black),
        borderRadius: BorderRadius.circular(4),
      ),
      child: CustomPaint(
        painter: ObjectIconPainter(objectType: objectType),
      ),
    );
  }
}

/// Custom painter for object icons
class ObjectIconPainter extends CustomPainter {
  final String objectType;
  
  ObjectIconPainter({required this.objectType});
  
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.black
      ..strokeWidth = 1.0
      ..style = PaintingStyle.stroke;
    
    // Draw a simple icon based on object type
    switch (objectType.toLowerCase()) {
      case 'toilet':
        _drawToilet(canvas, size, paint);
        break;
      case 'sink':
        _drawSink(canvas, size, paint);
        break;
      case 'double_sink':
        _drawDoubleSink(canvas, size, paint);
        break;
      case 'bathtub':
        _drawBathtub(canvas, size, paint);
        break;
      case 'shower':
        _drawShower(canvas, size, paint);
        break;
      case 'bidet':
        _drawBidet(canvas, size, paint);
        break;
      case 'washing_machine':
        _drawWashingMachine(canvas, size, paint);
        break;
    }
  }
  
  void _drawToilet(Canvas canvas, Size size, Paint paint) {
    // Simple toilet outline
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * 0.4;
    
    // Draw the toilet bowl
    canvas.drawOval(
      Rect.fromCenter(center: center, width: radius * 1.5, height: radius),
      paint,
    );
    
    // Draw the toilet tank
    final tankRect = Rect.fromLTWH(
      center.dx - radius / 2,
      size.height * 0.1,
      radius,
      size.height * 0.3,
    );
    canvas.drawRect(tankRect, paint);
  }
  
  void _drawSink(Canvas canvas, Size size, Paint paint) {
    // Simple sink outline
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * 0.4;
    
    // Draw the sink bowl
    canvas.drawCircle(center, radius, paint);
    
    // Draw the tap
    canvas.drawLine(
      Offset(center.dx, center.dy - radius),
      Offset(center.dx, center.dy - radius * 1.5),
      paint,
    );
    
    // Draw the spout
    canvas.drawArc(
      Rect.fromCenter(
        center: Offset(center.dx, center.dy - radius * 1.5),
        width: radius * 0.8,
        height: radius * 0.8,
      ),
      0, // startAngle
      math.pi, // sweepAngle
      false, // useCenter
      paint,
    );
  }
  
  void _drawDoubleSink(Canvas canvas, Size size, Paint paint) {
    // Double sink outline
    final center1 = Offset(size.width * 0.3, size.height / 2);
    final center2 = Offset(size.width * 0.7, size.height / 2);
    final radius = math.min(size.width, size.height) * 0.25;
    
    // Draw two sink bowls
    canvas.drawCircle(center1, radius, paint);
    canvas.drawCircle(center2, radius, paint);
  }
  
  void _drawBathtub(Canvas canvas, Size size, Paint paint) {
    // Simple bathtub outline
    final rect = Rect.fromLTWH(
      size.width * 0.1,
      size.height * 0.1,
      size.width * 0.8,
      size.height * 0.8,
    );
    
    // Draw the tub with rounded corners
    canvas.drawRRect(
      RRect.fromRectAndRadius(rect, Radius.circular(20)),
      paint,
    );
    
    // Draw water lines
    for (int i = 1; i <= 3; i++) {
      canvas.drawLine(
        Offset(rect.left + rect.width * 0.2, rect.top + rect.height * i / 4),
        Offset(rect.right - rect.width * 0.2, rect.top + rect.height * i / 4),
        paint,
      );
    }
  }
  
  void _drawShower(Canvas canvas, Size size, Paint paint) {
    // Simple shower outline
    final rect = Rect.fromLTWH(
      size.width * 0.1,
      size.height * 0.1,
      size.width * 0.8,
      size.height * 0.8,
    );
    
    // Draw the shower base
    canvas.drawRect(rect, paint);
    
    // Draw the shower head
    final showerHeadCenter = Offset(rect.center.dx, rect.top + rect.height * 0.2);
    canvas.drawCircle(showerHeadCenter, rect.width * 0.15, paint);
    
    // Draw water drops
    final dropsPaint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 1.0;
      
    for (int i = 0; i < 5; i++) {
      final startX = showerHeadCenter.dx - rect.width * 0.1 + i * rect.width * 0.05;
      canvas.drawLine(
        Offset(startX, showerHeadCenter.dy + rect.height * 0.1),
        Offset(startX, showerHeadCenter.dy + rect.height * 0.3),
        dropsPaint,
      );
    }
  }
  
  void _drawBidet(Canvas canvas, Size size, Paint paint) {
    // Simple bidet outline (similar to toilet but smaller)
    final center = Offset(size.width / 2, size.height / 2);
    final radius = math.min(size.width, size.height) * 0.35;
    
    // Draw the bidet bowl
    canvas.drawOval(
      Rect.fromCenter(center: center, width: radius * 1.5, height: radius),
      paint,
    );
    
    // Draw the water spout
    canvas.drawCircle(
      Offset(center.dx, center.dy - radius * 0.2),
      radius * 0.1,
      paint,
    );
  }
  
  void _drawWashingMachine(Canvas canvas, Size size, Paint paint) {
    // Simple washing machine outline
    final rect = Rect.fromLTWH(
      size.width * 0.1,
      size.height * 0.1,
      size.width * 0.8,
      size.height * 0.8,
    );
    
    // Draw the machine body
    canvas.drawRect(rect, paint);
    
    // Draw the door
    final doorCenter = Offset(rect.center.dx, rect.center.dy);
    final doorRadius = rect.width * 0.3;
    canvas.drawCircle(doorCenter, doorRadius, paint);
    
    // Draw the control panel
    final controlRect = Rect.fromLTWH(
      rect.left + rect.width * 0.2,
      rect.top + rect.height * 0.1,
      rect.width * 0.6,
      rect.height * 0.15,
    );
    canvas.drawRect(controlRect, paint);
  }
  
  @override
  bool shouldRepaint(ObjectIconPainter oldDelegate) {
    return oldDelegate.objectType != objectType;
  }
}
