import sys
import os
import math

# Add the project root to the path so we can import from other modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.helpers import check_overlap, check_euclidean_distance, is_corner_placement_sink
from utils.helpers import get_opposite_wall, windows_doors_overlap, calculate_space_before_object, check_opposite_walls_distance, calculate_behind_door_space, calculate_overlap_area, calculate_before_door_space
from algorithms.available_space import identify_available_space
from algorithms.available_space import check_enclosed_spaces
class BaseScoringFunction:
    """Base class for room layout scoring functions."""
    
    def __init__(self, room_type):
        self.room_type = room_type
        self.total_score = 0
        self.score_breakdown = {}
    
    # def score(self, layout, room_sizes, windows_doors=None, requested_objects=None):
    #     """Score a layout.
        
    #     Args:
    #         layout: List of placed objects
    #         room_sizes: Tuple of (width, depth) of the room
    #         windows_doors: List of windows and doors
    #         requested_objects: List of specifically requested objects
            
    #     Returns:
    #         float: Total score
    #         dict: Breakdown of scores by category
    #     """
    #     # Base implementation returns 0
    #     self.total_score, self.score_breakdown = self.score(layout, room_sizes, windows_doors, requested_objects)
    #     return self.total_score, self.score_breakdown

    def evaluate(self, layout, windows_doors=None, requested_objects=None):
        """Evaluate the layout using the provided scoring function.
        
        Args:
            layout: List of placed objects
            room_sizes: Tuple of (width, depth) of the room
            windows_doors: List of windows and doors
            requested_objects: List of specifically requested objects
            
        Returns:f
            float: Total score
        """

        self.score, self.score_breakdown = self.score(layout,  windows_doors, requested_objects)
        return self.score, self.score_breakdown


class BathroomScoringFunction(BaseScoringFunction):
    """Scoring function for bathroom layouts."""
    
    def __init__(self, room_type="bathroom"):
        super().__init__(room_type)

    def evaluate(self, layout, requested_objects=None,windows_doors=None ):
        """Evaluate the layout using the provided scoring function.
        
        Args:
            layout: List of placed objects
            room_sizes: Tuple of (width, depth) of the room
            windows_doors: List of windows and doors
            requested_objects: List of specifically requested objects
            
        Returns:f
            float: Total score
        """
        self.total_score, self.score_breakdown = self.score(layout)

          
    def _extract_object_properties(self, obj):
        """Extract standardized properties from an object regardless of its structure.
        
        Args:
            obj: Object to extract properties from (dict, tuple, or object with attributes)
            
        Returns:
            tuple: (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow, wall)
                  or None if properties cannot be extracted
        """
        # Case 1: It's a tuple with (object_info, position)
        if isinstance(obj, tuple) and len(obj) == 2:
            object_info, position = obj
            if isinstance(object_info, dict) and isinstance(position, tuple):
                name = object_info.get('name', 'Unknown')
                must_be_corner = object_info.get('must_be_corner', False)
                must_be_against_wall = object_info.get('must_be_against_wall', False)
                shadow = object_info.get('shadow', (0, 0, 0, 0))
                wall = object_info.get('wall', 'unknown')
                
                if len(position) >= 5:
                    x, y, width, depth, height = position[:5]
                else:
                    x, y = position[:2] if len(position) >= 2 else (0, 0)
                    width = position[2] if len(position) > 2 else 0
                    depth = position[3] if len(position) > 3 else 0
                    height = position[4] if len(position) > 4 else 0
                return (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow, wall)
        
        # Case 2: It's a tuple with all values
        elif isinstance(obj, tuple) and len(obj) >= 10:
            return obj[:10]  # Return first 10 elements
        
        # Case 3: It's a dictionary
        elif isinstance(obj, dict):
            x = obj.get('x', 0)
            y = obj.get('y', 0)
            width = obj.get('width', 0)
            depth = obj.get('depth', 0)
            height = obj.get('height', 0)
            name = obj.get('name', 'Unknown')
            must_be_corner = obj.get('must_be_corner', False)
            must_be_against_wall = obj.get('must_be_against_wall', False)
            shadow = obj.get('shadow', (0, 0, 0, 0))
            wall = obj.get('wall', 'unknown')
            return (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow, wall)
        
        # Case 4: It's an object with attributes
        elif hasattr(obj, 'position') and hasattr(obj, 'name'):
            x, y = obj.position if obj.position else (0, 0)
            width = obj.width if hasattr(obj, 'width') else 0
            depth = obj.depth if hasattr(obj, 'depth') else 0
            height = obj.height if hasattr(obj, 'height') else 0
            name = obj.name
            must_be_corner = obj.must_be_corner if hasattr(obj, 'must_be_corner') else False
            must_be_against_wall = obj.must_be_against_wall if hasattr(obj, 'must_be_against_wall') else False
            shadow = obj.shadow if hasattr(obj, 'shadow') else (0, 0, 0, 0)
            wall = obj.wall if hasattr(obj, 'wall') else 'unknown'
            return (x, y, width, depth, height, name, must_be_corner, must_be_against_wall, shadow, wall)
        
        # Can't extract properties
        return None
        
    def _get_corners(self, x, y, width, depth):
        """Get the four corners of a rectangular object."""
        return [
            (x, y),                   # top-left
            (x, y + width),           # top-right
            (x + depth, y),           # bottom-left
            (x + depth, y + width)    # bottom-right
        ]

    def _min_corner_distance(self, corners1, corners2):
        """Calculate minimum distance between corners of two objects."""
        return min(
            math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
            for c1 in corners1 for c2 in corners2
        )
    
    def score(self, layout):
        """Score a bathroom layout based on various criteria.
        
        Args:
            layout: Layout object or list of positions
            windows_doors: List of windows and doors
            requested_objects: List of specifically requested objects
            
        Returns:
            float: Total score
            dict: Breakdown of scores by category
        """
        placed_objects = layout.bathroom.get_placed_objects()
        windows_doors = layout.bathroom.windows_doors
        room_width, room_depth, room_height = layout.bathroom.get_size()
        requested_objects = layout.requested_objects  
        total_score = 0
        scores = {}
        
    

        # # check space
        available_space = identify_available_space(placed_objects, (room_width, room_depth), grid_size=1, windows_doors=windows_doors)
        available_space_without_shadow = available_space['without_shadow']
        
        # check enclosed spaces
        if check_enclosed_spaces(available_space_without_shadow, room_width, room_depth):
            scores["enclosed_spaces"] = 0
        else:
            scores["enclosed_spaces"] = 10


        # 1. Check for overlapping objects (critical constraint)
        no_overlap_score = 10
        
        # Check for overlaps between objects
        for i, obj in enumerate(placed_objects):
            x = obj["object"].position[0]
            y = obj["object"].position[1]
            width = obj["object"].width
            depth = obj["object"].depth
            height = obj["object"].height
            shadow = obj["object"].shadow
            name = obj["object"].name
            wall = obj["object"].wall
            
            
            # Check for overlaps with other objects
            for j in range(i + 1, len(placed_objects)):
                other_obj = placed_objects[j]
                other_x = other_obj["object"].position[0]
                other_y = other_obj["object"].position[1]
                other_width = other_obj["object"].width
                other_depth = other_obj["object"].depth
                other_height = other_obj["object"].height
                
                if check_overlap((x, y, width, depth,height), (other_x, other_y, other_width, other_depth,other_height)):
                    no_overlap_score = 0
                    break
            
            # Check for overlaps with windows and doors

            if windows_doors and windows_doors_overlap(windows_doors, x, y, 0,width, depth, height, room_width, room_depth, shadow,name):
                no_overlap_score = 0

        scores["no_overlap"] = no_overlap_score
        total_score += scores["no_overlap"]
        
        # Initialize all scoring variables at once
        wall_corner_score = 10  # Start with max score, reduce if constraints violated
        wall_coverage = {"top": 0, "bottom": 0, "left": 0, "right": 0}
        corner_coverage_score = 0
        corners = ["top-left", "top-right", "bottom-left", "bottom-right"]
        corner_objects = {corner: [] for corner in corners}
        door_sink_score = 10
        sink_score = 0
        sink_symmetrial_door_score = 0
        door_sink_distance_score = 0
        toilet_to_door_score = 0
        corner_toilet_score = 0
        sink_space = 0
        toilet_space = 0
        sink_count = 0
        toilet_count = 0
        requested_score = 0
        shadow_score = 0
        bathtub_placement_score = 0
        hidden_sink_score = 10
        not_enough_space = 10
        # 5. Door Position Constraints
        opposite_wall = ""
        behind_door_space = None
        if windows_doors:
            for door_window in windows_doors:
                if door_window.name.startswith("door"):
                    door_width = door_window.width
                    door_height = door_window.height
                    door_x = door_window.position[0]
                    door_y = door_window.position[1]
                    door_depth = door_window.depth
                    door_wall = door_window.wall
                    
                    hinge = door_window.hinge
                    
                    opposite_wall = get_opposite_wall(door_wall)
                    behind_door_space = calculate_behind_door_space(door_x, door_y, door_width, door_depth, door_wall,hinge,room_width, room_depth)
                    before_door_space = calculate_before_door_space(door_x, door_y, door_width, door_depth, door_wall,hinge,room_width, room_depth)
        # Process all objects in a single loop to collect data for multiple metrics
        for obj in placed_objects:
            x = obj["object"].position[0]
            y = obj["object"].position[1]
            width = obj["object"].width
            depth = obj["object"].depth
            height = obj["object"].height
            shadow = obj["object"].shadow
            name = obj["object"].name
            wall = obj["object"].wall
            # # 2. Wall and Corner Constraints
            # if must_be_against_wall and wall == "middle":
            #     wall_corner_score = 0  # Zero points if wall constraint violated
            
            # if must_be_corner and wall not in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            #     wall_corner_score = 0  # Zero points if corner constraint violated
            
            # 3. Wall Coverage
            if wall == "top-left":
                wall_coverage["top"] += width
                wall_coverage["left"] += depth
            elif wall == "top-right":
                wall_coverage["top"] += width
                wall_coverage["right"] += depth
            elif wall == "bottom-left":
                wall_coverage["bottom"] += width
                wall_coverage["left"] += depth
            elif wall == "bottom-right":
                wall_coverage["bottom"] += width
                wall_coverage["right"] += depth
            else:
                if wall in wall_coverage:
                    wall_coverage[wall] += width if wall in ["top", "bottom"] else depth
            
            # 4. Corner Coverage
            for corner in corners:
                if is_corner_placement_sink(x, y, room_width, room_depth, width, depth):
                    corner_objects[corner].append(obj)
            if check_overlap(before_door_space, (x, y, width, depth )):
                overlap = calculate_overlap_area(before_door_space, (x, y, width, depth))
                if overlap > door_width*door_width-3600:
                    not_enough_space = -50
                if name.lower() == "bathtub":
                    not_enough_space = 10
            # 5. Door Position Constraints
            # if windows_doors:
                
            #     door_width = windows_doors.width
            #     door_height = windows_doors.height
            #     door_x = windows_doors.position[0]
            #     door_y = windows_doors.position[1]
            #     door_depth = windows_doors.depth
            #     door_wall = windows_doors.wall
                
            #     hinge = windows_doors.hinge
                
            #     opposite_wall = get_opposite_wall(door_wall)
            #     behind_door_space = calculate_behind_door_space(door_x, door_y, door_width, door_depth, door_wall,hinge,room_width, room_depth)

                # Sink placement relative to door
            if name.lower() in ["sink", "double sink"]:
                    if wall == opposite_wall:
                        sink_score += 10  # Reward sink opposite door
                        # Check if sink is symmetrically placed relative to door
                        if (door_wall == "top" or door_wall == "bottom"):
                            if (door_y +door_width <= y+width and door_y >= y):
                                sink_symmetrial_door_score += 10
                        elif (door_wall == "left" or door_wall == "right"):
                            if (door_x + door_depth <= x+depth and door_x >= x):
                                sink_symmetrial_door_score += 10
                    if check_overlap(behind_door_space, (x, y, width, depth)):
                        if door_wall != wall:
                            overlap = calculate_overlap_area(behind_door_space, (x, y, width, depth))
                            if overlap:
                                hidden_sink_score = -20
                        if door_wall == wall:
                            hidden_sink_score -= 20
                    elif door_wall != wall:
                        door_sink_score += 5
                        # Check distance from door to sink
                        if check_euclidean_distance((door_x, door_y, door_width, door_depth), 
                                                  (x, y, width, depth)) < 200:
                            door_sink_distance_score += 10


                # Toilet placement relative to door
            elif name.lower() in ["toilet", "toilet bidet"]:
                        if get_opposite_wall(door_wall) != wall:
                            door_sink_score += 5  # Reward toilet not opposite door
                            # Check if toilet is directly visible from door
                        # if ((door_x <= x+depth and door_x + door_width >= x and 
                        #              door_x - 40 <= x and door_x+door_width+40 >= x+depth) or 
                        #             (door_y <= y+width and door_y + door_width >= y and 
                        #              door_y - 40 <= y and door_y+door_width+40 >= y+width)):
                        #             toilet_to_door_score = -10
                        if wall in ["top-left", "top-right", "bottom-left", "bottom-right"]:
                            corner_toilet_score = 10
                        else:
                            corner_toilet_score = 0
                                
                        # 11. Free space in front of key fixtures - toilet
                        space = calculate_space_before_object(obj, placed_objects, (room_width, room_depth, room_height))
                        toilet_space += space
                        toilet_count += 1
                
                        if door_wall == wall:
                            door_sink_score += 5  # Reward toilet on same wall as door (hidden)
                        if check_overlap(before_door_space, (x, y, width, depth)):
                            toilet_to_door_score += -40
                        if check_overlap(behind_door_space, (x, y, width, depth)):
                            overlap = calculate_overlap_area(behind_door_space, (x, y, width, depth))
                            if overlap == width*depth:
                                toilet_to_door_score += 20
                                if door_wall == wall:
                                    toilet_to_door_score += 20
                            elif door_wall == wall:
                                toilet_to_door_score += 10

                        
            # # 6. Toilet in corner (preferred placement)
            # if name.lower() in ["toilet", "toilet bidet"]:
            #     if wall in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            #         corner_toilet_score = 10
            #     else:
            #         corner_toilet_score = 0
                    
            #     # 11. Free space in front of key fixtures - toilet
            #     space = calculate_space_before_object(obj, placed_objects, (room_width, room_depth, room_height))
            #     toilet_space += space
            #     toilet_count += 1
                

                
            # 9. Shadow constraints (ensuring proper clearance around fixtures)
            shadow_top, shadow_left, shadow_right, shadow_bottom = shadow
            # Check if shadow is within room boundaries
            if (x - shadow_top >= 0 and y - shadow_left >= 0 and
                x + depth + shadow_bottom <= room_width and y + width + shadow_right <= room_depth):
                shadow_score += 1
                
            # 10. Bathtub placement (orientation and position)
            if "bathtub" in name.lower():
                # Get door wall
                door_wall = layout.bathroom.get_door_walls()
                door_opposite_wall = get_opposite_wall(door_wall[0])
                # Check if bathtub is placed appropriately
                if (door_opposite_wall in wall or wall in door_opposite_wall):
                    # Prefer wider dimension along the wall
                    if (width > depth and door_opposite_wall in ["top", "bottom"] )or (width < depth and door_opposite_wall in ["left", "right"]):
                        bathtub_placement_score = 10
                    else:
                        bathtub_placement_score = 0
                else:
                    bathtub_placement_score = 10
                    
            # 11. Free space in front of key fixtures - sink
            if name.lower() in ["sink", "double sink"]:
                space = calculate_space_before_object(obj, placed_objects, (room_width, room_depth, room_height))
                sink_space += space
                sink_count += 1
        # 8. Requested objects (fulfilling user requirements)
        if requested_objects and name.lower() in [req_obj.lower() for req_obj in requested_objects]:
            requested_score += 1
        # Calculate wall coverage percentage and score
        wall_coverage_score = 0
        for wall in wall_coverage:
            if wall in ["top", "bottom"]:
                coverage_percent = (wall_coverage[wall] / room_depth) * 100
            elif wall in ["left", "right"]:
                coverage_percent = (wall_coverage[wall] / room_width) * 100
            else:
                continue
                
            if coverage_percent >= 70:  # Reward for good wall coverage
                wall_coverage_score += 5
                
        # Reward for having objects in corners
        for corner, objects in corner_objects.items():
            if objects:
                corner_coverage_score += 2.5
                
        # 7. Object Spacing (appropriate distances between fixtures)
        spacing_score = len(placed_objects) * 10
        
        # Calculate spacing between objects
        for i, obj1 in enumerate(placed_objects):
            obj1 = obj1['object']
            x1, y1 =obj1.position[:2]
            width1, depth1 = obj1.width, obj1.depth
            corners1 = self._get_corners(x1, y1, width1, depth1)

            for j in range(i+1, len(placed_objects)):
                obj2 = placed_objects[j]['object']
                x2, y2 = obj2.position[:2]
                width2, depth2 = obj2.width, obj2.depth
                corners2 = self._get_corners(x2, y2, width2, depth2)

                # Calculate minimum corner-to-corner distance
                min_dist = self._min_corner_distance(corners1, corners2)
                if 10 < min_dist < 30:  # Too much free space
                    spacing_score -= 5
        
        # Normalize door_sink_score
        door_sink_score = door_sink_score / 15 * 10
        
        # Add all scores to the scores dictionary
        scores["wall_corner_constraints"] = wall_corner_score
        #scores["wall_coverage"] = min(wall_coverage_score, 10)
        scores["corner_coverage"] = corner_coverage_score
        scores["door_sink_toilet"] = max(door_sink_score, 0)
        scores["sink_opposite_door"] = max(sink_score, 0)
        scores["sink_symmetrial_door"] = max(sink_symmetrial_door_score, 0)
        scores["door_sink_distance"] = max(door_sink_distance_score, 0)
        scores["toilet_to_door"] = toilet_to_door_score
        scores["corner_toilet"] = corner_toilet_score
        scores["hidden_sink"] = hidden_sink_score
        scores["not_enough_space"] = not_enough_space
        
        if placed_objects:
            scores["spacing"] = max(spacing_score / len(placed_objects), 0)
            scores["shadow_constraints"] = min(shadow_score / len(placed_objects) * 10, 10)
        else:
            scores["spacing"] = 0
            scores["shadow_constraints"] = 0
            
        if requested_objects:
            scores["requested_objects"] = requested_score / len(requested_objects) * 10

        else:
            scores["requested_objects"] = 0
            
        scores["bathtub_placement"] = max(bathtub_placement_score, 0)
        
        # Add all scores to total
        total_score += scores["wall_corner_constraints"]
        #total_score += scores["wall_coverage"]
        total_score += scores["corner_coverage"]
        total_score += scores["door_sink_toilet"]
        total_score += scores["sink_opposite_door"]
        total_score += scores["sink_symmetrial_door"]
        total_score += scores["door_sink_distance"]
        total_score += scores["corner_toilet"]
        total_score += scores["spacing"]
        total_score += scores["requested_objects"]
        total_score += scores["shadow_constraints"]
        total_score += scores["bathtub_placement"]
        total_score += scores["hidden_sink"]
        total_score += scores["not_enough_space"]
        total_score += scores["enclosed_spaces"]
        
        # Calculate average free space for sinks and toilets
        avg_sink_space = sink_space / sink_count if sink_count > 0 else 0
        avg_toilet_space = toilet_space / toilet_count if toilet_count > 0 else 0
        
        # Score based on average free space
        sink_space_score = min(10, avg_sink_space / 600) if avg_sink_space > 0 else 0
        toilet_space_score = min(10, avg_toilet_space / 600) if avg_toilet_space > 0 else 0
        
        #scores["sink_free_space"] = sink_space_score
        scores["toilet_free_space"] = toilet_space_score if toilet_count > 0 else 0
        
        #total_score += scores["sink_free_space"]
        if toilet_count > 0:

                total_score += scores["toilet_free_space"]
                total_score += scores["toilet_to_door"]
        
        # 12. Check minimum distance between objects on opposite walls
        has_sufficient_distance, violations = check_opposite_walls_distance(placed_objects, (room_width, room_depth, room_height), min_distance=60)
        
        if has_sufficient_distance:
            scores["opposite_walls_distance"] = 10
        else:
            scores["opposite_walls_distance"] = 0
        
        total_score += scores["opposite_walls_distance"]

        
        # Critical constraints check - if any critical constraint is violated, score is 0
        if (scores["no_overlap"] == 0 or 
            scores["wall_corner_constraints"] == 0 or 
            scores["opposite_walls_distance"] < 5) or scores["enclosed_spaces"] == 0 :
            total_score = 0
        else:
            # Normalize score to be between 0-100
            total_score = (total_score / len(scores)) * 10
        
        # Additional penalty for poor door-sink-toilet arrangement
        if scores["door_sink_toilet"] == 0 or scores["sink_opposite_door"] == 0 or scores["toilet_to_door"] < 0:
            total_score = max(total_score - 10, 0)
        
        # According to project requirements, layouts with accessibility scores < 4 are rejected
        if total_score < 4:
            total_score = 0
        self.total_score = total_score
        self.score_breakdown = scores
        return self.total_score, self.score_breakdown



        
class BedroomScoringFunction(BaseScoringFunction):
    """Scoring function for bedroom layouts."""

    def __init__(self, room_type="bedroom"):
        super().__init__(room_type)

    def score(self, layout, room_sizes, windows_doors=None, requested_objects=None):
        """Score a bedroom layout."""
        # Implement bedroom-specific scoring logic
        return 0, {}


class KitchenScoringFunction(BaseScoringFunction):
    """Scoring function for kitchen layouts."""
    
    def __init__(self, room_type="kitchen"):
        super().__init__(room_type)
    
    def score(self, layout, room_sizes, windows_doors=None, requested_objects=None):
        """Score a kitchen layout."""
        # Implement kitchen-specific scoring logic
        return 0, {}


def get_scoring_function(room_type):
    """Factory function to get the appropriate scoring function for a room type.
    
    Args:
        room_type: Type of room (bathroom, bedroom, kitchen, etc.)
        
    Returns:
        A scoring function instance
    """
    scoring_functions = {
        "bathroom": BathroomScoringFunction,
        "bedroom": BedroomScoringFunction,
        "kitchen": KitchenScoringFunction,
    }
    
    return scoring_functions.get(room_type.lower(), BaseScoringFunction)(room_type)


def compare_room_layouts(layouts, criteria=None):
    """Compare multiple room layouts that already have scores and rank them based on multiple criteria.
    
    This function takes pre-scored layouts and compares them based on specified criteria.
    It can be used to rank layouts by different aspects like accessibility, aesthetics,
    or overall score.
    
    Args:
        layouts: List of pre-scored layout options to compare. Each layout should be a tuple or
                dictionary containing at least the layout objects and their score.
        criteria: Optional dictionary of criteria to use for comparison with weights
                 (e.g., {'overall_score': 1.0, 'accessibility': 2.0, 'aesthetics': 1.5})
                 If None, layouts will be sorted by their overall score.
    
    Returns:
        List of layouts sorted by the specified criteria (highest first)
    """
    # If no criteria specified, sort by overall score
    if criteria is None:
        # Assuming each layout has a score attribute or is a tuple with score as second element
        try:
            # Try sorting assuming layouts are objects with a score attribute
            sorted_layouts = sorted(layouts, key=lambda x: x.score if hasattr(x, 'score') else x[1], reverse=True)
        except (AttributeError, IndexError, TypeError):
            # If that fails, try to sort assuming layouts are dictionaries with a 'score' key
            try:
                sorted_layouts = sorted(layouts, key=lambda x: x.get('score', 0) if isinstance(x, dict) else 0, reverse=True)
            except (AttributeError, TypeError):
                # If all else fails, return the layouts unsorted
                print("Warning: Could not sort layouts by score. Check the layout format.")
                return layouts
    else:
        # Sort by weighted criteria
        def calculate_weighted_score(layout):
            total = 0
            weight_sum = 0
            
            # Handle different layout formats
            if hasattr(layout, 'score_breakdown'):
                # Object with score_breakdown attribute
                breakdown = layout.score_breakdown
            elif isinstance(layout, tuple) and len(layout) > 2 and isinstance(layout[2], dict):
                # Tuple with breakdown as third element
                breakdown = layout[2]
            elif isinstance(layout, dict) and 'score_breakdown' in layout:
                # Dictionary with score_breakdown key
                breakdown = layout['score_breakdown']
            else:
                # Can't find breakdown, use overall score
                if hasattr(layout, 'score'):
                    return layout.score
                elif isinstance(layout, tuple) and len(layout) > 1:
                    return layout[1]
                elif isinstance(layout, dict) and 'score' in layout:
                    return layout['score']
                return 0
            
            # Calculate weighted score based on criteria
            for criterion, weight in criteria.items():
                if criterion in breakdown:
                    total += breakdown[criterion] * weight
                    weight_sum += weight
            
            # Return weighted average or original score if no matching criteria
            return total / weight_sum if weight_sum > 0 else (
                layout.score if hasattr(layout, 'score') else 
                layout[1] if isinstance(layout, tuple) and len(layout) > 1 else 
                layout.get('score', 0) if isinstance(layout, dict) else 0
            )
        
        # Sort layouts by weighted score
        sorted_layouts = sorted(layouts, key=calculate_weighted_score, reverse=True)
    
    return sorted_layouts
