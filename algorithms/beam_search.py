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
    def layout_signature(self,layout):
        """Create a unique signature of the layout based on placed objects."""
        placed = layout.bathroom.get_placed_objects()
        # sort for stability

        placed_sorted = sorted(
            [(obj["object"].object_type, round(obj["position"][0], 2), round(obj["position"][1], 2)) for obj in placed]
        )
        return tuple(placed_sorted)
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

                    sorted_objects.insert(0, "sink")
                    layout.requested_objects.insert(0, "sink")
                    
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

            # Ellenőrizzük, hogy minden új candidate 0 score
            all_zero_score = all(layout.score == 0 for layout in new_candidates)

            if all_zero_score:
                # Ha minden score 0, akkor nem helyezünk el új objektumot
                continue  # beam marad változatlan
            if obj.lower() == "bathtub" or obj.lower() == "shower":
                new_candidates = sorted(new_candidates, key=lambda x: x.score, reverse=True)
                beam = new_candidates[:30]
            else:
                # Ha csak néhány score 0, azokat dobjuk el
                new_candidates = [layout for layout in new_candidates if layout.score != 0]

                # Maximális ismétlések szabályozása objektum szám alapján
                num_objects = len(sorted_objects)  # vagy layout.requested_objects
                if num_objects <= 3:
                    max_repeat = 1
                elif num_objects == 4:
                    max_repeat = 2
                else:
                    max_repeat = 3  # default

                # Gyűjtsük az egyedi layoutokat score és elrendezés szerint
                seen_score = {}
                seen_layout = {}
                beam_temp = []

                # Rendezés score szerint
                sorted_candidates = sorted(new_candidates, key=lambda x: x.score, reverse=True)

                for layout in sorted_candidates:
                    # Score deduplikáció
                    rounded_score = round(layout.score, 2)
                    seen_score[rounded_score] = seen_score.get(rounded_score, 0) + 1
                    if seen_score[rounded_score] > 1:
                        continue  # ha túl sok layout van ugyanazzal a score-val, kihagyjuk

                    # Layout deduplikáció
                    sig = self.layout_signature(layout)
                    count = seen_layout.get(sig, 0)
                    if count >= max_repeat:
                        continue  # ha már elértük az ismétlések max számát, kihagyjuk

                    seen_layout[sig] = count + 1
                    beam_temp.append(layout)

                # Top 30 layout kiválasztása
                beam = beam_temp[:30]

            
            # beam = new_candidates
                
            # else:
            #     seen = {}
            #     sorted_canditates = sorted(new_candidates, key=lambda x: x.score, reverse=True)
            #     for layout in sorted_canditates:
            #         print("layout score", layout.score)
            #         rounded = round(layout.score, 2)
            #         seen[rounded] = seen.get(rounded, 0) + 1
                    
            #         if seen[rounded] <= 1:  # Keep up to 3 layouts with the same score
            #             new_candidates.append(layout)



            # Select top layouts for the next iteration
            #beam = sorted(new_candidates, key=lambda x: x.score, reverse=True)[:30]




        return beam

