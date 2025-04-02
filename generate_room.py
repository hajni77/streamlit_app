


# READ OBJECT TYPES FROM FILE
import json

from visualize import visualize_room_with_shadows_3d
from utils import check_valid_room, fit_objects_in_room, check_distance_from_wall, check_which_wall, check_distance, adjust_object_placement_pos, convert_values, adjust_object_placement, is_valid_placement
class ObjectType:
    """Defines the constraints for different object types."""
    def __init__(self, name, must_be_corner, shadow_space, size_range, must_be_against_wall):
        self.name = name
        self.must_be_corner = must_be_corner
        self.shadow_space = shadow_space  # How much space the shadow takes up on the front and sides
        self.size_range = size_range  # (min_width, max_width, min_depth,max_depth,min_height, max_height)
        self.optimal_size = size_range  # (optimal_width, optimal_depth, optimal_height)
        self.must_be_against_wall = must_be_against_wall


OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)
    
    

windows_doors = [
    # ("window1", "left", 100, 80, 80, 100, 90),
    ("door1", "left", 50, 0, 75, 200, 0),
]
bathroom_size = (200, 200)  # Width, Depth, Height
objects = ["sink","bathtub","washing_machine",]

# bathroom_size = (180, 160)  # Width, Depth, Height
# objects = ["bathtub","sink", "washing_machine"]
positions = fit_objects_in_room(bathroom_size, objects, windows_doors, attempt=10000)



visualize_room_with_shadows_3d(bathroom_size, positions, windows_doors)
check_valid_room( positions)