from utils.helpers import sort_objects_by_size
from models.layout import Layout
from .placement import DefaultPlacementStrategy
from optimization.scoring import BathroomScoringFunction
import gc
import random
import uuid
import time
from utils.timing_logger import TimingContext
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
    def get_bathtub_shower_corner(self, layout):
        """Determine which corner contains the bathtub or shower."""
        placed = layout.bathroom.get_placed_objects()
        for obj in placed:
            return obj["object"].wall

                
        return None
    def _ensure_corner_diversity(self, layouts, min_different_corners=4):
        """
        Select layouts to ensure diversity in bathtub/shower corner placements.
        
        Prioritizes having at least min different_corners different corner placements
        while maintaining high scores.
        
        Args:
            layouts (list): List of Layout objects sorted by score (descending)
            min_different_corners (int): Minimum number of different corners to have (default: 4)
        
        Returns:
            list: Selected layouts with diverse corner placements
        """
        if not layouts:
            return []
        
        # Track which corners we've seen and their best layouts
        corner_to_layouts = {
            'top-left': [],
            'top-right': [],
            'bottom-left': [],
            'bottom-right': [],
            None: []  # Layouts without bathtub/shower in corner
        }
        
        # Group layouts by corner placement
        for layout in layouts:
            corner = self.get_bathtub_shower_corner(layout)
            corner_to_layouts[corner].append(layout)
        
        # Strategy: Ensure we have at least one layout from each corner (if available)
        selected = []
        corners_covered = set()
        
        # Phase 1: Get the best layout from each corner
        for corner in ['top-left', 'top-right', 'bottom-left', 'bottom-right']:
            if corner_to_layouts[corner]:
                # Take the best scoring layout from this corner
                best_from_corner = corner_to_layouts[corner][0]
                selected.append(best_from_corner)
                corners_covered.add(corner)
        
        # Phase 2: If we have less than min different_corners, try to get more diversity
        if len(corners_covered) < min_different_corners:
            # Add more layouts from corners we haven't covered yet
            for corner in ['top-left', 'top-right', 'bottom-left', 'bottom-right']:
                if corner not in corners_covered and corner_to_layouts[corner]:
                    selected.append(corner_to_layouts[corner][0])
                    corners_covered.add(corner)
                    if len(corners_covered) >= min_different_corners:
                        break
        
        # Phase 3: Add second-best from each corner to increase diversity
        for corner in ['top-left', 'top-right', 'bottom-left', 'bottom-right']:
            if len(selected) >= 10:
                break
            if len(corner_to_layouts[corner]) > 1:
                # Add second best from this corner
                selected.append(corner_to_layouts[corner][1])
        
        # Phase 4: Fill remaining slots with best overall scores
        if len(selected) < 10:
            already_selected = set(id(l) for l in selected)
            for layout in layouts:
                if id(layout) not in already_selected:
                    selected.append(layout)
                    if len(selected) >= 10:
                        break
        
        return selected[:10]
    
    def generate(self, objects_to_place, windows_doors):
        # Generate a unique ID for this layout generation process
        layout_id = str(uuid.uuid4())[:8]
        room_size = (self.bathroom.width, self.bathroom.depth)
        num_objects = len(objects_to_place)
        
        # Start timing for the entire generation process
        with TimingContext("layout_generation", layout_id=layout_id, room_size=room_size, num_objects=num_objects) as tc:
            # Sort objects by priority
            sorted_objects = sort_objects_by_size(objects_to_place, self.bathroom.width, self.bathroom.depth)
            
            # Initialize beam with empty layout
            beam = [Layout(self.bathroom.clone(), objects_to_place)]
            
            # Add additional info to the timing log
            tc.add_info({"beam_width": self.beam_width})
        
        # Process each object in sorted order
        for obj in sorted_objects:
            
            obj_def = self.bathroom.OBJECT_TYPES[obj]
            validator = ObjectConstraintValidator.get_validator(obj)
            new_candidates = []
            start_time = time.time()
            # Generate placement options for the object
            for layout in beam:
                # Generate placement options
                from utils.timing_logger import log_time
                start_time = time.time()
                placement_options = self.placement_strategy.generate_options(
                    layout, obj, obj_def, self.bathroom.get_size(), layout.bathroom.get_placed_objects(), windows_doors
                )
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                log_time(
                    operation="placement_option_generation",
                    duration_ms=duration_ms,
                    layout_id=f"beam_{beam.index(layout)}",
                    room_size=(self.bathroom.width, self.bathroom.depth),
                    num_objects=len(layout.bathroom.get_placed_objects()) + 1,
                    additional_info={"object_type": obj, "num_options": len(placement_options) if placement_options else 0}
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
                    from utils.timing_logger import log_time
                    start_time = time.time()
                    new_layout.evaluate(self.scoring_function, True)
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    log_time(
                        operation="layout_scoring",
                        duration_ms=duration_ms,
                        layout_id=f"candidate_{len(new_candidates)}",
                        room_size=(self.bathroom.width, self.bathroom.depth),
                        num_objects=len(new_layout.bathroom.get_placed_objects()),
                        additional_info={ "object_added": obj}
                    )
                    # add the new layout to the candidates
                    new_candidates.append(new_layout)
                    
                    # Log individual object placement time
                    # if hasattr(new_layout, "score") and new_layout.score > 0:
                    #     with TimingContext("object_placement", layout_id=layout_id, room_size=room_size, num_objects=1) as tc_obj:
                    #         tc_obj.add_info({"object_type": obj, "position": placement["position"][:2], "score": new_layout.score})

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
                # Only log timing for objects that made it into the final beam
                for idx, selected_layout in enumerate(beam):
                    # Get the objects in this layout
                    placed_objects = selected_layout.bathroom.get_placed_objects()
                    
                    # Find the most recently placed object (should be the current one)
                    for placed_obj in placed_objects:
                        if placed_obj["object"].object_type == obj:
                            # Log timing info for this successful placement
                            with TimingContext("object_placement", layout_id=layout_id, room_size=room_size, num_objects=1) as tc_obj:
                                tc_obj.add_info({
                                    "object_type": obj,
                                    "position": placed_obj["position"][:2],
                                    "score": selected_layout.score,
                                    "beam_position": idx + 1  # Position in the beam (1-10)
                                })
                            break  # Only log once per layout
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
                    max_repeat = 1  # default

                # Gyűjtsük az egyedi layoutokat score és elrendezés szerint
                seen_score = {}
                seen_layout = {}
                corner_diversity = {}  # Track bathtub/shower corner placements
                beam_temp = []

                # Rendezés score szerint
                sorted_candidates = sorted(new_candidates, key=lambda x: x.score, reverse=True)

                for layout in sorted_candidates:
                    # Score deduplikáció
                    rounded_score = round(layout.score, 2)
                    seen_score[rounded_score] = seen_score.get(rounded_score, 0) + 1
                    if seen_score[rounded_score] > 2:
                        continue  # ha túl sok layout van ugyanazzal a score-val, kihagyjuk

                    # Layout deduplikáció
                    sig = self.layout_signature(layout)
                    count = seen_layout.get(sig, 0)
                    if count >= max_repeat:
                        continue  # ha már elértük az ismétlések max számát, kihagyjuk

                    seen_layout[sig] = count + 1
                    beam_temp.append(layout)
                
                # Ensure diversity in bathtub/shower corner placements
                # Prioritize layouts with different corner placements
                beam = self._ensure_corner_diversity(beam_temp, min_different_corners=4)
                
                # If we don't have enough layouts, fill with remaining best scores
                if len(beam) < 10:
                    remaining = [l for l in beam_temp if l not in beam]
                    beam.extend(remaining[:10 - len(beam)])
                
                # Only log timing for objects that made it into the final beam
                for idx, selected_layout in enumerate(beam):
                    # Get the objects in this layout
                    placed_objects = selected_layout.bathroom.get_placed_objects()
                    
                    # Find the most recently placed object (should be the current one)
                    for placed_obj in placed_objects:
                        if placed_obj["object"].object_type == obj:
                            # Log timing info for this successful placement
                            with TimingContext("object_placement", layout_id=layout_id, room_size=room_size, num_objects=1) as tc_obj:
                                tc_obj.add_info({
                                    "object_type": obj,
                                    "position": placed_obj["position"][:2],
                                    "score": selected_layout.score,
                                    "beam_position": idx + 1  # Position in the beam (1-10)
                                })
                            break  # Only log once per layout
                
            
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

