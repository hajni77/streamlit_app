
import random
import json
import streamlit as st
import math
OBJECT_TYPES = []
with open('object_types.json') as f:
    OBJECT_TYPES = json.load(f)
# check which wall is the object is on
def check_which_wall(new_rect, room_width, room_depth):
    x,y,width,depth = new_rect
    
    """Check which wall the object is closest to."""
    if x == 0 and y==0:
        return "top-left"
    elif y == room_depth-width and x == 0:
        return "top-right"
    elif x == room_width-depth and y == 0:
        return "bottom-left"
    elif x == room_width-depth and y == room_depth-width:
        return "bottom-right"
    elif x == 0 and y!= 0:
        return "top"
    elif y == 0 and x!=0:
        return "left"
    elif x == room_width-depth and y != 0:
        return "bottom"
    elif y == room_depth-width and x != 0:
        return "right"
    else:
        return "middle"
def check_which_wall_for_door(new_rect, room_width, room_depth):
    x,y,width,depth,height = new_rect
    
    if x == 0 and y==0:
        return "top-left"
    elif y == room_depth-width and x == 0:
        return "top-right"
    elif x == room_width-depth and y == 0:
        return "bottom-left"
    elif x == room_width-depth and y == room_depth-width:
        return "bottom-right"
    elif x == 0 and y!= 0:
        return "top"
    elif y == 0 and x!=0:
        return "left"
    elif y == room_depth and x != 0:
        return "right"
    elif x == room_width and y != 0:
        return "bottom"
    else:
        return "middle"
# only modify shadow values
def convert_values(rect, shadow, wall, door_wall):
    """Converts the values of the object and shadow based on the wall it is closest to."""
    x, y, width, depth = rect

    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
    new_shadow_top = 0
    new_shadow_right = 0
    new_shadow_left = 0
    new_shadow_bottom = 0
    if wall == "top":
        new_shadow_left = shadow_right
        new_shadow_right = shadow_left
        new_shadow_bottom = shadow_top
        new_shadow_top = shadow_bottom
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "right":
        new_shadow_right = shadow_bottom
        new_shadow_top = shadow_right
        new_shadow_bottom = shadow_left
        new_shadow_left = shadow_top
        return x, y, width, depth,  new_shadow_top, new_shadow_left,new_shadow_right, new_shadow_bottom
    elif wall == "left":
        new_shadow_left = shadow_bottom
        new_shadow_top = shadow_left
        new_shadow_bottom = shadow_right
        new_shadow_right = shadow_top
        return x, y, width, depth,  new_shadow_top, new_shadow_left,new_shadow_right, new_shadow_bottom 
    elif wall == "bottom":
        return x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom
    elif wall == "top-left":
        if width > depth or door_wall == "bottom" or door_wall == "left":
            new_shadow_right = shadow_left
            new_shadow_bottom = shadow_top
        if width < depth or door_wall == "right" or door_wall == "top":
            new_shadow_right = shadow_top
            new_shadow_bottom = shadow_right

        
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
        
    elif wall == "top-right":
    
        if width > depth or door_wall == "bottom" or door_wall == "right":   
            new_shadow_left = shadow_right
            new_shadow_bottom = shadow_top
        if width < depth or door_wall == "left" or door_wall == "top":
            new_shadow_left = shadow_top
            new_shadow_bottom = shadow_left
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "bottom-left":
        if width > depth or door_wall == "top" or door_wall == "left":
            new_shadow_right = shadow_right
            new_shadow_top = shadow_top
        if width < depth or door_wall == "right" or door_wall == "bottom":
            new_shadow_right = shadow_top
            new_shadow_top = shadow_left
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "bottom-right":
        if width > depth or door_wall == "top" or door_wall == "right":
            new_shadow_left = shadow_left
            new_shadow_top = shadow_top
        if width < depth or door_wall == "bottom" or door_wall == "left":
            new_shadow_left = shadow_top
            new_shadow_top = shadow_right
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    else:
        return x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom
def convert_shadows(shadows, wall):
    shadow_top, shadow_left, shadow_right, shadow_bottom = shadows
    if wall == "top":
        new_shadow_left = shadow_right
        new_shadow_right = shadow_left
        new_shadow_bottom = shadow_top
        new_shadow_top = shadow_bottom
        return new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "right":
        new_shadow_right = shadow_bottom
        new_shadow_top = shadow_right
        new_shadow_bottom = shadow_left
        new_shadow_left = shadow_top
        return  new_shadow_top, new_shadow_left,new_shadow_right, new_shadow_bottom
    elif wall == "left":
        new_shadow_left = shadow_bottom
        new_shadow_top = shadow_left
        new_shadow_bottom = shadow_right
        new_shadow_right = shadow_top
        return   new_shadow_top, new_shadow_left,new_shadow_right, new_shadow_bottom 
    elif wall == "bottom":
        return shadow_top, shadow_left, shadow_right, shadow_bottom
    elif wall == "top-left":
        new_shadow_top = 0
        new_shadow_left = 0

        return new_shadow_top, new_shadow_left, shadow_right, shadow_bottom
        
    elif wall == "top-right":
        new_shadow_top = 0
        new_shadow_right = 0

        return  new_shadow_top, shadow_left, new_shadow_right, shadow_bottom
    elif wall == "bottom-left":
        new_shadow_left = 0
        new_shadow_bottom = 0

        return shadow_top, new_shadow_left, shadow_right, new_shadow_bottom
    elif wall == "bottom-right":
        new_shadow_right = 0
        new_shadow_bottom = 0

        return shadow_top, shadow_left, new_shadow_right, new_shadow_bottom
    else:
        return  shadow_top, shadow_left, shadow_right, shadow_bottom       
# Check if two rectangles overlap
def check_overlap(rect1, rect2):
    rect1_left = rect1[1]
    rect1_right = rect1[1] + rect1[2]
    rect1_top = rect1[0]
    rect1_bottom = rect1[0] + rect1[3]

    rect2_left = rect2[1]
    rect2_right = rect2[1] + rect2[2]
    rect2_top = rect2[0]
    rect2_bottom = rect2[0] + rect2[3]
    # check if the rectangles are inside each other (1 in 2)
    if rect1_left >= rect2_left and rect1_right <= rect2_right and rect1_top >= rect2_top and rect1_bottom <= rect2_bottom:
        return True

    # check if the rectangles are inside each other (2 in 1)
    if rect2_left >= rect1_left and rect2_right <= rect1_right and rect2_top >= rect1_top and rect2_bottom <= rect1_bottom:
        return True
    
    
    # Check if the rectangles overlap
    if (rect1_right <= rect2_left or rect2_right <= rect1_left) or (rect1_bottom <= rect2_top or rect2_bottom <= rect1_top): 
        return False  # No overlap 

    # If none of the above conditions are met, there is an overlap
    return True

# Check if the new object can be placed without overlapping with existing objects or shadows
def is_valid_placement(new_rect, placed_rects, shadow_space, room_width, room_depth,  door_wall):
    """Ensures the new object does not overlap with existing objects or shadows."""

    
    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow_space  # Extract shadow values
    new_rect_wall = check_which_wall(new_rect, room_width, room_depth)
    #convert values
    conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values(new_rect, shadow_space,new_rect_wall,door_wall )
    # check that the object actually fits in the room
    if conv_x < 0 or conv_y < 0 or conv_x + conv_depth > room_width or conv_y + conv_width > room_depth:
        return False  # Object extends outside the room → INVALID
    # create squares for shadow space
    if shadow_top == 0 and shadow_left == 0 and shadow_right == 0 and shadow_bottom == 0:
        shadow_space = [(conv_x, conv_y, conv_width, conv_depth)]
    else:
        shadow_space = [(conv_x - conv_shadow_top, conv_y - conv_shadow_left, conv_width + conv_shadow_left + conv_shadow_right, conv_depth + conv_shadow_top + conv_shadow_bottom)]
    object_space = [(conv_x, conv_y, conv_width, conv_depth)]
     
    for rect in placed_rects:
        rx, ry, r_width, r_depth, r_shadow = rect  # Each placed rect has shadow info
        rect_sizes = (rx, ry, r_width, r_depth)
        
        r_top_shadow, r_left_shadow, r_right_shadow, r_bottom_shadow= r_shadow
        placed_rect_wall = check_which_wall(rect_sizes, room_width, room_depth)
        # convert values
        r_conv_x, r_conv_y, r_conv_width, r_conv_depth, r_conv_shadow_top, r_conv_shadow_left, r_conv_shadow_right, r_conv_shadow_bottom = convert_values(rect_sizes, r_shadow, placed_rect_wall,door_wall)
        if r_top_shadow == 0 and r_left_shadow == 0 and r_right_shadow == 0 and r_bottom_shadow == 0:
            r_shadow_space = [(r_conv_x, r_conv_y, r_conv_width, r_conv_depth)]
        else:
            r_shadow_space = [(r_conv_x - r_conv_shadow_top, r_conv_y - r_conv_shadow_left, r_conv_width + r_conv_shadow_left + r_conv_shadow_right, r_conv_depth + r_conv_shadow_top + r_conv_shadow_bottom)]
        r_object_space = [(r_conv_x, r_conv_y, r_conv_width, r_conv_depth)]

        
        # check if the actual objects overlap (STRICT)
        if check_overlap(object_space[0], r_object_space[0]):
            return False  # Objects themselves overlap → INVALID
        # check if the new object's shadow overlaps an existing OBJECT (STRICT) 
        if check_overlap(shadow_space[0], r_object_space[0]):
            return False
        # check if the existing object's shadow overlaps the new object
        if check_overlap(r_shadow_space[0], object_space[0]):
            return False


    
    return True  # Placement is valid
def check_bathtub_shadow(new_rect,placed_rects, shadow_space,room_width, room_depth, positions, obj_type):
    if obj_type == "bathtub" or obj_type == "asymmetrical bathtub":
        return True
    # search for bathtub
    # check if there is a bathtub
    bathtub_rect = None
    shadow_area = 0
    required_shadow_area = 60 * 90
    bathroom_shadow = (0,0,0,0)
    # search for bathtub

    for object_position in positions:
        if object_position[5] == "Bathtub" or object_position[5] == "Asymmetrical Bathtub":
            bathtub_rect = object_position[0:4]
            x,y,width,depth = bathtub_rect
                
            #convert values
            if width > depth:
                shadow_area = width * 90
                bathroom_shadow = (90,0,0,90)
                bathroom_shadow_space = (x-90, y-0, width, depth+180)
            else:
                shadow_area =  depth * 90
                bathroom_shadow = (0,90,90,0)
                bathroom_shadow_space = (x-0, y-90, width+180, depth)

            if shadow_area < required_shadow_area:
                return False
    for object_position in positions:
        if object_position[5] != "Bathtub" or object_position[5] != "Asymmetrical Bathtub":
            rect = object_position[0:4]
            x,y,width,depth = rect
            rect_shadow_space = (i for i in object_position[8])
            #convert values
            rect_area = width * depth   
            if check_overlap(rect, bathroom_shadow_space):
                # calculate the overlap area
                overlap_area = calculate_overlap_area(bathroom_shadow_space,rect )
                shadow_area = shadow_area - overlap_area 
    # Calculate remaining rectangles after overlap
    remaining_rects = calculate_rect_after_overlap(bathroom_shadow_space, new_rect)
    
    # Calculate total remaining shadow area
    shadow_area = 0
    has_minimum_width = False
    
    for rect in remaining_rects:
        x, y, width, depth = rect
        rect_area = width * depth
        shadow_area += rect_area
        
        # Check if any remaining rectangle has at least 60 cm width or depth
        if width >= 60 or depth >= 60:
            has_minimum_width = True
    
    # Check both total area and minimum width requirements
    if shadow_area < required_shadow_area:
        return False
    
    if not has_minimum_width:
        return False
        
    return True
def check_door_sink_placement(new_rect, placed_objects, windows_doors, room_width, room_depth, object_type):
    """
    Check if a sink is placed behind an inward-opening door on the hinge side.
    This prevents sinks from being blocked by the door or blocking the door's movement.
    
    Args:
        new_rect (tuple): New object being placed (x, y, width, depth)
        placed_objects (list): List of already placed objects
        windows_doors (list): List of windows and doors
        room_width (int): Width of the room
        room_depth (int): Depth of the room
    
    Returns:
        bool: True if placement is valid (no sink behind inward door), False otherwise
    """
    # Check if the new object is a sink, only one object TODO
    hinge_area = None
    # Iterate through all doors
    for door in windows_doors:
        if 'door' in door[0].lower():  # Only check actual doors
            door_type = door[1]  # wall type (top, bottom, left, right)
            door_x, door_y = door[2], door[3]  # position
            door_width = door[4]  # width
            door_way = door[7] if len(door) > 7 else "Inward"  # Default to inward if not specified
            door_hinge = door[8] if len(door) > 8 else "Left"  # Default to left hinge if not specified
            
            # Only check inward-opening doors
            if door_way == "inward" or door_way == "Inward":
                # Calculate the area behind the door hinge (not the entire swing area)
                
                if door_type == "top":
                    if door_hinge == "Left":
                        # Door hinged on left side of the opening
                        hinge_area = (0, door_y+door_width, door_width, door_width)  # Area behind left hinge
                    else:  # right hinge
                        # Door hinged on right side of the opening
                        hinge_area = (0, door_y - door_width, door_width, door_width)  # Area behind right hinge
                
                elif door_type == "bottom":
                    if door_hinge == "Left":
                        # Door hinged on left side of the opening
                        hinge_area = (room_width - door_width, door_y-door_width, door_width, door_width)  # Area behind left hinge
                    else:  # right hinge
                        # Door hinged on right side of the opening
                        hinge_area = (room_width - door_width, door_y + door_width , door_width, door_width)  # Area behind right hinge
                
                elif door_type == "left":
                    if door_hinge == "Left":
                        # Door hinged on top side of the opening
                        hinge_area = (door_x-door_width, 0, door_width, door_width)  # Area behind top hinge
                    else:  # bottom hinge
                        # Door hinged on bottom side of the opening
                        hinge_area = (door_x + door_width , 0, door_width, door_width)  # Area behind bottom hinge
                
                elif door_type == "right":
                    if door_hinge == "Left":
                        # Door hinged on top side of the opening
                        hinge_area = (door_x+door_width, room_depth - door_width, door_width, door_width)  # Area behind top hinge
                    else:  # bottom hinge
                        # Door hinged on bottom side of the opening
                        hinge_area = (door_x - door_width, room_depth - door_width, door_width, door_width)  # Area behind bottom hinge
                
                # If we have a valid hinge area and the new object is a sink, check for overlap
    if hinge_area and  (object_type == "sink" or object_type == "double sink"):

        if check_overlap(new_rect[0:4], hinge_area):
                        
            return False
                
                # # Check existing sinks against the new door's hinge area
                # if not new_obj_is_sink and 'door' in new_rect[5].lower():
                #     new_door_type = new_rect[1]  # wall type
                #     new_door_x, new_door_y = new_rect[2], new_rect[3]  # position
                #     new_door_width = new_rect[4]  # width
                #     new_door_way = new_rect[7] if len(new_rect) > 7 else "inward"  # Default to inward
                #     new_door_hinge = new_rect[8] if len(new_rect) > 8 else "left"  # Default to left hinge
                    
                #     # Only check inward-opening doors
                #     if new_door_way.lower() == "inward":
                #         # Calculate the new door's hinge area
                #         new_hinge_area = None
                        
                #         # Calculate the area behind the new door's hinge (similar to above)
                #         if new_door_type == "top":
                #             if new_door_hinge == "left":
                #                 new_hinge_area = (0, new_door_y+new_door_width, 40, 40)
                #             else:  # right hinge
                #                 new_hinge_area = (0, new_door_y - 40, 40, 40)
                #         elif new_door_type == "bottom":
                #             if new_door_hinge == "left":
                #                 new_hinge_area = (room_width - 40, new_door_y-40, 40, 40)
                #             else:  # right hinge
                #                 new_hinge_area = (room_width - 40, new_door_y + new_door_width, 40, 40)
                #         elif new_door_type == "left":
                #             if new_door_hinge == "left":
                #                 new_hinge_area = (new_door_x-40, 0, 40, 40)
                #             else:  # bottom hinge
                #                 new_hinge_area = (new_door_x + new_door_width , 0, 40, 40)
                #         elif new_door_type == "right":
                #             if new_door_hinge == "left":
                #                 new_hinge_area = (new_door_x+new_door_width, room_depth - 40, 40, 40)
                #             else:  # bottom hinge
                #                 new_hinge_area = (new_door_x - 40, room_depth - 40, 40, 40)
                        
                #         # Check all placed objects for sinks
                #         for obj in placed_objects:
                #             if 'sink' in obj[5].lower() or 'Sink' in obj[5]:
                #                 sink_rect = obj[0:4]
                #                 if new_hinge_area and check_overlap(sink_rect, new_hinge_area):
                #                     return False
    
    return True


def calculate_rect_after_overlap(rect1, rect2):
    """
    Calculate the remaining rectangle(s) after subtracting the intersection of rect2 from rect1.
    
    Args:
        rect1 (tuple): First rectangle (x, y, width, depth)
        rect2 (tuple): Second rectangle (x, y, width, depth)
    
    Returns:
        list: List of remaining rectangles after subtracting the intersection
    """
    # Extract coordinates of rect1
    x1, y1, width1, depth1 = rect1
    x1_end = x1 + depth1
    y1_end = y1 + width1
    
    # Extract coordinates of rect2
    x2, y2, width2, depth2 = rect2
    x2_end = x2 + depth2
    y2_end = y2 + width2
    
    # Check if there's an overlap
    if (x1 >= x2_end or x2 >= x1_end or y1 >= y2_end or y2 >= y1_end):
        # No overlap, return the original rect1
        return [rect1]
    
    # Calculate the intersection rectangle
    intersection_x = max(x1, x2)
    intersection_y = max(y1, y2)
    intersection_x_end = min(x1_end, x2_end)
    intersection_y_end = min(y1_end, y2_end)
    
    # Calculate the remaining rectangles (up to 4 possible rectangles)
    remaining_rects = []
    
    # Top rectangle
    if y1 < intersection_y:
        top_rect = (x1, y1, width1, intersection_y - y1)
        remaining_rects.append(top_rect)
    
    # Bottom rectangle
    if y1_end > intersection_y_end:
        bottom_rect = (x1, intersection_y_end, width1, y1_end - intersection_y_end)
        remaining_rects.append(bottom_rect)
    
    # Left rectangle (excluding any overlap with top and bottom rectangles)
    if x1 < intersection_x:
        left_rect = (x1, intersection_y, intersection_x - x1, intersection_y_end - intersection_y)
        remaining_rects.append(left_rect)
    
    # Right rectangle (excluding any overlap with top and bottom rectangles)
    if x1_end > intersection_x_end:
        right_rect = (intersection_x_end, intersection_y, x1_end - intersection_x_end, intersection_y_end - intersection_y)
        remaining_rects.append(right_rect)
    
    # Filter out any rectangles with zero or negative area
    valid_rects = []
    for rect in remaining_rects:
        rx, ry, rwidth, rdepth = rect
        if rwidth > 0 and rdepth > 0:
            valid_rects.append(rect)
    
    return valid_rects

def is_valid_placement_without_converting(new_rect, placed_rects, shadow_space, room_width, room_depth):
    """Check if a placement is valid without converting coordinates.
    
    This function checks if a placement is valid without converting to wall-relative coordinates.
    """
    x,y,width,depth = new_rect
    new_rect_wall = check_which_wall(new_rect, room_width, room_depth)
    # check that the object actually fits in the room
    if x < 0 or y < 0 or x + depth > room_width or y + width > room_depth:
        return False  # Object extends outside the room → INVALID
    # create squares for shadow space
    if shadow_space == (0, 0, 0, 0):
        shadow_space = [(x, y, width, depth)]
    else:
        shadow_space = [(x - shadow_top, y - shadow_left, width + shadow_left + shadow_right, depth + shadow_top + shadow_bottom)]
    object_space = [(x, y, width, depth)]
    
    for rect in placed_rects:
        rx, ry, r_width, r_depth, r_shadow = rect  # Each placed rect has shadow info
        rect_sizes = (rx, ry, r_width, r_depth)
        
        r_top_shadow, r_left_shadow, r_right_shadow, r_bottom_shadow= r_shadow
        placed_rect_wall = check_which_wall(rect_sizes, room_width, room_depth)
        # convert values
        if r_top_shadow == 0 and r_left_shadow == 0 and r_right_shadow == 0 and r_bottom_shadow == 0:
            r_shadow_space = [(rx, ry, r_width, r_depth)]
        else:
            r_shadow_space = [(rx - r_top_shadow, ry - r_left_shadow, r_width + r_left_shadow + r_right_shadow, r_depth + r_top_shadow + r_bottom_shadow)]
        r_object_space = [(rx, ry, r_width, r_depth)]

        
        # check if the actual objects overlap (STRICT)
        if check_overlap(object_space[0], r_object_space[0]):
            return False  # Objects themselves overlap → INVALID
        # check if the new object's shadow overlaps an existing OBJECT (STRICT) 
        if check_overlap(shadow_space[0], r_object_space[0]):
            return False
        # check if the existing object's shadow overlaps the new object
        if check_overlap(r_shadow_space[0], object_space[0]):
            return False
        
    return True  # Placement is valid

# without sink the room is invalid
def check_valid_room(placed_obj):
    """Check if the room is valid."""
    for obj in placed_obj:
        name = obj[5]
        if name == "sink" or name == "Sink" or name == "double sink" or name =="Double Sink":
            return True
    print("No sink in the room")
    return False

def sort_objects_by_size(object_list, OBJECT_TYPES):
    """Sort objects by their maximum possible area (largest first)."""
    if len(object_list) <= 2:
        # sink will be the first
        if "sink" in object_list[0] or "Sink" in object_list[0]:
            return object_list
        elif "sink" in object_list[1] or "Sink" in object_list[1]:
            return object_list[::-1]
    else:
        objects_list_priority = ["bathtub", "shower", "asymmetrical bathtub", "double sink", "sink", "toilet", "toilet bidet","washing machine", "washing dryer",  "cabinet", "washing machine dryer"]
        # sort object_list by priority
        object_list.sort(key=lambda obj: objects_list_priority.index(obj) if obj in objects_list_priority else len(objects_list_priority), reverse=False)
        return object_list

def generate_random_size(object_type):
    """Generates a random size within the allowed range for an object."""
    min_w, max_w, min_d, max_d,min_h, max_h = object_type["size_range"]
    optimal_size = object_type["optimal_size"]
    opt_width, opt_depth, opt_height = optimal_size
    return random.randint(min_w, opt_width), random.randint(min_d, opt_depth),random.randint(min_h, opt_height)

def windows_doors_overlap(windows_doors, x, y, z, width, depth, height, room_width, room_depth, shadow_space):
    new_rect = (x, y, width, depth)
    door_wall = ""
    for dor in windows_doors:
        door_wall = dor[1]
    new_rect_wall = check_which_wall(new_rect, room_width, room_depth)
    conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values(new_rect, shadow_space,new_rect_wall, door_wall)
    # create squares for shadow space
    shadow_space = [(conv_x - conv_shadow_top, conv_y - conv_shadow_left, conv_width + conv_shadow_left + conv_shadow_right, conv_depth + conv_shadow_top + conv_shadow_bottom)]
    object_space = [(conv_x, conv_y, conv_width, conv_depth)]

    door_shadow=75
    isValid = False
    for wd in windows_doors:
        name, position, wx, wy, wwidth,wheight,parapet ,way, hinge= wd
        # Only check shadow for doors
        if "door" in name.lower():
            # Calculate shadow area based on door position
            if position == "top":

                
                shadow_rect = (wx,wy, wwidth, door_shadow)
            elif position == "bottom":
                shadow_rect = (wx-door_shadow,wy, wwidth, door_shadow)
            elif position == "left":
                shadow_rect = (wx , wy, door_shadow, wwidth)
            elif position == "right":
                shadow_rect = (wx,room_depth-door_shadow,door_shadow, wwidth)
            else:
                continue
            if check_overlap(shadow_rect, object_space[0]):

                return True
     
        if "window" in name.lower():
            # Check if one rectangle is to the left of the other
            if not(wx + wwidth <= x or x + width <= wx):
                return True
            # Check if one rectangle is above the other
            if not(wy + wheight <= y or y + depth <= wy):
                return True

    return False

# Check the distance of the object from the walls
def check_distance_from_wall(rect, room_width, room_depth,wall, shadow):
    """Check the distance of the object from the wall."""
    x,y,width,depth = rect
    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
    if (wall == "top" or wall == "bottom"):
        dist_top =31
        dist_left = y - shadow_left
        dist_right = room_depth - (y + width + shadow_right )
        dist_bottom = 31
    elif (wall == "left" or wall == "right"):
        dist_top = x - shadow_top
        dist_bottom = room_width - (x + depth + shadow_bottom )
        dist_left = 31
        dist_right = 31

    return dist_top,dist_left,dist_right,dist_bottom

# adjust the position of the object 
def adjust_object_placement_pos(new_rect, shadow,room_width, room_depth, wall):
    """Adjusts object placement based on remaining space from walls."""
    
    x, y, width, depth = new_rect 
    shadow_top, shadow_left,shadow_right,shadow_bottom = shadow# Object's original position and size
    new_x, new_y = x, y  # Initialize new position to original position
    if wall == "top":
        new_x = shadow_top
    elif wall == "bottom":
        new_x = room_width - (depth + shadow_bottom)
    elif wall == "left":
        new_y = shadow_left
    elif wall == "right":
        new_y = room_depth - (width + shadow_right)
    return new_x,new_y  # Return original if no adjustment is needed

# Check the distance between two converted rectangles
def check_distance (conv_rect1,conv_rect2):
    x1, y1, width1, depth1, shadow_top1, shadow_left1, shadow_right1, shadow_bottom1 = conv_rect1
    x2, y2, width2, depth2, shadow_top2, shadow_left2, shadow_right2, shadow_bottom2 = conv_rect2
    dist = 0
    
    if x1 < x2:
        # check which greater
        shadow = shadow_bottom1 if shadow_bottom1 > shadow_top2 else shadow_top2
        dist = x2 - (x1 + width1+shadow )
        smaller = True
    elif x1 > x2:
        shadow = shadow_bottom2 if shadow_bottom2 > shadow_top1 else shadow_top1
        dist = x1 - (x2 + width2)
        smaller = False
    elif y1 < y2:
        shadow = shadow_right1 if shadow_right1 > shadow_left2 else shadow_left2
        dist = y2 - (y1 + depth1+shadow)
        smaller = True
    elif y1 > y2:
        shadow = shadow_right2 if shadow_right2 > shadow_left1 else shadow_left1
        dist = y1 - (y2 + depth2+shadow)
        smaller = False
    return dist, smaller
def check_euclidean_distance(rect1, rect2):
    x1, y1, width1, depth1 = rect1
    x2, y2, width2, depth2 = rect2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def adjust_object_placement(conv_rect,  room_width, room_depth, rect_wall, dist):
    """Adjusts object placement based on remaining space from walls."""
    x, y, width, depth , shadow_top, shadow_left,shadow_right,shadow_bottom= conv_rect 
    new_x, new_y = x, y  # Initialize new position to original position
    
    if rect_wall == "top" or rect_wall == "bottom":
        new_y = new_y + dist
    elif rect_wall == "left" or rect_wall == "right":
        new_x = new_x + dist

    return new_x,new_y # Return original if no adjustment is needed

def get_available_walls(door_walls):
    """Get the walls that are available for placing objects."""
    available_walls = ["top", "bottom", "left", "right"]
    if "top" not in door_walls:
        available_walls.remove("bottom")
    if "bottom" not in door_walls:
        available_walls.remove("top")
    if "left" not in door_walls:
        available_walls.remove("right")
    if "right" not in door_walls:
        available_walls.remove("left")
    return available_walls

def reduce_size(conv_placed_obj, size_range):
    """Reduces the size of the object by 10%."""
    min_width, max_width, min_depth, max_depth = size_range
    x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom = conv_placed_obj
    n_width = int(width * 0.9)
    n_depth = int(depth * 0.9)
    if (n_width > min_width and n_depth > min_depth):
        return (x, y, n_width, n_depth)
    else:
        return (x, y, width, depth)
    
def resize_object(rect,room_width, room_depth, type, windows_doors):
    """Resize the object based on the available space. Give smaller size."""
    obj_def = OBJECT_TYPES[type]
    min_width, max_width = obj_def["size_range"][0], obj_def["size_range"][1]
    min_depth, max_depth = obj_def["size_range"][2], obj_def["size_range"][3]
    x, y, obj_width, obj_depth, shadow = rect
    wall = check_which_wall(rect, room_width, room_depth)
    door_wall = ""
    for dor in windows_doors:
        door_wall = dor[1]
    conv_placed_obj = convert_values((x,y,obj_width,obj_depth), shadow, wall, door_wall)
    
    
    new_x, new_y , new_width, new_depth = reduce_size(conv_placed_obj, type, (min_width,max_width, min_depth,max_depth))
    
    return new_x, new_y, new_width, new_depth
def calculate_overlap_area(rect1, rect2):
    x1, y1, width1, depth1 = rect1
    x2, y2, width2, depth2 = rect2
    # calculate the overlap area
    overlap_x = max(0, min(x1 + width1, x2 + width2) - max(x1, x2))
    overlap_y = max(0, min(y1 + depth1, y2 + depth2) - max(y1, y2))
    return overlap_x * overlap_y
    
def is_corner_placement_sink(x, y, room_width, room_depth,  sink_width, sink_depth, corner_threshold=50,):
    """
    Check if an object is placed in a corner of the room.
    
    Args:
        x (int): X coordinate of the object
        y (int): Y coordinate of the object
        room_width (int): Width of the room
        room_depth (int): Depth of the room
        corner_threshold (int): Distance from walls to consider a corner
        
    Returns:
        bool: True if object is in a corner, False otherwise
    """
    return (x < corner_threshold)or \
           (y < corner_threshold) or \
           (x + sink_depth> room_depth - corner_threshold) or \
           (y + sink_width> room_width - corner_threshold)

def get_object_type(obj_name):
    """Get the object type based on the object name."""
    return next((v for v in OBJECT_TYPES.values() if v["name"] == obj_name), None)

def get_opposite_wall(wall):
    if wall == "top":
        return "bottom"
    elif wall == "bottom":
        return "top"
    elif wall == "left":
        return "right"
    elif wall == "right":
        return "left"
    elif wall == "top-left":
        return "bottom-right"
    elif wall == "top-right":
        return "bottom-left"
    elif wall == "bottom-left":
        return "top-right"
    elif wall == "bottom-right":
        return "top-left"
        
def get_walls_parallel_to_doors(door_walls):
    """
    Get walls that are parallel to doors, which are preferred for toilet placement.
    
    Args:
        door_walls (list): List of walls where doors are located
        
    Returns:
        list: Walls that are parallel to doors (preferred for toilet placement)
    """
    parallel_walls = []
    for wall in door_walls:
        if wall in ["top", "bottom"]:
            parallel_walls.extend(["left", "right"])
        elif wall in ["left", "right"]:
            parallel_walls.extend(["top", "bottom"])
    
    # Remove duplicates and return unique walls
    return list(set(parallel_walls))
def calculate_space_before_object(obj, placed_objects, room_size):
    """
    Calculate the space in front of an object toward the opposite wall.
    For objects against a wall, it calculates the free space in the direction away from the wall.
    
    Args:
        obj (tuple): Object to check space for (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow)
        placed_objects (list): List of all placed objects in the room
        room_size (tuple): Room dimensions (width, depth)
        
    Returns:
        float: Amount of free space in front of the object (in cm)
    """
    x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow = obj
    room_width, room_depth = room_size
    
    # Determine which wall(s) the object is against
    against_wall = check_which_wall((x, y, width, depth), room_width, room_depth)
    
    # Calculate the distance to the opposite wall and the free space
    free_space = 0
    if against_wall == "top":
        # Object is against top wall, calculate space toward bottom wall
        total_space_coordinates = (x+depth,y,width,room_width-depth)  # Distance from object to bottom wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2]
                                     
    elif against_wall == "bottom":
        # Object is against bottom wall, calculate space toward top wall
        total_space_coordinates = (0,y,width, room_width-depth)  # Distance from object to top wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2]
                                     
    elif against_wall == "left":
        # Object is against left wall, calculate space toward right wall
        total_space_coordinates = (x,y+width,room_depth-width,depth)  # Distance from object to right wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2]
                   
    elif against_wall == "right":
        # Object is against right wall, calculate space toward left wall
        total_space_coordinates = (x,0,room_depth-width,depth)  # Distance from object to left wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2]


    elif against_wall == "top-left":
        # Object is against top-left wall, calculate space toward bottom-right wall
        total_space_coordinates_left = (x,y+width,room_depth-width,depth) # Distance from object to bottom-right wall
        total_space_coordinates = (x+depth,y,width,room_width-depth)  # Distance from object to bottom-right wall
        free_space = total_space_coordinates_left[3]*total_space_coordinates_left[2] + total_space_coordinates[3]*total_space_coordinates[2]
    elif against_wall == "top-right":
        # Object is against top-right wall, calculate space toward bottom-left wall
        total_space_coordinates= (x+depth,y,width,room_width-depth) # Distance from object to bottom-left wall
        total_space_coordinates_right = (x,0,room_depth-width,depth)   # Distance from object to bottom-right wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2] + total_space_coordinates_right[3]*total_space_coordinates_right[2]
    elif against_wall == "bottom-left":
        # Object is against bottom-left wall, calculate space toward top-right wall
        total_space_coordinates = (0,y,width, room_width-depth) # Distance from object to top-right wall
        total_space_coordinates_left = (x,y+width,room_depth-width,depth) # Distance from object to top-left wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2] + total_space_coordinates_left[3]*total_space_coordinates_left[2]
    elif against_wall == "bottom-right":
        # Object is against bottom-right wall, calculate space toward top-left wall
        total_space_coordinates =(0,y,width, room_width-depth)  # Distance from object to top-left wall
        total_space_coordinates_right = (x,0,room_depth-width,depth) # Distance from object to top-left wall
        free_space = total_space_coordinates[3]*total_space_coordinates[2] + total_space_coordinates_right[3]*total_space_coordinates_right[2]
    # Check for objects in between that reduce free space
    for other_obj in placed_objects:
        if other_obj != obj:
            other_x, other_y, other_width, other_depth, other_height, other_name, other_corner, other_against_wall, other_shadow = other_obj
            if against_wall == "top-left" or against_wall == "bottom-left" :
                if check_overlap(total_space_coordinates_left, (other_x, other_y, other_width, other_depth)):
                    overlap = calculate_overlap_area(total_space_coordinates_left, (other_x, other_y, other_width, other_depth))
                    free_space -= overlap
            elif against_wall == "top-right" or against_wall == "bottom-right" :
                if check_overlap(total_space_coordinates_right, (other_x, other_y, other_width, other_depth)):
                    overlap = calculate_overlap_area(total_space_coordinates_right, (other_x, other_y, other_width, other_depth))
                    free_space -= overlap
            # Check if other object is in the path between this object and left wall
            else:
                if check_overlap(total_space_coordinates, (other_x, other_y, other_width, other_depth)):
                    overlap = calculate_overlap_area(total_space_coordinates, (other_x, other_y, other_width, other_depth))
                    free_space -= overlap
    
    return free_space

def get_nearest_parallel_wall(door, room_width, room_depth):
    if door[1] == "top" or door[1] == "bottom":

        door_y = door[3]
        if door_y < room_depth/2:
            return "left"
        else:
            return "right"
    elif door[1] == "left" or door[1] == "right":
        door_x = door[2]
        if door_x < room_width/2:
            return "top"
        else:
            return "bottom"
    
    return door[1]