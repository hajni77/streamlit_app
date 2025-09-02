# Bathroom Layout Generator - Flutter Integration Example

This directory contains example code showing how to integrate the Bathroom Layout Generator API with a Flutter application.

## Files Overview

- `bathroom_api_client.dart` - API client class for making requests to the bathroom layout generator API
- `bathroom_layout_widget.dart` - Widget for visualizing bathroom layouts in Flutter
- `bathroom_layout_screen.dart` - Complete UI screen for generating and displaying bathroom layouts

## Integration Steps

1. Add these files to your Flutter project.

2. Add the required dependencies to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^0.13.5  # For API requests
```

3. Import and use the components in your app:

```dart
import 'package:flutter/material.dart';
import 'package:your_app/bathroom_layout_screen.dart';

void main() {
  runApp(MaterialApp(
    title: 'Bathroom Layout Generator',
    theme: ThemeData(
      primarySwatch: Colors.blue,
      visualDensity: VisualDensity.adaptivePlatformDensity,
    ),
    home: BathroomLayoutScreen(),
  ));
}
```

## API Configuration

Make sure to configure the API base URL in `bathroom_layout_screen.dart`:

```dart
final BathroomApiClient _apiClient = BathroomApiClient(
  baseUrl: 'http://your-api-url:8000', // Change this to your API URL
);
```

## Usage Example

The `BathroomLayoutScreen` provides a complete UI for:

1. Setting bathroom dimensions
2. Selecting fixtures to place
3. Adding windows and doors
4. Generating optimized layouts
5. Visualizing the results with score breakdowns

For more customized usage, you can use the components individually:

### API Client Only

```dart
final apiClient = BathroomApiClient(baseUrl: 'http://your-api-url:8000');

// Generate a layout
try {
  final layoutData = await apiClient.generateLayout(
    roomWidth: 300,
    roomDepth: 240,
    objectsToPlace: ['toilet', 'sink', 'shower'],
  );
  print('Layout generated with ID: ${layoutData['layout_id']}');
} catch (e) {
  print('Error: $e');
}
```

### Layout Widget Only

```dart
// Assuming you have layout data from the API
Widget buildLayout(Map<String, dynamic> layoutData) {
  return Container(
    width: 400,
    height: 300,
    child: BathroomLayoutWidget(
      layoutData: layoutData,
      // Optional custom colors
      objectColors: {
        'toilet': Colors.grey[200]!,
        'shower': Colors.blue[300]!,
      },
    ),
  );
}
```

## Performance Considerations

1. Layout generation may take several seconds depending on the complexity of the request.
   Consider displaying a loading indicator during API calls.

2. The visualization widget scales to fit the available container space.

3. For large bathrooms with many fixtures, consider increasing the parent container size
   to ensure details are visible.

## Error Handling

The provided components include error handling for:

- API connectivity issues
- Invalid layout generation requests
- Server-side errors

Custom error handling can be implemented by catching exceptions from the API client.
