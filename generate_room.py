


# READ OBJECT TYPES FROM FILE
import json
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
from optimization_file import optimize_object, optimization, maximize_object_sizes, fill_wall_with_cabinets, place_cabinets_against_walls
from visualization_file import visualize_room_with_shadows_3d
from utils_file import check_valid_room,check_distance_from_wall,is_corner_placement_sink, check_which_wall, check_distance, check_bathtub_shadow,adjust_object_placement_pos, convert_values, adjust_object_placement, is_valid_placement, get_available_walls, windows_doors_overlap, check_overlap, sort_objects_by_size, generate_random_size,  windows_doors_overlap, check_which_wall_for_door, get_walls_parallel_to_doors, OBJECT_TYPES
from validation import get_constraint_validator
import numpy as np
from utils_file import check_door_sink_placement
class ObjectType:
    """Defines the constraints for different object types."""
    def __init__(self, name, must_be_corner, shadow_space, size_range, must_be_against_wall):
        self.name = name
        self.must_be_corner = must_be_corner
        self.shadow_space = shadow_space  # How much space the shadow takes up on the top and sides
        self.size_range = size_range  # (min_width, max_width, min_depth,max_depth,min_height, max_height)
        self.optimal_size = size_range  # (optimal_width, optimal_depth, optimal_height)
        self.must_be_against_wall = must_be_against_wall


room_height = 280



def fit_objects_in_room(bathroom_size, object_list, windows_doors, OBJECT_TYPES, attempt=1000, validator=None):
    door_wall = ""
    for dor in windows_doors:
        if "door" in dor[0].lower():
            door_wall = dor[1]
    room_width, room_depth = bathroom_size
    placed_objects = []
    object_positions = []
    door_walls = []
    for i in windows_doors:
        if "door" in i[0].lower():
            wall = check_which_wall_for_door((i[2],i[3],i[4],i[5]), room_width, room_depth)
            door_walls.append(wall)

    # Define priority order for bathroom objects (higher index = higher priority)

    
    # Check if both "Sink" and "Double Sink" are in the object list
    has_sink = "Sink" in object_list or "sink" in object_list
    has_double_sink = "Double Sink" in object_list or "double sink" in object_list
    
    # If both types of sinks are present, choose which one to keep
    filtered_object_list = object_list.copy()
    if has_sink and has_double_sink:
        # For small bathrooms (< 300x300 cm), always keep the regular sink
        if room_width < 300 or room_depth < 300:
            sink_to_keep = "Sink"
            filtered_object_list.remove("double sink")
            print(f"Small bathroom detected ({room_width}x{room_depth}). Keeping only regular Sink.")
        else:
            # For larger bathrooms, randomly choose which sink type to keep
            sink_to_keep = random.choice(["Sink", "double sink"])
            if sink_to_keep == "Sink":
                filtered_object_list.remove("double sink")
            else:
                filtered_object_list.remove("sink")
            print(f"Larger bathroom detected. Keeping only: {sink_to_keep}")
    
    
    
    # Sort objects by size (largest first)
    sorted_objects = sort_objects_by_size(filtered_object_list, OBJECT_TYPES)

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
                bathroom_obj = BathroomObject(obj_type,OBJECT_TYPES, obj_width, obj_depth, obj_height, shadow)
                
                # Validate placement using the constraint validator
                is_valid = validator.validate_placement(bathroom_obj, (x, y), bathroom)
            else:
                # Legacy validation
                is_valid = is_valid_placement((x, y, obj_width, obj_depth,obj_height), placed_objects, shadow, room_width, room_depth, door_wall)
                
            if is_valid:
                if ("bathtub" or "asymmetrical bathtub") not in object_positions or check_bathtub_shadow((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, object_positions, obj_type):
                    if (obj_type == "sink" or obj_type == "toilet"  or obj_type == "double sink") and not check_door_sink_placement((x, y, obj_width, obj_depth), placed_objects, windows_doors, room_width, room_depth, obj_type):
                        placed = False
                    elif windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth, shadow) :
                        placed = False

                    else:
                        placed = True
                        x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions,door_wall)
                        object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                        #fig = visualize_room_with_shadows_3d(bathroom_size, object_positions, windows_doors)
                        #st.pyplot(fig)
                        placed_objects.append((x, y, obj_width, obj_depth, shadow ))
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
                    bathroom_obj = BathroomObject(obj_type,OBJECT_TYPES, obj_width, obj_depth, obj_height, shadow)
                    
                    # Validate placement using the constraint validator
                    is_valid = validator.validate_placement(bathroom_obj, (x, y), bathroom)
                else:
                    # Legacy validation
                    is_valid = is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, door_wall)
                    
                if is_valid:
                    if ("bathtub" or "asymmetrical bathtub") not in object_positions or check_bathtub_shadow((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth, object_positions, obj_type):
                        if (obj_type == "sink"  or obj_type == "toilet"   or obj_type == "double sink") and not check_door_sink_placement((x, y, obj_width, obj_depth), placed_objects, windows_doors, room_width, room_depth, obj_type):
                            placed = False
                        elif windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth,shadow):
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
                #             if windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth, shadow):
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



