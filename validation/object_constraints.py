import sys
import os
import math

# Add the project root to the path so we can import from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.helpers import check_which_wall, check_overlap, check_distance_from_wall, check_euclidean_distance

class ObjectConstraintValidator:
    """Validator for object-specific constraints."""
    
    @staticmethod
    def get_validator(object_type):
        """
        Get the appropriate validator for an object type.
        
        Args:
            object_type: Type of object
            
        Returns:
            An object validator instance
        """
        validators = {
            # Bathroom fixtures
            "toilet": ToiletConstraintValidator(),
            "sink": SinkConstraintValidator(),
            "shower": ShowerConstraintValidator(),
            "bathtub": BathtubConstraintValidator(),
            "cabinet": CabinetConstraintValidator(),
            "washing machine": WashingMachineConstraintValidator(),
            "washing dryer": WashingDryerConstraintValidator(),
            "washing machine dryer": WashingMachineDryerConstraintValidator(),
            "asymmetrical bathtub": AsymmetricalBathtubConstraintValidator(),
            "toilet bidet": ToiletBidetConstraintValidator(),
            "double sink": DoubleSinkConstraintValidator()
        }
        
        return validators.get(object_type.lower(), DefaultObjectConstraintValidator())


class DefaultObjectConstraintValidator:
    """Default validator for objects without specific constraints."""
    
    def validate(self, placement, room):
        """
        Validate object constraints.
        
        Args:
            obj: Object to validate
            room: Room object
            
        Returns:
            bool: Whether the object satisfies its constraints
        """
        return True
    
    def _is_corner_placement(self, obj, room):
        """Check if object is placed in a corner."""
        if obj.position is None:
            return False
            
        x, y, z = obj.position
        room_width, room_depth, _ = room.get_size()
        
        # Check if object is in one of the corners
        is_top = abs(x) < 20
        is_bottom = abs(x + obj.depth - room_width) < 20
        is_left = abs(y) < 20
        is_right = abs(y + obj.width - room_depth) < 20
        
        return (is_left and is_top) or (is_left and is_bottom) or (is_right and is_top) or (is_right and is_bottom)
    
    def _is_against_wall(self, obj, room):
        """Check if object is placed against a wall."""
        if obj.position is None:
            return False
            
        x, y, z = obj.position
        room_width, room_depth, _ = room.get_size()
        
        # Check if object is against any wall
        is_top= abs(x) < 20
        is_bottom = abs(x + obj.depth - room_width) < 20
        is_left = abs(y) < 20
        is_right = abs(y + obj.width - room_depth) < 20
        
        return is_left or is_right or is_top or is_bottom


class ToiletConstraintValidator(DefaultObjectConstraintValidator):
    """Validator for toilet-specific constraints."""
    
    def validate(self, obj, room):
        """Validate toilet constraints."""
        # First check common constraints
        if not super().validate(obj, room):
            return False
            
        # Check toilet-specific constraints
        # For example, toilet should have enough space in front
        if not self._has_clearance_in_front(obj, room):
            return False
            
        return True
    
    def _has_clearance_in_front(self, obj, room):
        """Check if toilet has enough clearance in front."""
        # Implementation specific to toilet
        # This is a placeholder - implement based on your requirements
        return True

    def score(self, placement, room):
        """Score the toilet based on its placement."""
        return 0


class SinkConstraintValidator(DefaultObjectConstraintValidator):
    """Validator for sink-specific constraints."""
    
    def validate(self, obj, room):
        """Validate sink constraints."""
        # First check common constraints
        if not super().validate(obj, room):
            return False
            
        # Check sink-specific constraints
        # For example, sink should be accessible
        if not self._is_accessible(obj, room):
            return False
            
        return True
    
    def _is_accessible(self, obj, room):
        """Check if sink is accessible."""
        # Implementation specific to sink
        # This is a placeholder - implement based on your requirements
        return True


class ShowerConstraintValidator(DefaultObjectConstraintValidator):
    """Validator for shower-specific constraints."""
    
    def validate(self, obj, room):
        """Validate shower constraints."""
        # First check common constraints
        if not super().validate(obj, room):
            return False
            
        # Check shower-specific constraints
        # For example, shower should have enough space
        if not self._has_enough_space(obj, room):
            return False
            
        return True
    
    def _has_enough_space(self, obj, room):
        """Check if shower has enough space."""
        # Implementation specific to shower
        # This is a placeholder - implement based on your requirements
        return True


class BathtubConstraintValidator(DefaultObjectConstraintValidator):
    """Validator for bathtub-specific constraints."""
    
    def validate(self, obj, room):
        """Validate bathtub constraints."""
        # First check common constraints
        if not super().validate(obj, room):
            return False
            
        # Check bathtub-specific constraints
        # For example, bathtub should have enough space around it
        if not self._has_enough_space_around(obj, room):
            return False
            
        return True
    
    def _has_enough_space_around(self, obj, room):
        """Check if bathtub has enough space around it."""
        # Implementation specific to bathtub
        # This is a placeholder - implement based on your requirements
        return True


class CabinetConstraintValidator(DefaultObjectConstraintValidator):
    """Validator for cabinet-specific constraints."""
    
    def validate(self, obj, room):
        """Validate cabinet constraints."""
        # First check common constraints
        if not super().validate(obj, room):
            return False
            
        # Check cabinet-specific constraints
        # For example, cabinet should not block access to other objects
        if not self._does_not_block_access(obj, room):
            return False
            
        return True
    
    def _does_not_block_access(self, obj, room):
        """Check if cabinet doesn't block access to other objects."""
        # Check if cabinet blocks access to important fixtures like toilets and sinks
        min_clearance = 60  # Minimum clearance in cm
        
        for other_obj in room.get_placed_objects():
            if other_obj == obj:  # Skip self
                continue
                
            # Check if other object is a critical fixture that needs access
            if other_obj.object_type.lower() in ["toilet", "sink", "shower", "bathtub", "double sink"]:
                # Calculate distance between objects
                distance = check_euclidean_distance(
                    (obj.position[0], obj.position[1], obj.width, obj.depth),
                    (other_obj.position[0], other_obj.position[1], other_obj.width, other_obj.depth)
                )
                
                if distance < min_clearance:
                    return False
                    
        return True


class WashingMachineConstraintValidator(DefaultObjectConstraintValidator):
    """Validator for washing machine-specific constraints."""
    
    def validate(self, obj, room):
        """Validate washing machine constraints."""
        # First check common constraints
        if not super().validate(obj, room):
            return False
            
        # Check if washing machine is against a wall
        if not self._is_against_wall(obj, room):
            return False
            
        # Check if there's enough space in front for loading/unloading
        if not self._has_loading_space(obj, room):
            return False
            
        return True
    
    def _has_loading_space(self, obj, room):
        """Check if washing machine has enough space in front for loading/unloading."""
        min_space = 80  # Minimum space in cm
        
        # Determine which side is the front (usually the side not against the wall)
        x, y, z = obj.position
        room_width, room_depth, _ = room.get_size()
        
        # Simplified check - ensure there's space in front of the machine
        # In a real implementation, you would determine which side is the front based on the model
        wall = check_which_wall((x, y, obj.width, obj.depth), room_width, room_depth)
        
        # Check space based on which wall it's against
        if wall == "top":
            # Check space below
            for other_obj in room.get_placed_objects():
                if other_obj == obj:  # Skip self
                    continue
                    
                other_x, other_y, _ = other_obj.position
                if (other_x < x + obj.depth and other_x + other_obj.depth > x and
                    other_y > y and other_y < y + min_space):
                    return False
        # Similar checks for other walls
        
        return True


class WashingDryerConstraintValidator(WashingMachineConstraintValidator):
    """Validator for washing dryer-specific constraints."""
    # Inherits constraints from washing machine
    pass


class WashingMachineDryerConstraintValidator(WashingMachineConstraintValidator):
    """Validator for combined washing machine/dryer-specific constraints."""
    # Inherits constraints from washing machine
    pass


class AsymmetricalBathtubConstraintValidator(BathtubConstraintValidator):
    """Validator for asymmetrical bathtub-specific constraints."""
    
    def validate(self, obj, room):
        """Validate asymmetrical bathtub constraints."""
        # First check common bathtub constraints
        if not super().validate(obj, room):
            return False
            
        # Check if the asymmetrical part is correctly oriented
        if not self._correct_orientation(obj, room):
            return False
            
        return True
    
    def _correct_orientation(self, obj, room):
        """Check if the asymmetrical bathtub is correctly oriented."""
        # In a real implementation, you would check if the wider part of the bathtub
        # is oriented in a way that makes sense (e.g., not against a wall)
        return True


class ToiletBidetConstraintValidator(ToiletConstraintValidator):
    """Validator for toilet bidet-specific constraints."""
    # Inherits constraints from toilet
    pass


class DoubleSinkConstraintValidator(SinkConstraintValidator):
    """Validator for double sink-specific constraints."""
    
    def validate(self, obj, room):
        """Validate double sink constraints."""
        # First check common sink constraints
        if not super().validate(obj, room):
            return False
            
        # Check if bathroom is large enough for a double sink
        room_width, room_depth, _ = room.get_size()
        room_area = room_width * room_depth
        
        # Double sinks are only appropriate for larger bathrooms (>= 300x300cm)
        if room_area < 90000:  # 300*300 = 90000 sq cm
            return False
            
        return True