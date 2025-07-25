"""
Placement strategies for bathroom objects.
This module contains different strategies for placing objects in a bathroom layout.
"""

import sys
import os
import random
from abc import ABC, abstractmethod
from models.object import BathroomObject, BaseObject
from utils.helpers import check_which_wall, is_valid_placement, windows_doors_overlap, extract_object_based_on_type, extract_door_window_based_on_type, convert_values, generate_random_position

# Add the project root to the path so we can import from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from validation import get_constraint_validator


class PlacementStrategy(ABC):
    """Abstract base class for placement strategies."""
    
    @abstractmethod
    def generate_options(self, layout, obj_type, obj_def, bathroom_size, placed_objects, windows_doors, num_options=10):
        """Generate placement options for a bathroom object."""
        pass
        
    def __str__(self):
        return "AbstractPlacementStrategy"


class DefaultPlacementStrategy(PlacementStrategy):
    """Default strategy that places objects based on their constraints."""
    
    def generate_options(self, layout, obj_type, obj_def, bathroom_size, placed_objects, windows_doors, num_options=50, use_optimal_size=True):
        """Generate placement options for a bathroom object.
        
        Args:
            layout: The current bathroom layout
            obj_type: The type of object to place
            obj_def: Object definition with constraints
            bathroom_size: Tuple of (width, depth) of the bathroom
            placed_objects: List of BathroomObject instances already placed
            windows_doors: List of windows and doors
            num_options: Number of options to generate
            use_optimal_size: Whether to use optimal size or try variations
            
        Returns:
            List of placement options as dictionaries with 'object' and 'position' keys
        """
        options = []
        room_width, room_depth, room_height = bathroom_size
        shadow = obj_def["shadow_space"]
        #use_optimal_size = random.choice([True, False])
        # Get size variations to try
        if use_optimal_size:
            # Only use optimal size
            size_variations = [obj_def["optimal_size"]]
            if obj_def["name"] == "Washing Machine":
                min_width, max_width, min_depth, max_depth, min_height, max_height = obj_def["size_range"]
                size_variations.append((min_width, min_depth, min_height))
                
            # also use the switched width and depth value
            #size_variations.append((obj_def["optimal_size"][1], obj_def["optimal_size"][0], obj_def["optimal_size"][2]))
        else:
            # Generate size variations within min/max range
            if obj_def["name"] == "Washing Machine":
                min_width, max_width, min_depth, max_depth, min_height, max_height = obj_def["size_range"]
                size_variations.append((min_width, min_depth, min_height))
            size_variations = self._generate_size_variations(obj_def)


        # get door wall
        # get door wall
        door_walls = []

        if windows_doors:
            # Handle both single object and list of objects
            if isinstance(windows_doors, list):
                # It's a list of WindowsDoors objects
                for door_window in windows_doors:
                    if hasattr(door_window, 'get_door_walls'):
                        door_walls.append(door_window.get_door_walls())
            else:
                # It's a single WindowsDoors object
                if hasattr(windows_doors, 'get_door_walls'):
                    door_walls.append(windows_doors.get_door_walls())
                elif hasattr(windows_doors, 'wall'):
                    door_walls.append(windows_doors.wall)
        # For each size variation, try different positions
        for obj_width, obj_depth, obj_height in size_variations:
            # Try different positions based on constraints
            if obj_def["must_be_corner"]:
                options.extend(self._generate_corner_positions(
                    obj_type, obj_def, obj_width, obj_depth, obj_height, shadow,
                    bathroom_size, placed_objects, windows_doors, num_options, door_walls
                ))
            elif obj_def["must_be_against_wall"]:
                options.extend(self._generate_wall_positions(
                    obj_type, obj_def, obj_width, obj_depth, obj_height, shadow,
                    bathroom_size, placed_objects, windows_doors, num_options, door_walls
                ))
            else:
                options.extend(self._generate_free_positions(
                    obj_type, obj_def, obj_width, obj_depth, obj_height, shadow,
                    bathroom_size, placed_objects, windows_doors, num_options, door_walls
                ))


            # If we have enough options, stop
        # if len(options) >= num_options:
        #     return options[:num_options]
        return options
    
    def __str__(self):
        return "DefaultPlacementStrategy"
    
    def _generate_size_variations(self, obj_def):
        """Generate size variations within min/max range using 5cm increments."""
        min_width, max_width, min_depth, max_depth, min_height, max_height = obj_def["size_range"]
        optimal_width, optimal_depth, optimal_height = obj_def["optimal_size"]
        
        # Start with optimal size
        variations = [(optimal_width, optimal_depth, optimal_height)]
        
        # Calculate aspect ratio to maintain proportions
        aspect_ratio = optimal_depth / optimal_width if optimal_width > 0 else 1
        
        # # Add smaller variations in 5cm decrements while maintaining proportions
        # current_width = optimal_width
        # current_depth = optimal_depth
        
        # # Generate smaller variations
        # while True:
        #     # Decrease by 5cm
        #     current_width -= 5
        #     # Maintain proportion for depth
        #     current_depth = int(current_width * aspect_ratio)
            
        #     # Check if we've reached minimum size
        #     if current_width < min_width or current_depth < min_depth:
        #         break
                
        #     variations.append((current_width, current_depth, optimal_height))
        #     #variations.append((current_depth, current_width, optimal_height))

        # Generate larger variations
        current_width = optimal_width
        current_depth = optimal_depth
        
        while True:
            # Increase by 5cm
            current_width += 5
            # Maintain proportion for depth
            current_depth = int(current_width * aspect_ratio)
            
            # Check if we've reached maximum size
            if current_width > max_width or current_depth > max_depth:
                break
                
            variations.append((current_width, current_depth, optimal_height))
            #variations.append((current_depth, current_width, optimal_height))
        
        return variations
    
    def _generate_corner_positions(self, obj_type, obj_def, obj_width, obj_depth, obj_height, shadow,
                            bathroom_size, placed_objects, windows_doors, num_options, door_walls):
        """Generate positions for objects that must be in a corner."""
        options = []
        room_width, room_depth, room_height = bathroom_size
        
        # Try each corner
        corner_positions = [
            (0, 0),  # Top-left
            (room_width - obj_depth, 0),  # Top-right
            (0, room_depth - obj_width),  # Bottom-left
            (room_width - obj_depth, room_depth - obj_width)  # Bottom-right
        ]
        # corner positions dict with walls
        corner_positions_dict = {
            (0, 0): "top-left",
            (room_width - obj_depth, 0): "bottom-left",
            (0, room_depth - obj_width): "top-right",
            (room_width - obj_depth, room_depth - obj_width): "bottom-right"
        }
        

        for x, y in corner_positions:
            shadow = obj_def["shadow_space"]
            # can switch between width and depth
            _,_,_,_,shadow_top, shadow_left, shadow_right, shadow_bottom = convert_values((x, y, obj_width, obj_depth, obj_height), shadow, corner_positions_dict[(x, y)])
            shadow = [shadow_top, shadow_left, shadow_right, shadow_bottom]
            obj_width_TEMP, obj_depth_TEMP = obj_width, obj_depth
            for i in range(2):
                obj_width_TEMP, obj_depth_TEMP = obj_depth_TEMP, obj_width_TEMP
                if is_valid_placement((x, y, obj_width_TEMP, obj_depth_TEMP, obj_height), placed_objects, shadow, room_width, room_depth, door_walls):
                    if not windows_doors_overlap(windows_doors, x, y, 0,obj_width_TEMP, obj_depth_TEMP, obj_height, room_width, room_depth, shadow,obj_type):
                        
                        # Create a BathroomObject instance
                        bathroom_obj = BathroomObject(
                            object_type=obj_type,
                            
                            width=obj_width_TEMP,
                            depth=obj_depth_TEMP,
                            height=obj_height,
                            shadow=shadow,
                            position=(x, y),
                            wall=corner_positions_dict[(x, y)]
                            
                        )
                        
                        options.append({
                            "object": bathroom_obj,
                            "position": (x, y, obj_width_TEMP, obj_depth_TEMP, obj_height, shadow)
                        })
                        

        
        return options
    
    def _generate_wall_positions(self, obj_type, obj_def, obj_width, obj_depth, obj_height, shadow,
                              bathroom_size, placed_objects, windows_doors, num_options, door_walls):
        """Generate positions for objects that must be against a wall."""
        options = []
        room_width, room_depth, room_height = bathroom_size
        # Get all objects that are against walls
        wall_objects = []
        for obj in placed_objects:
            x, y, width, depth, height, obj_name, shadow = extract_object_based_on_type(obj)
                
            # Determine which wall(s) this object is against
            wall = check_which_wall((x, y, width, depth, height), room_width, room_depth)
            wall_objects.append({
                    "name": obj_name,
                    "wall": wall,
                    "x": x,
                    "y": y,
                    "width": width,
                    "depth": depth,
                    "height": height
                })
        
        # Also consider windows and doors as wall objects
        if windows_doors:  # Check if windows_doors exists
            # Handle both single object and list of objects
            door_windows_list = [windows_doors] if not isinstance(windows_doors, list) else windows_doors
            
            for door_window in door_windows_list:
                # Extract properties from door_window
                x, y, width, depth, height, wall = extract_door_window_based_on_type(door_window)
                
                # Determine which wall this window/door is on
                # If we already have a wall from the object, use it
                if wall and isinstance(wall, str):
                    walls = [wall]
                else:
                    # Otherwise determine based on position
                    against_top = y < 20
                    against_bottom = y + height > room_depth - 20
                    against_left = x < 20
                    against_right = x + width > room_width - 20
                    
                    walls = []
                    if against_top:
                        walls.append("top")
                    if against_bottom:
                        walls.append("bottom")
                    if against_left:
                        walls.append("left")
                    if against_right:
                        walls.append("right")
                
                # Add wall objects for this door/window
                for wall_pos in walls:
                    wall_objects.append({
                        "name": door_window.name if hasattr(door_window, 'name') else "window_door",
                        "wall": wall_pos,
                        "x": x,
                        "y": y,
                        "width": width,
                        "depth": depth,
                        "height": height
                    })
            
        # generate all possible positions for the new object considering the wall objects
        # go through all the wall objects and check if the new object can be placed next to it
        wall_positions = []

        for obj in wall_objects:

            
            if "top" in obj["wall"] :

                # check if the new object can be placed next to it
                if room_depth - obj["y"] - obj["width"] > obj_width and "right" not in obj["wall"]:
                    wall_positions.append((int(obj["x"]), int(obj["y"]+obj["width"]), "top"))
                    i = 1
                    while room_depth - obj["y"] - obj["width"] > obj_width+i*5:
                        wall_positions.append((int(obj["x"]), int(obj["y"]+obj["width"]+i*5), "top"))
                        i += 1
                if obj["y"] > obj_width:
                    wall_positions.append((int(obj["x"]), int(obj["y"]-obj["width"]), "top"))
                    i = 1
                    while obj["y"] > obj_width+i*5:
                        wall_positions.append((int(obj["x"]), int(obj["y"]-obj["width"]-i*5), "top"))
                        i += 1
            elif "bottom" in obj["wall"]:

                if room_depth - obj["y"] - obj["width"] > obj_width and "right" not in obj["wall"]:
                    wall_positions.append((int(room_width-obj_depth), int(obj["y"]+obj["width"]), "bottom"))
                    i = 1
                    while room_depth - obj["y"] - obj["width"] > obj_width+i*5:
                        wall_positions.append((int(room_width-obj_depth), int(obj["y"]+obj["width"]+i*5), "bottom"))
                        i += 1
                if obj["y"] > obj_width:
                    wall_positions.append((int(room_width-obj_depth), int(obj["y"]-obj_width), "bottom"))
                    i = 1
                    while obj["y"] > obj_width+i*5:
                        wall_positions.append((int(room_width-obj_depth), int(obj["y"]-obj_width-i*5), "bottom"))
                        i += 1
            elif "left" in obj["wall"] :

                if room_width - obj["x"] - obj["depth"] > obj_width and "bottom" not in obj["wall"]:
                    wall_positions.append((int(obj["x"]+obj["depth"]), int(obj["y"]), "left"))
                    i = 1
                    while room_width - obj["x"] - obj["depth"] > obj_width+i*5:
                        wall_positions.append((int(obj["x"]+obj["depth"]+i*5), int(obj["y"]), "left"))
                        i += 1
                if obj["x"] > obj_width:
                    wall_positions.append((int(obj["x"]-obj_width), int(obj["y"]), "left"))
                    i = 1
                    while obj["x"] > obj_width+i*5:
                        wall_positions.append((int(obj["x"]-obj_width-i*5), int(obj["y"]), "left"))
                        i += 1
            elif "right" in obj["wall"]:

                if room_width - obj["x"] - obj["depth"] > obj_width and "bottom" not in obj["wall"]:
                    wall_positions.append((int(obj["x"]+obj["depth"]), int(room_depth-obj_depth), "right"))
                    i = 1
                    while room_width - obj["x"] - obj["depth"] > obj_width+i*5:
                        wall_positions.append((int(obj["x"]+obj["depth"]+i*5), int(room_depth-obj_depth), "right"))
                        i += 1
                if obj["x"] > obj_width:
                    wall_positions.append((int(obj["x"]-obj_width), int(room_depth-obj_depth), "right"))
                    i = 1
                    while obj["x"] > obj_width+i*5:
                        wall_positions.append((int(obj["x"]-obj_width-i*5), int(room_depth-obj_depth), "right"))
                        i += 1
        # place object randomly in room where there are no wall objects

        top_positions = generate_random_position("top",room_width,room_depth,obj_width,obj_depth)
        if top_positions:
            for pos in top_positions:
                wall_positions.append(pos)

        bottom_positions = generate_random_position("bottom",room_width,room_depth,obj_width,obj_depth)
        if bottom_positions:
            for pos in bottom_positions:
                wall_positions.append(pos)

        left_positions = generate_random_position("left",room_width,room_depth,obj_width,obj_depth)
        if left_positions:
            for pos in left_positions:
                wall_positions.append(pos)

        right_positions = generate_random_position("right",room_width,room_depth,obj_width,obj_depth)
        if right_positions:
            for pos in right_positions:
                wall_positions.append(pos)
        for (x,y,wall) in wall_positions:
            if x < 0 or y < 0:
                continue
            shadow = obj_def["shadow_space"]
            obj_width_TEMP, obj_depth_TEMP = obj_width, obj_depth
            if wall == "right" or wall == "left" :
                obj_width_TEMP, obj_depth_TEMP = obj_depth, obj_width
            _,_,_,_,shadow_top, shadow_left, shadow_right, shadow_bottom = convert_values((x, y, obj_width_TEMP, obj_depth_TEMP, obj_height), shadow, wall)
            shadow = [shadow_top, shadow_left, shadow_right, shadow_bottom]
            if is_valid_placement((x, y, obj_width_TEMP, obj_depth_TEMP, obj_height), placed_objects, shadow, room_width, room_depth, door_walls):
                if not windows_doors_overlap(windows_doors, x, y, 0, obj_width_TEMP, obj_depth_TEMP, obj_height, room_width, room_depth, shadow,obj_type):
                    # Create a BathroomObject instance
                    bathroom_obj = BathroomObject(
                        object_type=obj_type,
                        
                        width=obj_width_TEMP,
                        depth=obj_depth_TEMP,
                        height=obj_height,
                        shadow=shadow,
                        position=(x, y),
                        wall=wall
                    )
                    
                    options.append({
                        "object": bathroom_obj,
                        "position": (x, y, obj_width_TEMP, obj_depth_TEMP, obj_height, shadow)
                    })

                    
                    # if len(options) >= num_options:
                    #     break
        
        return options 
        
        # Function to check if a position is next to an existing object along a wall
    def is_next_to_object(x, y, wall):
        for obj in wall_objects:
            if obj["wall"] != wall:
                continue
            
            if wall == "top" or wall == "bottom":
                # Check if horizontally adjacent
                obj_left = obj["x"]
                obj_right = obj["x"] + obj["depth"]
                new_left = x
                new_right = x + obj_depth
                    
                # Check if they're next to each other (with a small gap)
                if (abs(new_left - obj_right) < 10 or abs(new_right - obj_left) < 10):
                    return True
                
            elif wall == "left" or wall == "right":
                # Check if vertically adjacent
                obj_top = obj["y"]
                obj_bottom = obj["y"] + obj["width"]
                new_top = y
                new_bottom = y + obj_width
                    
                # Check if they're next to each other (with a small gap)
                if (abs(new_top - obj_bottom) < 10 or abs(new_bottom - obj_top) < 10):
                    return True
                        
        return False
        
    # Function to check if a position overlaps with an existing object
    def overlaps_with_object(x, y, wall):
        for obj in wall_objects:
            if wall == "top" or wall == "bottom":
                # Check horizontal overlap
                obj_left = obj["x"]
                obj_right = obj["x"] + obj["depth"]
                new_left = x
                new_right = x + obj_depth
                    
                # Check for overlap
                if max(new_left, obj_left) < min(new_right, obj_right):
                    return True
                
            elif wall == "left" or wall == "right":
                # Check vertical overlap
                obj_top = obj["y"]
                obj_bottom = obj["y"] + obj["width"]
                new_top = y
                new_bottom = y + obj_width
                    
                # Check for overlap
                if max(new_top, obj_top) < min(new_bottom, obj_bottom):
                    return True
                        
        return False
        
        # # Generate positions along each wall
        # wall_data = [
        #     {"name": "top", "positions": [(x, shadow[2]) for x in range(shadow[0], room_width - obj_depth - shadow[1], 10)]},
        #     {"name": "bottom", "positions": [(x, room_depth - obj_width - shadow[3]) for x in range(shadow[0], room_width - obj_depth - shadow[1], 10)]},
        #     {"name": "left", "positions": [(shadow[0], y) for y in range(shadow[2], room_depth - obj_width - shadow[3], 10)]},
        #     {"name": "right", "positions": [(room_width - obj_depth - shadow[1], y) for y in range(shadow[2], room_depth - obj_width - shadow[3], 10)]}
        # ]
        
        # # First, try positions next to existing objects
        # adjacent_positions = []
        # for wall in wall_data:
        #     for x, y in wall["positions"]:
        #         if is_next_to_object(x, y, wall["name"]) and not overlaps_with_object(x, y, wall["name"]):
        #             adjacent_positions.append((x, y, wall["name"]))
        
        # # Then, add positions that aren't next to objects but don't overlap
        # other_positions = []
        # for wall in wall_data:
        #     for x, y in wall["positions"]:
        #         if not overlaps_with_object(x, y, wall["name"]) and not any(p[0] == x and p[1] == y for p in adjacent_positions):
        #             other_positions.append((x, y, wall["name"]))
        
        # # Combine and prioritize: adjacent positions first, then other valid positions
        # all_positions = adjacent_positions + other_positions
        
        # # Check each position for validity
        # for x, y, _ in all_positions:
        #     door_wall = windows_doors.wall
        #     if is_valid_placement((x, y, obj_width, obj_depth, obj_height), placed_objects, shadow, room_width, room_depth, door_wall):
        #         if not windows_doors_overlap(windows_doors, x, y, 0, obj_width, obj_depth, obj_height, room_width, room_depth, shadow):
        #             # Create a BathroomObject instance
        #             bathroom_obj = BathroomObject(
        #                 object_type=obj_type,
        #                 width=obj_width,
        #                 depth=obj_depth,
        #                 height=obj_height,
        #                 shadow=shadow,
        #                 position=(x, y),
        #                 wall=_  # wall name from the tuple
        #             )
                    
        #             options.append({
        #                 "object": bathroom_obj,
        #                 "position": (x, y, obj_width, obj_depth, obj_height, obj_def['name'], 
        #                             obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow)
        #             })
                    
        #             if len(options) >= num_options:
        #                 break
        
        # return options
    
    def _generate_free_positions(self, obj_type, obj_def, obj_width, obj_depth, obj_height, shadow,
                               bathroom_size, placed_objects, windows_doors, num_options, door_walls):
        """Generate positions for free-standing objects that can be placed anywhere."""
        options = []
        room_width, room_depth, room_height = bathroom_size
        
        # Try grid positions with a smaller step for more options
        step_size = 15  # cm between position attempts
        
        # Add some randomness to the starting position to avoid grid-like layouts
        import random
        start_x = shadow[0] + random.randint(0, 10)
        start_y = shadow[2] + random.randint(0, 10)
        
        for x in range(start_x, room_width - obj_depth - shadow[1], step_size):
            for y in range(start_y, room_depth - obj_width - shadow[3], step_size):
                if is_valid_placement((x, y, obj_width, obj_depth, obj_height), placed_objects, shadow, room_width, room_depth, room_height):
                    if not windows_doors_overlap(windows_doors, x, y, 0, obj_width, obj_depth, obj_height, room_width, room_depth, shadow):
                        # Create a BathroomObject instance
                        bathroom_obj = BathroomObject(
                            object_type=obj_type,
                            
                            width=obj_width,
                            depth=obj_depth,
                            height=obj_height,
                            shadow=shadow,
                            position=(x, y),
                            wall=None  # Free-standing object
                        )
                        
                        options.append({
                            "object": bathroom_obj,
                            "position": (x, y, obj_width, obj_depth, obj_height, obj_def['name'], 
                                        obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow)
                        })
                        
                        if len(options) >= num_options:
                            return options

    def fit_objects_in_room(bathroom_size, object_list, windows_doors, OBJECT_TYPES, attempt=1000, validator=None):


        


        for obj_type in sorted_objects:
            obj_def = OBJECT_TYPES[obj_type]
            shadow = obj_def["shadow_space"]
            optimal_size = obj_def["optimal_size"]
            placed = False

            # Dictionary to store wall selection counts
            wall_counts = {"top": 0, "bottom": 0, "left": 0, "right": 0}
            for _ in range(attempt):  # Try placements
                if _ == attempt/2 and obj_type == "double sink":
                    obj_def = OBJECT_TYPES["sink"]
                    obj_type = "sink"
                    optimal_size = obj_def["optimal_size"]
                    
                obj_width, obj_depth, obj_height = optimal_size
                if obj_def["must_be_corner"]:
                    # randomly switch width and depth
                    if random.choice([0,1]):
                        obj_width, obj_depth = obj_depth, obj_width
                    # Place in a corner
                    corners = [
                        (0, 0),  # Top-left
                        (0,room_depth - obj_width),  # Top-right
                        (room_width - obj_depth,0),  # Bottom-left
                        (room_width - obj_depth, room_depth - obj_width)  # Bottom-right
                    ]
                    x, y = random.choice(corners)


                elif obj_def['must_be_against_wall']:
                    # Ensure longest side is along the wall
                    walls = ["top", "bottom", "left", "right"]
                    
                    if obj_def['name'] in ["toilet", "Toilet", "Toilet Bidet", "toilet bidet"]:
                        # First try to get walls parallel to doors, which are preferred for toilet placement
                        parallel_walls = get_walls_parallel_to_doors(door_walls)
                        
                        # Check if we have any parallel walls available
                        available_parallel_walls = [w for w in parallel_walls if w in ["top", "bottom", "left", "right"]]
                        
                        # If we have parallel walls, prioritize them
                        if available_parallel_walls:
                            wall = random.choice(available_parallel_walls)
                        else:
                            # Fall back to any available wall if no parallel walls
                            available_walls = get_available_walls(door_walls)
                            wall = random.choice(available_walls)
                    else:
                        wall = random.choice(walls)
                    # Track wall selection count
                    wall_counts[wall] += 1
                    if wall == "top":
                            x, y = 0,max(random.randint(0, room_depth - obj_width),0)
                    elif wall == "bottom":
                            x, y = max(room_width-obj_depth,0),max(random.randint(0, room_depth- obj_width),0)
                    elif wall == "right":
                            if obj_width > obj_depth:
                            # switch object depth and width value
                                obj_width, obj_depth = obj_depth, obj_width
                            x, y = max(random.randint(0, room_width - obj_depth),0),max(room_depth - obj_width,0)
                    elif wall == "left":
                            if obj_width > obj_depth:
                            # switch object depth and width value
                                obj_width, obj_depth = obj_depth, obj_width

                            x, y = max(random.randint(0, room_width - obj_depth),0),0 
                    # x, y, obj_width, obj_height = adjust_orientation_for_wall(x, y, obj_width, obj_height, room_width, room_depth)
                else:
                    # Place anywhere in the room
                    x = random.randint(0, room_width - obj_depth)
                    y = random.randint(0, room_depth - obj_width)

                z = obj_height
                # x, y, obj_width, obj_depth = adjust_object_placement((x, y, obj_width, obj_depth),shadow, room_width, room_depth, min_space=30)  



                # Use the constraint validator if provided, otherwise fall back to legacy validation
                if validator:
                    # Create a bathroom object representation for validation
                    from models.bathroom import Bathroom
                    bathroom = Bathroom(room_width, room_depth)
                    for wd in windows_doors:
                        bathroom.add_window_door(wd)
                    
                    # Create an object representation for validation
                    from models.object import BathroomObject
                    bathroom_obj = BathroomObject(obj_type,  obj_width, obj_depth, obj_height, shadow)
                    
                    # Validate placement using the constraint validator
                    is_valid = validator.validate_placement(bathroom_obj, (x, y), bathroom)
                else:
                    # Legacy validation
                    is_valid = is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, door_wall)
                    
                if is_valid:
                    if ("bathtub" or "asymmetrical bathtub") not in object_positions or check_bathtub_shadow((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, object_positions, obj_type):
                        if (obj_type == "sink" or obj_type == "toilet"  or obj_type == "double sink") and not check_door_sink_placement((x, y, obj_width, obj_depth), placed_objects, windows_doors, room_width, room_depth, obj_type):
                            placed = False
                        elif windows_doors_overlap(windows_doors, x, y, z, obj_width, obj_depth, obj_height, room_width, room_depth, shadow) :
                            placed = False

                        else:
                            placed = True
                            x,y,obj_width,obj_depth,obj_height = optimize_object((x, y, obj_width, obj_depth,obj_height), shadow, room_width, room_depth,object_positions,door_wall)
                            object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                            #fig = visualize_room_with_shadows_3d(bathroom_size, object_positions, windows_doors)
                            #st.pyplot(fig)
                            placed_objects.append((x, y, obj_width, obj_depth,obj_height, shadow ))
                            break
                # if obj_type == "toilet":
                #     toilet_placed = is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow,room_width, room_depth)
                #     if toilet_placed:
                #         # if bathtub is in the objects

                #         if "bathtub" not in object_positions or check_bathtub_shadow((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, object_positions, obj_type):
                #             if windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth, shadow):
                #                 placed = False
                #             else :
                #                 placed = True
                #                 x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions )
                #                 object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                #                 #fig = visualize_room_with_shadows_3d(bathroom_size, object_positions, windows_doors)
                #                 #st.pyplot(fig)
                #                 placed_objects.append((x, y, obj_width, obj_depth, shadow ))
                #                 break
                #if obj_type == "bathtub":
                    
                    #dist,rect_smaller = check_distance(conv_rect, conv_placed_obj)
        
            if not placed :
                
                obj_def = OBJECT_TYPES[obj_type]
                orig_obj_width, orig_obj_depth,orig_obj_height = generate_random_size(obj_def)
                if obj_type == "washing machine" or obj_type == "washing dryer":
                    # randomly 45 or 60
                    orig_obj_width= random.choice([45])
                    orig_obj_depth = 60
                for _ in range(attempt):  # Try 100 placements
                    obj_width, obj_depth, obj_height = orig_obj_width, orig_obj_depth,orig_obj_height
                    if obj_def["must_be_corner"]:
                        # randomly switch width and depth
                        if random.choice([0,1]):
                            obj_width, obj_depth = obj_depth, obj_width
                        # Place in a corner
                        corners = [
                            (0, 0),  # Top-left
                            (0,room_depth - obj_width),  # Top-right
                            (room_width - obj_depth,0),  # Bottom-left
                            (room_width - obj_depth, room_depth - obj_width)  # Bottom-right
                        ]
                        x, y = random.choice(corners)

                    elif obj_def['must_be_against_wall']:
                        # Ensure longest side is along the wall
                        walls = ["top", "bottom", "left", "right"]
                        # if obj_width > obj_depth:  # Landscape orientation
                        #     preferred_walls = ["top", "bottom"]
                        # else:  # Portrait orientation
                        #     preferred_walls = ["left", "right"]
                        
                        if obj_def['name'] == "toilet" or obj_def['name'] == "Toilet":
                            parallel_walls = get_walls_parallel_to_doors(door_walls)
                            available_parallel_walls = [w for w in parallel_walls if w in ["top", "bottom", "left", "right"]]
                            if available_parallel_walls:
                                wall = random.choice(available_parallel_walls)
                            else:
                                available_walls = get_available_walls(door_walls)
                                wall = random.choice(available_walls)
                        else:
                            wall = random.choice(walls)

                        if wall == "top":
                            x, y = 0,max(random.randint(0, room_depth - obj_width),0)
                        elif wall == "bottom":
                            x, y = max(room_width-obj_depth,0),max(random.randint(0, room_depth- obj_width),0)
                        elif wall == "right":
                            if obj_width > obj_depth:
                            # switch object depth and width value
                                obj_width, obj_depth = obj_depth, obj_width
                            x, y = max(random.randint(0, room_width - obj_depth),0),max(room_depth - obj_width,0)
                        elif wall == "left":
                            if obj_width > obj_depth:
                            # switch object depth and width value
                                obj_width, obj_depth = obj_depth, obj_width

                            x, y = max(random.randint(0, room_width - obj_depth),0),0 
                        # x, y, obj_width, obj_height = adjust_orientation_for_wall(x, y, obj_width, obj_height, room_width, room_depth)
                    else:
                        # Place anywhere in the room
                        x = random.randint(0, room_width - obj_width)
                        y = random.randint(0, room_depth - obj_depth)
                    z = obj_height


                    # Use the constraint validator if provided, otherwise fall back to legacy validation
                    if validator:
                        # Create a bathroom object representation for validation
                        from models.bathroom import Bathroom
                        bathroom = Bathroom(room_width, room_depth)
                        for wd in windows_doors:
                            bathroom.add_window_door(wd)
                        
                        # Create an object representation for validation
                        from models.object import BathroomObject
                        bathroom_obj = BathroomObject(obj_type,  obj_width, obj_depth, obj_height, shadow)
                        
                        # Validate placement using the constraint validator
                        is_valid = validator.validate_placement(bathroom_obj, (x, y), bathroom)
                    else:
                        # Legacy validation
                        is_valid = is_valid_placement((x, y, obj_width, obj_depth,obj_height), placed_objects, shadow, room_width, room_depth, door_wall)
                        
                    if is_valid:
                        if ("bathtub" or "asymmetrical bathtub") not in object_positions or check_bathtub_shadow((x, y, obj_width, obj_depth,obj_height), placed_objects, shadow, room_width, room_depth, object_positions, obj_type):
                            if (obj_type == "sink"  or obj_type == "toilet"   or obj_type == "double sink") and not check_door_sink_placement((x, y, obj_width, obj_depth), placed_objects, windows_doors, room_width, room_depth, obj_type):
                                placed = False
                            elif windows_doors_overlap(windows_doors, x, y, obj_width, obj_depth, obj_height):
                                
                                placed = False

                            else :
                                placed = True
                                x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions,door_wall)
                                # x, y, obj_width, obj_depth = adjust_object_placement((x, y, obj_width, obj_depth),shadow, room_width, room_depth, placed_objects,min_space=30)
                                object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                                #fig = visualize_room_with_shadows_3d(bathroom_size, object_positions, windows_doors)
                                #st.pyplot(fig)
                                placed_objects.append((x, y, obj_width, obj_depth, shadow ))
                            break
                    # if obj_type == "toilet":
                    #     toilet_placed = is_valid_placement((x, y, obj_width, obj_depth), placed_objects,shadow, room_width, room_depth)
                    #     if toilet_placed:
                    #         if "bathtub" not in object_positions or check_bathtub_shadow((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, object_positions, obj_type):
                    #             if windows_doors_overlap(windows_doors, x, y, z, obj_width, obj_depth, obj_height, room_width, room_depth, shadow):
                    #                 placed = False
                    #             else :
                    #                 placed = True
                                
                    #             x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions )
                    #             object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                    #             #fig = visualize_room_with_shadows_3d(bathroom_size, object_positions, windows_doors)
                    #             #st.pyplot(fig)
                    #             placed_objects.append((x, y, obj_width, obj_depth, shadow ))

                    #             break
                        

                if not placed:
                    object_positions = optimization(object_positions, bathroom_size, windows_doors)
                    # try to get the last three objects, and resize the objects
                    
                    # last_object = placed_objects[-1]
                    # last_object_type = object_positions[-1][-4]
                    # modified_object = resize_object(last_object, room_width, room_depth, last_object_type)
                    # x,y,width,depth = modified_object
                    # # modify the last object in the list
                    # object_positions[-1] = (x,y,width,depth, last_object[4], last_object[5], last_object[6], last_object[7], last_object[8])
                    # placed_objects[-1] = (x,y,width,depth, last_object[4], last_object[5], last_object[6], last_object[7], last_object[8])
                    print(f"Could not place object {obj_type} due to space limitations.")
            
        object_positions = optimization(object_positions, bathroom_size, windows_doors)
        print("Optimization done")
        object_positions = maximize_object_sizes(object_positions, bathroom_size, OBJECT_TYPES)
        print("Maximization done")
        # fill wall with cabinets
        # object_positions = place_cabinets_against_walls(object_positions, bathroom_size, windows_doors)
        # print("Cabinet placement done")
        return object_positions