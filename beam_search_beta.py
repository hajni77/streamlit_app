def beam_search_layout_generation(bathroom_size, object_list, windows_doors, OBJECT_TYPES, beam_width=5):
    """
    Generate bathroom layouts using beam search to explore multiple placement options.
    
    Args:
        bathroom_size: (width, depth) of the bathroom
        object_list: List of objects to place
        windows_doors: List of windows and doors
        OBJECT_TYPES: Dictionary of object type definitions
        beam_width: Number of candidate layouts to maintain (default: 5)
        
    Returns:
        List of top layouts sorted by score
    """
    room_width, room_depth = bathroom_size
    
    # Sort objects by size/priority
    sorted_objects = sort_objects_by_size(object_list, OBJECT_TYPES)
    
    # Initialize beam with a single empty layout
    beam = [{"placed_objects": [], "object_positions": [], "score": 0}]
    
    # Process each object
    for obj_type in sorted_objects:
        obj_def = OBJECT_TYPES[obj_type]
        shadow = obj_def["shadow_space"]
        optimal_size = obj_def["optimal_size"]
        
        # Generate new candidate layouts by placing the current object
        new_candidates = []
        
        # For each layout in the current beam
        for layout in beam:
            placed_objects = layout["placed_objects"].copy()
            object_positions = layout["object_positions"].copy()
            
            # Try multiple placements for this object
            placement_options = generate_placement_options(
                obj_type, obj_def, bathroom_size, placed_objects, 
                object_positions, windows_doors, num_options=10  # Try 10 different placements
            )
            
            # Add each placement option to new candidates
            for placement in placement_options:
                new_layout = {
                    "placed_objects": placed_objects + [placement["object"]],
                    "object_positions": object_positions + [placement["position"]],
                    "score": evaluate_partial_layout(
                        placed_objects + [placement["object"]], 
                        object_positions + [placement["position"]], 
                        bathroom_size, OBJECT_TYPES, windows_doors, sorted_objects[:sorted_objects.index(obj_type)+1]
                    )
                }
                new_candidates.append(new_layout)
        
        # Select top beam_width layouts for the next iteration
        beam = sorted(new_candidates, key=lambda x: x["score"], reverse=False)[:beam_width]
        
        # If no valid placements were found for this object in any layout, we have a problem
        if not beam:
            print(f"Could not place object {obj_type} in any layout")
            break
    
    # Return the final beam of layouts
    return beam

def generate_placement_options(obj_type, obj_def, bathroom_size, placed_objects, object_positions, windows_doors, num_options=10):
    """
    Generate multiple placement options for an object with different positions and sizes.
    
    Returns:
        List of placement options, each containing the object and its position
    """
    options = []
    room_width, room_depth = bathroom_size
    shadow = obj_def["shadow_space"]
    
    # Get size variations to try (optimal and some variations within min/max range)
    size_variations = generate_size_variations(obj_def)
    
    # For each size variation, try different positions
    for obj_width, obj_depth, obj_height in size_variations:
        # Try different positions based on constraints
        if obj_def["must_be_corner"]:
            # Try each corner
            corner_positions = [
                (shadow[0], shadow[2]),  # Top-left
                (room_width - obj_depth - shadow[1], shadow[2]),  # Top-right
                (shadow[0], room_depth - obj_width - shadow[3]),  # Bottom-left
                (room_width - obj_depth - shadow[1], room_depth - obj_width - shadow[3])  # Bottom-right
            ]
            
            for x, y in corner_positions:
                if is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth):
                    if not windows_doors_overlap(windows_doors, x, y, 0, obj_width, obj_depth, room_width, room_depth, shadow):
                        options.append({
                            "object": (x, y, obj_width, obj_depth, shadow),
                            "position": (x, y, obj_width, obj_depth, obj_height, obj_def['name'], 
                                        obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow)
                        })
                        
                        # Break early if we have enough options
                        if len(options) >= num_options:
                            return options
        
        elif obj_def["must_be_against_wall"]:
            # Try positions along each wall
            wall_positions = []
            
            # Top wall
            for x in range(shadow[0], room_width - obj_depth - shadow[1], 20):
                wall_positions.append((x, shadow[2]))
            
            # Bottom wall
            for x in range(shadow[0], room_width - obj_depth - shadow[1], 20):
                wall_positions.append((x, room_depth - obj_width - shadow[3]))
            
            # Left wall
            for y in range(shadow[2], room_depth - obj_width - shadow[3], 20):
                wall_positions.append((shadow[0], y))
            
            # Right wall
            for y in range(shadow[2], room_depth - obj_width - shadow[3], 20):
                wall_positions.append((room_width - obj_depth - shadow[1], y))
            
            # Shuffle to get more variety
            import random
            random.shuffle(wall_positions)
            
            for x, y in wall_positions:
                if is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth):
                    if not windows_doors_overlap(windows_doors, x, y, 0, obj_width, obj_depth, room_width, room_depth, shadow):
                        options.append({
                            "object": (x, y, obj_width, obj_depth, shadow),
                            "position": (x, y, obj_width, obj_depth, obj_height, obj_def['name'], 
                                        obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow)
                        })
                        
                        if len(options) >= num_options:
                            return options
        
        else:
            # Free placement - try grid positions
            for x in range(shadow[0], room_width - obj_depth - shadow[1], 20):
                for y in range(shadow[2], room_depth - obj_width - shadow[3], 20):
                    if is_valid_placement((x, y, obj_width, obj_depth), placed_objects, shadow, room_width, room_depth):
                        if not windows_doors_overlap(windows_doors, x, y, 0, obj_width, obj_depth, room_width, room_depth, shadow):
                            options.append({
                                "object": (x, y, obj_width, obj_depth, shadow),
                                "position": (x, y, obj_width, obj_depth, obj_height, obj_def['name'], 
                                            obj_def['must_be_corner'], obj_def['must_be_against_wall'], shadow)
                            })
                            
                            if len(options) >= num_options:
                                return options
    
    return options

def generate_size_variations(obj_def):
    """Generate different size variations for an object within its min/max range"""
    min_width, max_width, min_depth, max_depth, min_height, max_height = obj_def["size_range"]
    optimal_width, optimal_depth, optimal_height = obj_def["optimal_size"]
    
    # Start with optimal size
    variations = [(optimal_width, optimal_depth, optimal_height)]
    
    # Add some variations (smaller and larger)
    width_step = (max_width - min_width) / 4
    depth_step = (max_depth - min_depth) / 4
    
    for w_factor in [0.8, 0.9, 1.1, 1.2]:
        width = max(min_width, min(max_width, optimal_width * w_factor))
        for d_factor in [0.8, 0.9, 1.1, 1.2]:
            depth = max(min_depth, min(max_depth, optimal_depth * d_factor))
            variations.append((width, depth, optimal_height))
    
    return variations

def evaluate_partial_layout(placed_objects, object_positions, room_sizes, object_types_dict, windows_doors, placed_object_types):
    """
    Evaluate a partial layout, considering only the objects that have been placed so far.
    This is a modified version of evaluate_room_layout that works with partial layouts.
    """
    # Use your existing evaluation function, but adapt it to work with partial layouts
    score, details = evaluate_room_layout(object_positions, room_sizes, object_types_dict, windows_doors, placed_object_types)
    return score