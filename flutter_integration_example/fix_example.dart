// INCORRECT way (what's causing the error):
final droppedItems = wallNotifier.getDroppedItems;
debugPrint("Dropped items: $droppedItems");

// CORRECT way (fix):
final droppedItems = wallNotifier.getDroppedItems();
debugPrint("Dropped items: $droppedItems");

/* 
Explanation:
- getDroppedItems is a method that returns List<DroppedItem>
- Without parentheses, it references the function itself, not its return value
- Adding parentheses () calls the method and returns the actual list
*/
