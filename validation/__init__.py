from .room_constraints import *
from .object_constraints import *
from .accessibility import *



# Factory function to get the appropriate constraint validator for a room type
def get_constraint_validator(room_type="bathroom"):
    """
    Get the appropriate constraint validator for a room type.
    
    Args:
        room_type: Type of room ('bathroom', 'kitchen', 'bedroom')
        
    Returns:
        BaseConstraintValidator: Appropriate constraint validator
    """
    validators = {
        'bathroom': BathroomConstraintValidator(),
        'kitchen': KitchenConstraintValidator(),
        'bedroom': BedroomConstraintValidator()
    }
    
    return validators.get(room_type.lower(), BaseConstraintValidator())