from utils import check_which_wall,check_distance,adjust_object_placement, check_distance_from_wall, convert_values, adjust_object_placement_pos, is_valid_placement


def optimization(placed_obj, room_sizes):
    room_width, room_depth = room_sizes
    # loop through objects to check if they can be replaced
    extracted_positions = [(item[0], item[1], item[2], item[3], item[-1]) for item in placed_obj]

    for i,obj in enumerate(placed_obj):
        x,y,width,depth,height, _1,_2,_3,shadow = obj
        shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
        # check which wall the object is on
        wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        
        # if wall string contains - then it is a corner
        if wall not in ["top-left", "top-right", "bottom-left", "bottom-right"]:
        # check the distance from the walls perendicular to the wall the object is on
            dist_top,dist_left,dist_right,dist_bottom = check_distance_from_wall((x,y,width,depth), room_width, room_depth, wall,shadow)
            # create dictionary
            dist = {"top":dist_top, "left":dist_left, "right":dist_right, "bottom":dist_bottom}
            # select the wall key with the smallest value
            wall_side,min_dist = min(dist.items(), key=lambda x: x[1])
            
            if min_dist < 30:

                # convert values
                conv_x,conv_y,conv_width,conv_depth, conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom = convert_values((x,y,width,depth), shadow, wall)
                # adjust object placement
                new_x,new_y = adjust_object_placement_pos((conv_x,conv_y,conv_width,conv_depth), (conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom), room_width, room_depth, wall_side)
                # Create a new list excluding the current object
                other_positions = extracted_positions[:i] + extracted_positions[i+1:]
                
                if is_valid_placement((x,y,width,depth), other_positions, (conv_shadow_top, conv_shadow_left, conv_shadow_right, conv_shadow_bottom), room_width, room_depth):
                    # update placed objects
                    del placed_obj[i]

                    placed_obj.insert(i, (new_x, new_y, width, depth, height, _1, _2, _3, shadow))
            ## TODO kiterjesztés méretnövelés

    return placed_obj
        
# optimize only one object  
def optimize_object (rect, shadow, room_width, room_depth, placed_obj):
    rect_wall = check_which_wall(rect, room_width, room_depth)
    x_rect, y_rect, width_rect, depth_rect = rect
    rect_top, rect_left, rect_right, rect_bottom = shadow
    
    conv_rect = convert_values(rect, shadow, rect_wall)
    for i,obj in enumerate(placed_obj):
        x,y,width,depth,height, _1,_2,_3,shadow = obj
        shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
        wall = check_which_wall((x,y,width,depth), room_width, room_depth)
        conv_placed_obj = convert_values((x,y,width,depth), shadow, wall)
        # if rect wall and wall contains the same wall  name
        if rect_wall in wall or wall in rect_wall:
            # check the distance of the objects from each other
            dist,rect_smaller = check_distance(conv_rect, conv_placed_obj)
            if dist < 50 and dist > 0:

                if (rect_smaller):
                    new_x,new_y = adjust_object_placement(conv_rect,  room_width, room_depth, rect_wall, dist)
                elif not(rect_smaller):
                    new_x,new_y = adjust_object_placement(conv_rect,  room_width, room_depth, wall, -dist)
                # Create a new list 
                extracted_positions = [(item[0], item[1], item[2], item[3], item[-1]) for item in placed_obj]
                
                if is_valid_placement((new_x,new_y,width_rect,depth_rect),extracted_positions, (rect_top, rect_left, rect_right, rect_bottom), room_width, room_depth):
                    # update placed objects
                    x_rect = new_x
                    y_rect = new_y
                    break
    return (x_rect,y_rect, width_rect, depth_rect)