from utils.helpers import sort_objects_by_size
from models.layout import Layout
from .placement import DefaultPlacementStrategy
from optimization.scoring import BathroomScoringFunction
import gc
import random
from validation.object_constraints import ObjectConstraintValidator
# algorithms/beam_search.py
class BeamSearch:
    """Implements beam search algorithm for layout generation."""
    
    def __init__(self, bathroom, object_types, beam_width=10):
        self.bathroom = bathroom
        self.object_types = object_types  #only names
        self.beam_width = beam_width
        self.placement_strategy = DefaultPlacementStrategy()
        self.scoring_function = BathroomScoringFunction()
        self.backtracking_strategy = None
        
    def set_placement_strategy(self, strategy):
        """Set the placement strategy."""
        self.placement_strategy = strategy
        
    def set_scoring_function(self, function):
        """Set the scoring function."""
        self.scoring_function = function
        
    def set_backtracking_strategy(self, strategy):
        """Set the backtracking strategy."""
        self.backtracking_strategy = strategy

    def generate(self, objects_to_place, windows_doors):
        """Generate layouts using beam search."""
        # Sort objects by priority
        sorted_objects = sort_objects_by_size(objects_to_place, self.bathroom.width, self.bathroom.depth)

        # Initialize beam with empty layout
        beam = [Layout(self.bathroom.clone(), objects_to_place)]
        
        # Process each object in sorted order
        for obj in sorted_objects:
            
            obj_def = self.bathroom.OBJECT_TYPES[obj]
            validator = ObjectConstraintValidator.get_validator(obj)
            new_candidates = []
            # Generate placement options for the object
            for layout in beam:
                
                # Generate placement options
                placement_options = self.placement_strategy.generate_options(
                    layout, obj, obj_def, self.bathroom.get_size(), layout.bathroom.get_placed_objects(), windows_doors
                )
                if not placement_options and obj == "double sink":
                    obj_def = self.bathroom.OBJECT_TYPES["sink"]
                    #change sorted_objects double sink to sink
                    sorted_objects.remove('double sink')
                    layout.requested_objects.remove('double sink')
                    #place the sink first
                    print("sorted_objects", sorted_objects)

                    sorted_objects.insert(0, "sink")
                    layout.requested_objects.insert(0, "sink")
                    print("sorted_objects", sorted_objects)
                    
                    placement_options = self.placement_strategy.generate_options(
                        layout, "sink", obj_def, self.bathroom.get_size(), layout.bathroom.get_placed_objects(), windows_doors
                    )

                # if not placement_options and self.backtracking_strategy:
                #     # Try backtracking, and move placed objects to create space for the object
                #     backtrack_layouts = self.backtracking_strategy.backtrack(
                #         layout, obj, self.object_types
                #     )
                    
                #     for backtrack_layout in backtrack_layouts:
                #         new_candidates.append(backtrack_layout)
                # else:
                #     # Add each placement option to candidates
                for placement in placement_options:
                    # create a the layout with the object placed
                    new_layout = layout.clone()
                    # add the new object to the layout
                    new_layout.bathroom.add_object(placement)
                    # evaluate the object on the layout
                    #new_layout.score = validator.validate(placement, self.bathroom)
                    new_layout.evaluate(self.scoring_function)
                    # add the new layout to the candidates
                    new_candidates.append(new_layout)

                    # delete candidates with the exact same score and keep only one
                    # if obj == "bathtub" or obj == "shower":
                    #     continue
                    # # delete candidates with the exact same score and keep only one
                    # else:
                    #     seen = set()
                    #     new_candidates = [
                    #         layout for layout in sorted(new_candidates, key=lambda x: x.score, reverse=True)
                    #         if (rounded := round(layout.score, 5)) not in seen and not seen.add(rounded)
                    #     ]
                    # random shuffle the candidates
                    random.shuffle(new_candidates)
            # If no candidates, we're stuck
            if not new_candidates:
                continue
            # 
            if obj.lower() == "bathtub" or obj.lower() == "shower":
                new_candidates = sorted(new_candidates, key=lambda x: x.score, reverse=True)
                
            # delete candidates with the exact same score and keep only one
            else:
                seen = {}
                sorted_canditates = sorted(new_candidates, key=lambda x: x.score, reverse=True)
                for layout in sorted_canditates:
                    rounded = round(layout.score, 5)
                    seen[rounded] = seen.get(rounded, 0) + 1
                    
                    if seen[rounded] <= 2:  # Keep up to 3 layouts with the same score
                        new_candidates.append(layout)

            # Select top layouts for the next iteration
            beam = sorted(new_candidates, key=lambda x: x.score, reverse=True)[:self.beam_width]




        return beam