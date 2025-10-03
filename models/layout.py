

# models/layout.py
class Layout:
    """Represents a specific layout configuration."""
    
    def __init__(self, bathroom,requested_objects):
        self.bathroom = bathroom
        self.score = None
        self.score_breakdown = {}
        self.requested_objects = requested_objects
        
    def clone(self):
        """Create a deep copy of this layout."""
        import copy
        return copy.deepcopy(self)
        
    def evaluate(self, scoring_function, use_cpp_scoring=False):
        """Evaluate the layout using the provided scoring function."""
        if use_cpp_scoring:
            try:
                # Import here to avoid circular import
                from optimization.cpp_scoring.python_wrapper import CppBathroomScoringWrapper
                scorer = CppBathroomScoringWrapper()
                self.score, self.score_breakdown = scorer.score(self)
            except (ImportError, Exception) as e:
                # Fallback to Python scorer if C++ not available
                print(f"[Warning] C++ scorer not available, using Python: {e}")
                self.score, self.score_breakdown = scoring_function.score(self)
        else:
            # Use the provided scoring function (default behavior)
            self.score, self.score_breakdown = scoring_function.score(self)
        
    def get_object_positions(self):
        """Get positions of all objects in the layout."""
        return [(obj.position[0], obj.position[1], obj.width, obj.depth, 
                obj.height, obj.name, obj.object_type["must_be_corner"], 
                obj.object_type["must_be_against_wall"], obj.object_type["shadow_space"]) 
                for obj in self.bathroom.objects]
    def get_room_sizes(self):
        return self.bathroom.get_size()
