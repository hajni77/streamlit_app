# import object_types from utils
from utils.helpers import get_object_def, convert_values
class BaseObject:
    def __init__(self, object_type, width=None, depth=None, height=None, shadow=None, position=None, wall=None):
        self.object_type = object_type  # Type of object (e.g., 'sink', 'toilet')
        self.name = object_type  # Use object_type as name for compatibility
        self.width = width
        self.depth = depth
        self.height = height
        self.shadow = shadow  # Shadow space (top, right, bottom, left)
        self.position = position  # (x, y) or None if not placed
        self.wall = wall # wall the object is against
        



# A BathroomObject is an object that can be placed in a bathroom
class BathroomObject(BaseObject):
    """Represents a bathroom object with its properties and constraints."""
    
    def __init__(self, object_type, width=None, depth=None, height=None, shadow=None, position=None, wall=None):
        super().__init__(object_type, width, depth, height, shadow, position, wall)
        if wall is not None and shadow is None:
            self.shadow = self.get_shadow_area()
        
    def resize(self, new_size):
        """Resize the object within constraints."""
        min_width, max_width, min_depth, max_depth, min_height, max_height = self.object_type["size_range"]
        new_width, new_depth, new_height = new_size
        
        # Ensure size is within constraints
        self.width = max(min_width, min(max_width, new_width))
        self.depth = max(min_depth, min(max_depth, new_depth))
        self.height = max(min_height, min(max_height, new_height))
        
        return self
    
    def get_footprint(self):
        """Get the footprint (x, y, width, depth) of the object."""
        if self.position is None:
            return None
        return (self.position[0], self.position[1], self.width, self.depth, self.height)
    
    def get_shadow_area(self):
        """Get the area including shadow space."""
        if self.position is None:
            return None
            
        x, y = self.position[0], self.position[1]
        # get shadow from OBJECT_TYPES
        shadow = get_object_def(self.object_type)["shadow_space"]
        _,_,_,_,shadow_top, shadow_left, shadow_right, shadow_bottom = convert_values(self.get_footprint(), shadow, self.wall)
        
        
        return (shadow_top, shadow_left, shadow_right, shadow_bottom)