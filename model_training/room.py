import numpy as np
import random
import torch

class RoomEnvironment:
    def __init__(self, objects, type_to_onehot):
        self.objects = objects
        self.type_to_onehot = type_to_onehot
        self.num_objects = len(objects)
        self.reset()

    def reset(self):
        self.positions = []
        for obj in self.objects:
            pos = obj.copy()
            if pos[6]:  # movable
                pos[0] += np.random.randint(-10, 10)
                pos[1] += np.random.randint(-10, 10)
            self.positions.append(pos)
        return self._get_state()

    def step(self, action):
        obj_idx = action // 4
        move = action % 4

        dx, dy = 0, 0
        if move == 0: dx = -5
        if move == 1: dx = 5
        if move == 2: dy = -5
        if move == 3: dy = 5

        if self.positions[obj_idx][6]:  # movable
            self.positions[obj_idx][0] += dx
            self.positions[obj_idx][1] += dy

        reward = self._calculate_reward_2()
        done = False
        return self._get_state(), reward, done

    def _get_state(self):
        state = []
        for pos in self.positions:
            x, y, width, depth, height, obj_type, movable, visible, shadows = pos
            type_onehot = self.type_to_onehot[obj_type]
            state.extend([
                x, y, width, depth, height,
                *type_onehot,
                int(movable),
                int(visible),
                *shadows
            ])
        return np.array(state, dtype=np.float32)

    def _calculate_reward(self):
        reward = 0.0
        for i in range(self.num_objects):
            for j in range(i + 1, self.num_objects):
                if not self.positions[i][7] or not self.positions[j][7]:
                    continue
                x1_i, y1_i = self.positions[i][0], self.positions[i][1]
                x2_i, y2_i = x1_i + self.positions[i][2], y1_i + self.positions[i][3]
                x1_j, y1_j = self.positions[j][0], self.positions[j][1]
                x2_j, y2_j = x1_j + self.positions[j][2], y1_j + self.positions[j][3]
                if not (x2_i <= x1_j or x1_i >= x2_j or y2_i <= y1_j or y1_i >= y2_j):
                    overlap_x = max(0, min(x2_i, x2_j) - max(x1_i, x1_j))
                    overlap_y = max(0, min(y2_i, y2_j) - max(y1_i, y1_j))
                    reward -= (overlap_x * overlap_y) * 0.01
        for pos in self.positions:
            center_x = pos[0] + pos[2] / 2
            center_y = pos[1] + pos[3] / 2
            dist_center = np.linalg.norm(np.array([center_x, center_y]) - np.array([128, 128]))
            reward += (1 - dist_center / 128) * 0.1
        return reward
    def _calculate_reward_2(self):
        import numpy as np

        reward = 0.0
        room_w, room_d = 256, 256
        min_clearance = 30

        # 1) Overlap penalty
        for i in range(self.num_objects):
            for j in range(i+1, self.num_objects):
                # only if both objects are visible/movable
                if not (self.positions[i][7] and self.positions[j][7]):
                    continue
                x1,y1,w1,d1 = self.positions[i][:4]
                x2,y2,w2,d2 = self.positions[j][:4]
                if not (x1+w1 <= x2 or x2+w2 <= x1 or y1+d1 <= y2 or y2+d2 <= y1):
                    # compute overlap rectangle
                    ox = max(0, min(x1+w1, x2+w2) - max(x1, x2))
                    oy = max(0, min(y1+d1, y2+d2) - max(y1, y2))
                    reward -= (ox * oy) * 0.01

        # 2) Corner & wall constraints + clearance rewards
        for x,y,w,d,_,_,must_corner,must_wall, _ in self.positions:
            # corner compliance
            at_corner = (x in (0, room_w-w)) and (y in (0, room_d-d))
            reward += 0.1 if must_corner and at_corner else (-0.1 if must_corner else 0)

            # wall adjacency
            at_wall = x==0 or y==0 or x+w==room_w or y+d==room_d
            reward += 0.05 if must_wall and at_wall else (-0.05 if must_wall else 0)

            # clearance from nearest wall
            cd = min(x, y, room_w-(x+w), room_d-(y+d))
            if cd < min_clearance:
                reward -= (min_clearance - cd) * 0.01
            else:
                reward += (cd - min_clearance) / room_w * 0.05

        return reward

    def calculate_layout_reward(object_positions, room_width, room_depth):
        """
        Calculate a reward score for the current room layout using the check_distance function.
        
        Args:
            object_positions: List of tuples containing object positions and properties
            room_width: Width of the room
            room_depth: Depth of the room
            
        Returns:
            float: Reward score for the current layout
        """
        reward = 0.0
        min_clearance = 30  # Minimum clearance between objects
        
        # Reward for proper spacing between objects
        for i in range(len(object_positions)):
            for j in range(i + 1, len(object_positions)):
                obj1 = object_positions[i]
                obj2 = object_positions[j]
                
                # Extract position information
                x1, y1, width1, depth1, height1, name1, must_corner1, must_wall1, shadow1 = obj1
                x2, y2, width2, depth2, height2, name2, must_corner2, must_wall2, shadow2 = obj2
                
                rect1 = (x1, y1, width1, depth1, height1)
                rect2 = (x2, y2, width2, depth2, height2)
                
                # Calculate distance between objects
                dist, smaller = check_distance(rect1, rect2)
                
                # Penalize if objects are too close
                if dist < min_clearance:
                    reward -= (min_clearance - dist) * 0.1
                else:
                    # Reward appropriate spacing
                    reward += min(dist * 0.01, 1.0)  # Cap the reward
        
        # Reward for objects against walls if they should be
        for obj in object_positions:
            x, y, width, depth, height, name, must_corner, must_wall, shadow = obj
            
            # Check if object is against a wall
            against_wall = (x == 0 or y == 0 or x + width == room_width or y + depth == room_depth)
            
            # Reward or penalize based on wall placement
            if must_wall and against_wall:
                reward += 1.0
            elif must_wall and not against_wall:
                reward -= 1.0
            
            # Check if object is in a corner
            in_corner = (x == 0 and y == 0) or (x == 0 and y + depth == room_depth) or \
                    (x + width == room_width and y == 0) or (x + width == room_width and y + depth == room_depth)
            
            # Reward or penalize based on corner placement
            if must_corner and in_corner:
                reward += 2.0
            elif must_corner and not in_corner:
                reward -= 2.0
        
        return reward