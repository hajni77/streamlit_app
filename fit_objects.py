import matplotlib.pyplot as plt
import matplotlib.patches as patches
import random
from utils import check_which_wall, check_distance, adjust_object_placement, check_distance_from_wall, convert_values, adjust_object_placement_pos, is_valid_placement, windows_doors_overlap, generate_random_size, sort_objects_by_size, get_available_walls
from generate_room import OBJECT_TYPES

room_height = 280
def fit_objects_in_room(bathroom_size, object_list, windows_doors, attempt = 1000):
    room_width, room_depth = bathroom_size
    placed_objects = []
    object_positions = []
    door_walls = []
    for i in windows_doors:
        if "door" in i[0].lower():
            wall = check_which_wall((i[2],i[3],i[4],i[5]), room_width, room_depth)
            door_walls.append(wall)
    # Sort objects by size (largest first)
    sorted_objects = sort_objects_by_size(object_list)

    for obj_type in sorted_objects:
        obj_def = OBJECT_TYPES[obj_type]
        shadow = obj_def["shadow_space"]
        optimal_size = obj_def["optimal_size"]
        obj_width, obj_depth, obj_height = optimal_size
        placed = False
        # Dictionary to store wall selection counts
        wall_counts = {"top": 0, "bottom": 0, "left": 0, "right": 0}
        for _ in range(attempt):  # Try 100 placements
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
                # if obj_width > obj_depth:  # Landscape orientation
                #     preferred_walls = ["top", "bottom"]
                # else:  # Portrait orientation
                #     preferred_walls = ["left", "right"]
                
                
                if obj_def['name'] == "toilet" or obj_def['name'] == "Toilet":
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
            z = random.randint(0, room_height - obj_height)

            # x, y, obj_width, obj_depth = adjust_object_placement((x, y, obj_width, obj_depth),shadow, room_width, room_depth, min_space=30)  


            if is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth) and obj_type != "toilet":

                if windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth, shadow):
                    placed = False
                else :
                    placed = True
                    x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions)
                    object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                    placed_objects.append((x, y, obj_width, obj_depth, shadow ))
                    print("optimal size was used")
                    print(obj_def['name'])
                    break
            if obj_type == "toilet":
                toilet_placed = is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow,room_width, room_depth)
                if toilet_placed:
                    if windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth, shadow):
                        placed = False
                    else :
                        placed = True
                        x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions )
                        object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                        placed_objects.append((x, y, obj_width, obj_depth, shadow ))
                        print("optimal size was used")
                        print(obj_def['name'])
                        break
                    
            #if obj_type == "bathtub":
                
                #dist,rect_smaller = check_distance(conv_rect, conv_placed_obj)
                
        print(f"  was placed {wall_counts} times.")
        if not placed:
            orig_obj_width, orig_obj_depth,orig_obj_height = generate_random_size(obj_def)
           
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
                    
                    if obj_def['name'] == "toilet":
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
                z = random.randint(0, room_height - obj_height)
                    


                if is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth) and obj_type != "toilet":

                    if windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth,shadow):
                        placed = False
                    else :
                        placed = True
                        x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions )
                        # x, y, obj_width, obj_depth = adjust_object_placement((x, y, obj_width, obj_depth),shadow, room_width, room_depth, placed_objects,min_space=30)
                        object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                        placed_objects.append((x, y, obj_width, obj_depth, shadow ))
                        print("not optimal size was used")
                        print(obj_def['name'])
                        
                        break
                if obj_type == "toilet":
                    toilet_placed = is_valid_placement((x, y, obj_width, obj_depth), placed_objects,shadow, room_width, room_depth)
                    if toilet_placed:
                        if windows_doors_overlap(windows_doors, x, y,z, obj_width, obj_depth, room_width, room_depth, shadow):
                            placed = False
                        else :
                            placed = True
                            x,y,obj_width,obj_depth = optimize_object((x, y, obj_width, obj_depth), shadow, room_width, room_depth,object_positions )
                            object_positions.append((x, y, obj_width, obj_depth, obj_height, obj_def['name'], obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow))
                            placed_objects.append((x, y, obj_width, obj_depth, shadow ))
                            print("not optimal size was used")
                            print(obj_def['name'])
                            break
                    

            if not placed:
                # optimization(object_positions, bathroom_size)
                # try to get the last three objects, and resize the objects
                
                # last_object = placed_objects[-1]
                # last_object_type = object_positions[-1][-4]
                # modified_object = resize_object(last_object, room_width, room_depth, last_object_type)
                # x,y,width,depth = modified_object
                # # modify the last object in the list
                # object_positions[-1] = (x,y,width,depth, last_object[4], last_object[5], last_object[6], last_object[7], last_object[8])
                # placed_objects[-1] = (x,y,width,depth, last_object[4], last_object[5], last_object[6], last_object[7], last_object[8])
                print(f"Could not place object {obj_type} due to space limitations.")

    return object_positions