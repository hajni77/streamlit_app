
import random

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
    x,y,width,depth = new_rect
    
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
def convert_values(rect, shadow, wall):
    """Converts the values of the object and shadow based on the wall it is closest to."""
    x, y, width, depth = rect

    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
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
        new_shadow_top = 0
        new_shadow_left = 0
        if width > depth:
            new_shadow_right = shadow_left
            new_shadow_bottom = shadow_top
        else:
            new_shadow_right = shadow_top
            new_shadow_bottom = shadow_right
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
        
    elif wall == "top-right":
        new_shadow_top = 0
        new_shadow_right = 0
        if width > depth:   
            new_shadow_left = shadow_right
            new_shadow_bottom = shadow_top
        else:
            new_shadow_left = shadow_top
            new_shadow_bottom = shadow_left
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "bottom-left":
        new_shadow_left = 0
        new_shadow_bottom = 0
        if width > depth:
            new_shadow_right = shadow_right
            new_shadow_top = shadow_top
        else:
            new_shadow_right = shadow_top
            new_shadow_top = shadow_left
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    elif wall == "bottom-right":
        new_shadow_right = 0
        new_shadow_bottom = 0
        if width > depth:
            new_shadow_left = shadow_left
            new_shadow_top = shadow_top
        else:
            new_shadow_left = shadow_top
            new_shadow_top = shadow_right
        return x, y, width, depth, new_shadow_top, new_shadow_left, new_shadow_right, new_shadow_bottom
    else:
        return x, y, width, depth, shadow_top, shadow_left, shadow_right, shadow_bottom
        
# Check if two rectangles overlap
def check_overlap(rect1, rect2):
    rect1_left = rect1[0]
    rect1_right = rect1[0] + rect1[3]
    rect1_top = rect1[1]
    rect1_bottom = rect1[1] + rect1[2]

    rect2_left = rect2[0]
    rect2_right = rect2[0] + rect2[3]
    rect2_top = rect2[1]
    rect2_bottom = rect2[1] + rect2[2]
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
def is_valid_placement(new_rect, placed_rects, shadow_space, room_width, room_depth):
    """Ensures the new object does not overlap with existing objects or shadows."""

    
    shadow_top, shadow_left, shadow_right, shadow_bottom = shadow_space  # Extract shadow values
    new_rect_wall = check_which_wall(new_rect, room_width, room_depth)
    #convert values
    conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values(new_rect, shadow_space,new_rect_wall )
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
        r_conv_x, r_conv_y, r_conv_width, r_conv_depth, r_conv_shadow_top, r_conv_shadow_left, r_conv_shadow_right, r_conv_shadow_bottom = convert_values(rect_sizes, r_shadow, placed_rect_wall)
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

# without sink the room is invalid
def check_valid_room(placed_obj):
    """Check if the room is valid."""
    for obj in placed_obj:
        name = obj[5]
        if name == "sink" or name == "Sink" or name == "double_sink" or name =="Double Sink":
            return True
    print("No sink in the room")
    return False

def sort_objects_by_size(object_list, OBJECT_TYPES):
    """Sort objects by their maximum possible area (largest first)."""
    return sorted(object_list, key=lambda obj: OBJECT_TYPES[obj]["size_range"][1] * OBJECT_TYPES[obj]["size_range"][3], reverse=True)

def generate_random_size(object_type):
    """Generates a random size within the allowed range for an object."""
    min_w, max_w, min_d, max_d,min_h, max_h = object_type["size_range"]
    return random.randint(min_w, max_w), random.randint(min_d, max_d),random.randint(min_h, max_h)

def windows_doors_overlap(windows_doors, x, y, z,width, depth,  room_width, room_depth, shadow_space):
    new_rect = (x, y, width, depth)
    new_rect_wall = check_which_wall(new_rect, room_width, room_depth)
    conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values(new_rect, shadow_space,new_rect_wall )
    # create squares for shadow space
    shadow_space = [(conv_x - conv_shadow_top, conv_y - conv_shadow_left, conv_width + conv_shadow_left + conv_shadow_right, conv_depth + conv_shadow_top + conv_shadow_bottom)]
    object_space = [(conv_x, conv_y, conv_width, conv_depth)]
    door_shadow=75
    isValid = False
    for wd in windows_doors:
        name, position, wx, wy, wwidth,wheight,parapet = wd
        
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
    
def resize_object(rect,room_width, room_depth, type):
    """Resize the object based on the available space. Give smaller size."""
    obj_def = OBJECT_TYPES[type]
    min_width, max_width = obj_def["size_range"][0], obj_def["size_range"][1]
    min_depth, max_depth = obj_def["size_range"][2], obj_def["size_range"][3]
    x, y, obj_width, obj_depth, shadow = rect
    wall = check_which_wall(rect, room_width, room_depth)
    conv_placed_obj = convert_values((x,y,obj_width,obj_depth), shadow, wall)
    
    
    new_x, new_y , new_width, new_depth = reduce_size(conv_placed_obj, type, (min_width,max_width, min_depth,max_depth))
    
    return new_x, new_y, new_width, new_depth