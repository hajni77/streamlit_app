# validation/room_constraints.py
import utils.helpers

class BaseConstraintValidator:
    """Base validator for object placement constraints."""
    
    def validate_placement(self, obj, position, room):
        """Validate if an object can be placed at the given position.
        
        Args:
            obj: The object to place
            position: (x, y) position tuple
            room: The room object
            
        Returns:
            bool: True if placement is valid, False otherwise
        """
        x, y = position
        
        # Check if position is within room bounds
        if not self._is_within_bounds(x, y, obj, room):
            return False
            
        # Check if position satisfies object's constraints
        if not self._satisfies_constraints(x, y, obj, room):
            return False
            
        # Check if position overlaps with other objects
        if self._overlaps_with_objects(x, y, obj, room):
            return False
            
        # Check if position overlaps with windows/doors
        if self._overlaps_with_windows_doors(x, y, obj, room):
            return False
            
        return True
    
    def validate_object_constraints(self, obj, room):
        """Validate object-specific constraints.
        
        Args:
            obj: The object to validate
            room: The room object
            
        Returns:
            bool: True if object constraints are satisfied, False otherwise
        """
        # Base implementation - can be overridden by subclasses
        return True
        
    def _is_within_bounds(self, x, y, obj, room):
        """Check if position is within room bounds."""
        room_width, room_depth = room.width, room.depth
        
        # Check if object is within room bounds
        if x < 0 or y < 0 or x + obj.width > room_width or y + obj.depth > room_depth:
            return False
        
        return True
        
    def _satisfies_constraints(self, x, y, obj, room):
        """Check if position satisfies object's constraints."""
        # Default implementation - can be overridden by subclasses
        return True
        
    def _overlaps_with_objects(self, x, y, obj, room):
        """Check if position overlaps with other objects."""
        # Check overlap with existing objects
        for placed_obj in room.get_placed_objects():
            if placed_obj == obj:  # Skip the object itself
                continue
                
            placed_x, placed_y = placed_obj.position
            
            # Check for overlap
            if check_overlap((x, y, obj.width, obj.depth), 
                            (placed_x, placed_y, placed_obj.width, placed_obj.depth)):
                return True
                
        return False
        
    def _overlaps_with_windows_doors(self, x, y, obj, room):
        """Check if position overlaps with windows/doors."""
        """
        Validate a complete room layout.
        
        Args:
            room: Room object
            layout: Layout object
            
        Returns:
            bool: Whether the layout is valid
        """
        # Check all objects in the layout
        for obj in room.get_placed_objects():
            if not self.validate_object_placement(obj, room, layout):
                return False
        
        # Check room-specific constraints
        if not self.validate_room_constraints(room, layout):
            return False
        
        return True
    
    def validate_object_placement(self, obj, room, layout=None):
        """
        Validate if an object placement is valid.
        
        Args:
            obj: Object to validate
            room: Room object
            layout: Optional layout object
            
        Returns:
            bool: Whether the placement is valid
        """
        # Check if position is within room bounds
        if not self._is_within_bounds(obj, room):
            return False
            
        # Check if position satisfies object's constraints
        if not self._satisfies_object_constraints(obj, room):
            return False
            
        # Check if position overlaps with other objects
        if self._overlaps_with_objects(obj, room):
            return False
            
        # Check if position overlaps with windows/doors
        if self._overlaps_with_windows_doors(obj, room):
            return False
            
        return True
    
    def validate_room_constraints(self, room, layout):
        """
        Validate room-specific constraints.
        
        Args:
            room: Room object
            layout: Layout object
            
        Returns:
            bool: Whether the room constraints are satisfied
        """
        # Base implementation - no specific room constraints
        return True
    
    def _is_within_bounds(self, obj, room):
        """Check if object is within room bounds."""
        if obj.position is None:
            return False
            
        x, y, z = obj.position
        room_width, room_depth, room_height = room.get_size()
        
        return (0 <= x <= room_width - obj.depth and 
                0 <= y <= room_depth - obj.width and
                0 <= z <= room_height - obj.height)
    
    def _satisfies_object_constraints(self, obj, room):
        """Check if object satisfies its constraints."""
        # Get object-specific validator
        validator = ObjectConstraintValidator.get_validator(obj.object_type)
        return validator.validate(obj, room)
    
    def _overlaps_with_objects(self, obj, room):
        """Check if object overlaps with other objects."""
        if obj.position is None:
            return False
            
        x, y, z = obj.position
        width, depth, height = obj.width, obj.depth, obj.height
        
        for other_obj in room.get_placed_objects():
            # Skip the object itself
            if other_obj is obj:
                continue
                
            if other_obj.position is None:
                continue
                
            other_x, other_y, other_z = other_obj.position
            other_width = other_obj.width
            other_depth = other_obj.depth
            
            # Check for overlap
            if (x < other_x + other_depth and x + depth > other_x and
                y < other_y + other_width and y + width > other_y):
                return True
                
            # Check shadow space overlap if applicable
            if hasattr(obj, 'get_shadow_area') and hasattr(other_obj, 'get_shadow_area'):
                shadow_area = obj.get_shadow_area()
                other_shadow_area = other_obj.get_shadow_area()
                
                if shadow_area and other_shadow_area:
                    shadow_x, shadow_y, shadow_width, shadow_depth = shadow_area
                    other_shadow_x, other_shadow_y, other_shadow_width, other_shadow_depth = other_shadow_area
                    
                    if (shadow_x < other_shadow_x + other_shadow_depth and 
                        shadow_x + shadow_depth > other_shadow_x and
                        shadow_y < other_shadow_y + other_shadow_width and 
                        shadow_y + shadow_width > other_shadow_y):
                        return True
        
        return False
    
    def _overlaps_with_windows_doors(self, obj, room):
        """Check if object overlaps with windows/doors."""
        if obj.position is None:
            return False
            
        x, y, z = obj.position
        width, depth, height = obj.width, obj.depth, obj.height
        
        for window_door in room.windows_doors:
            if len(window_door) >= 6:  # Make sure it has all required fields
                wd_x, wd_y, wd_width, wd_depth = window_door[2], window_door[3], window_door[4], window_door[5]
                
                # Check for overlap
                if (x < wd_x + wd_depth and x + depth > wd_x and
                    y < wd_y + wd_width and y + width > wd_y):
                    return True
        
        return False


class BathroomConstraintValidator(BaseConstraintValidator):
    """Constraint validator for bathrooms."""
    
    def validate_room_constraints(self, room, layout):
        """Validate bathroom-specific constraints."""
        # Check if toilet is not directly visible from door
        if not self._check_toilet_door_visibility(room, layout):
            return False
            
        # Check if sink is accessible from door
        if not self._check_sink_door_accessibility(room, layout):
            return False
            
        return True
    
    def _check_toilet_door_visibility(self, room, layout):
        """Check if toilet is not directly visible from door."""
        # Implementation specific to bathroom
        # This is a placeholder - implement based on your requirements
        return True
    
    def _check_sink_door_accessibility(self, room, layout):
        """Check if sink is accessible from door."""
        # Implementation specific to bathroom
        # This is a placeholder - implement based on your requirements
        return True


class KitchenConstraintValidator(BaseConstraintValidator):
    """Constraint validator for kitchens."""
    
    def validate_room_constraints(self, room, layout):
        """Validate kitchen-specific constraints."""
        # Check if refrigerator is accessible
        if not self._check_refrigerator_accessibility(room, layout):
            return False
            
        # Check if work triangle is efficient
        if not self._check_work_triangle(room, layout):
            return False
            
        return True
    
    def _check_refrigerator_accessibility(self, room, layout):
        """Check if refrigerator is accessible."""
        # Implementation specific to kitchen
        # This is a placeholder - implement based on your requirements
        return True
    
    def _check_work_triangle(self, room, layout):
        """Check if work triangle (sink, stove, refrigerator) is efficient."""
        # Implementation specific to kitchen
        # This is a placeholder - implement based on your requirements
        return True


class BedroomConstraintValidator(BaseConstraintValidator):
    """Constraint validator for bedrooms."""
    
    def validate_room_constraints(self, room, layout):
        """Validate bedroom-specific constraints."""
        # Check if bed is not directly facing door
        if not self._check_bed_door_placement(room, layout):
            return False
            
        # Check if there's enough space around the bed
        if not self._check_bed_accessibility(room, layout):
            return False
            
        return True
    
    def _check_bed_door_placement(self, room, layout):
        """Check if bed is not directly facing door."""
        # Implementation specific to bedroom
        # This is a placeholder - implement based on your requirements
        return True
    
    def _check_bed_accessibility(self, room, layout):
        """Check if there's enough space around the bed."""
        # Implementation specific to bedroom
        # This is a placeholder - implement based on your requirements
        return True




# Legacy compatibility functions
def is_valid_placement(obj, placed_objects, shadow, room_width, room_depth):
    """Legacy function for checking if a placement is valid."""
    # This is a compatibility function for existing code
    # It should be replaced with the new validation system in the future
    
    x, y, width, depth = obj
    
    # Check if object is within room bounds
    if x < 0 or y < 0 or x + depth > room_width or y + width > room_depth:
        return False
    
    # Check if object overlaps with any placed object
    for placed_obj in placed_objects:
        px, py, pwidth, pdepth, pshadow = placed_obj
        
        # Check if objects overlap
        if (x < px + pdepth and x + depth > px and
            y < py + pwidth and y + width > py):
            return False
        
        # Check if shadow spaces overlap
        shadow_x = x - shadow[0]
        shadow_y = y - shadow[2]
        shadow_width = width + shadow[0] + shadow[1]
        shadow_depth = depth + shadow[2] + shadow[3]
        
        pshadow_x = px - pshadow[0]
        pshadow_y = py - pshadow[2]
        pshadow_width = pwidth + pshadow[0] + pshadow[1]
        pshadow_depth = pdepth + pshadow[2] + pshadow[3]
        
        if (shadow_x < pshadow_x + pshadow_depth and shadow_x + shadow_depth > pshadow_x and
            shadow_y < pshadow_y + pshadow_width and shadow_y + shadow_width > pshadow_y):
            return False
    
    return True

def windows_doors_overlap(windows_doors, x, y, z, width, depth, room_width, room_depth, shadow):
    """Legacy function for checking if an object overlaps with windows or doors."""
    # This is a compatibility function for existing code
    # It should be replaced with the new validation system in the future
    
    for window_door in windows_doors:
        if len(window_door) >= 6:  # Make sure it has all required fields
            wd_x, wd_y, wd_width, wd_depth = window_door[2], window_door[3], window_door[4], window_door[5]
            
            # Check if objects overlap
            if (x < wd_x + wd_depth and x + depth > wd_x and
                y < wd_y + wd_width and y + width > wd_y):
                return True
    
    return False