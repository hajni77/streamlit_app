# A Bathroom is a room with a specific size and fixtures
class Bathroom:
    """Represents a bathroom with its dimensions and fixtures."""
    
    def __init__(self, width, depth, height,objects=None,windows_doors=None,object_types=None):
        self.width = width
        self.depth = depth
        self.height = height
        self.objects = objects if objects else []
        self.windows_doors = windows_doors if windows_doors else []
        self.OBJECT_TYPES = object_types
        
        
    def add_object(self, bathroom_object):
        """Add an object to the bathroom."""
        self.objects.append(bathroom_object)
        
    def add_window_door(self, window_door):
        """Add a window or door to the bathroom."""
        self.windows_doors.append(window_door)
        
    def get_placed_objects(self):
        """Get all placed objects."""
        placed_objects = []
        for obj in self.objects:
            # Handle both object instances and dictionaries
            if isinstance(obj, dict):
                if 'position' in obj and obj['position'] is not None:
                    placed_objects.append(obj)
            elif hasattr(obj, 'position') and obj.position is not None:
                placed_objects.append(obj)
        return placed_objects
    def get_placed_objects_name(self):
        """Get all placed objects."""
        placed_objects = []
        for obj in self.objects:
            # Handle both object instances and dictionaries
            if isinstance(obj, dict):
                if 'object' in obj and obj['object'] is not None:
                    placed_objects.append(obj['object'].name)
            elif hasattr(obj, 'object') and obj.object is not None:
                placed_objects.append(obj.object.name)
        return placed_objects
    def get_unplaced_objects(self):
        """Get all unplaced objects."""
        unplaced_objects = []
        for obj in self.objects:
            # Handle both object instances and dictionaries
            if isinstance(obj, dict):
                if 'position' not in obj or obj['position'] is None:
                    unplaced_objects.append(obj)
            elif not hasattr(obj, 'position') or obj.position is None:
                unplaced_objects.append(obj)
        return unplaced_objects
        
    def clear_objects(self):
        """Remove all objects from the bathroom."""
        self.objects = []
        
    def get_size(self):
        """Get the bathroom size."""
        return (self.width, self.depth, self.height)
    
    def get_door_walls(self):
        """Get the walls that have doors."""
        if not self.windows_doors:
            return []
            
        # Check if windows_doors is a list or a single object
        if isinstance(self.windows_doors, list):
            return [wd.wall for wd in self.windows_doors if wd.name.startswith("door")]
        else:
            # Backwards compatibility for single door
            return [self.windows_doors.wall]

    def clone(self):
        """Clone the bathroom."""
        return Bathroom(self.width, self.depth, self.height, self.objects, self.windows_doors, self.OBJECT_TYPES)