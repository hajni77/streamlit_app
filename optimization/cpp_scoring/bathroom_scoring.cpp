#include "bathroom_scoring.h"
#include <iostream>
#include <set>
#include <queue>
#include <algorithm>

namespace bathroom_scoring {

BathroomScoringFunction::BathroomScoringFunction() {}

BathroomScoringFunction::~BathroomScoringFunction() {}

// Get the four corners of a rectangular object
std::vector<std::tuple<double, double>> BathroomScoringFunction::get_corners(
    double x, double y, double width, double depth) const {
    return {
        std::make_tuple(x, y),                  // top-left
        std::make_tuple(x, y + width),          // top-right
        std::make_tuple(x + depth, y),          // bottom-left
        std::make_tuple(x + depth, y + width)   // bottom-right
    };
}

// Calculate minimum distance between corners of two objects
double BathroomScoringFunction::min_corner_distance(
    const std::vector<std::tuple<double, double>>& corners1,
    const std::vector<std::tuple<double, double>>& corners2) const {
    
    double min_dist = std::numeric_limits<double>::max();
    
    for (const auto& c1 : corners1) {
        for (const auto& c2 : corners2) {
            double dx = std::get<0>(c1) - std::get<0>(c2);
            double dy = std::get<1>(c1) - std::get<1>(c2);
            double dist = std::sqrt(dx * dx + dy * dy);
            min_dist = std::min(min_dist, dist);
        }
    }
    
    return min_dist;
}

// Check if two rectangles overlap
bool BathroomScoringFunction::check_overlap(const Rectangle& rect1, const Rectangle& rect2) const {
    return !(rect1.x + rect1.depth <= rect2.x ||
             rect2.x + rect2.depth <= rect1.x ||
             rect1.y + rect1.width <= rect2.y ||
             rect2.y + rect2.width <= rect1.y);
}

// Check if a rectangle overlaps with any in a vector
bool BathroomScoringFunction::check_overlap(const std::vector<Rectangle>& rects, const Rectangle& rect) const {
    for (const auto& r : rects) {
        if (check_overlap(r, rect)) {
            return true;
        }
    }
    return false;
}

// Calculate overlap area between two rectangles
double BathroomScoringFunction::calculate_overlap_area(const Rectangle& rect1, const Rectangle& rect2) const {
    if (!check_overlap(rect1, rect2)) {
        return 0.0;
    }
    
    double x_overlap = std::min(rect1.x + rect1.depth, rect2.x + rect2.depth) - 
                       std::max(rect1.x, rect2.x);
    double y_overlap = std::min(rect1.y + rect1.width, rect2.y + rect2.width) - 
                       std::max(rect1.y, rect2.y);
    
    return x_overlap * y_overlap;
}

// Calculate total overlap area with multiple rectangles
double BathroomScoringFunction::calculate_overlap_area(const std::vector<Rectangle>& rects, const Rectangle& rect) const {
    double total_area = 0.0;
    for (const auto& r : rects) {
        total_area += calculate_overlap_area(r, rect);
    }
    return total_area;
}

// Check if object is placed in a corner
bool BathroomScoringFunction::is_corner_placement(
    double x, double y, double room_width, double room_depth,
    double obj_width, double obj_depth) const {
    
    const double tolerance = 1.0;  // 1cm tolerance
    
    bool at_top = std::abs(x) < tolerance;
    bool at_bottom = std::abs(x + obj_depth - room_width) < tolerance;
    bool at_left = std::abs(y) < tolerance;
    bool at_right = std::abs(y + obj_width - room_depth) < tolerance;
    
    return (at_top && at_left) || (at_top && at_right) || 
           (at_bottom && at_left) || (at_bottom && at_right);
}

// Get opposite wall
std::string BathroomScoringFunction::get_opposite_wall(const std::string& wall) const {
    if (wall == "top") return "bottom";
    if (wall == "bottom") return "top";
    if (wall == "left") return "right";
    if (wall == "right") return "left";
    if (wall == "top-left") return "bottom-right";
    if (wall == "top-right") return "bottom-left";
    if (wall == "bottom-left") return "top-right";
    if (wall == "bottom-right") return "top-left";
    return "unknown";
}

// Calculate space behind door
Rectangle BathroomScoringFunction::calculate_behind_door_space(
    double door_x, double door_y, double door_width, double door_depth,
    const std::string& door_wall, const std::string& hinge,
    double room_width, double room_depth) const {
    
    Rectangle space;
    
    if (door_wall == "top") {
        if (hinge == "left") {
            space = Rectangle(0, door_y, door_width, door_y);
        } else {
            space = Rectangle(0, door_y + door_width, door_width, room_depth - door_y - door_width);
        }
    } else if (door_wall == "bottom") {
        if (hinge == "left") {
            space = Rectangle(room_width - door_width, door_y, door_width, door_y);
        } else {
            space = Rectangle(room_width - door_width, door_y + door_width, door_width, room_depth - door_y - door_width);
        }
    } else if (door_wall == "left") {
        if (hinge == "left") {
            space = Rectangle(door_x, 0, door_x, door_width);
        } else {
            space = Rectangle(door_x + door_depth, 0, room_width - door_x - door_depth, door_width);
        }
    } else if (door_wall == "right") {
        if (hinge == "left") {
            space = Rectangle(door_x, room_depth - door_width, door_x, door_width);
        } else {
            space = Rectangle(door_x + door_depth, room_depth - door_width, room_width - door_x - door_depth, door_width);
        }
    }
    
    return space;
}

// Calculate space before door
Rectangle BathroomScoringFunction::calculate_before_door_space(
    double door_x, double door_y, double door_width, double door_depth,
    const std::string& door_wall, const std::string& hinge,
    double room_width, double room_depth) const {
    
    Rectangle space;
    const double clearance = 60.0;  // 60cm clearance
    
    if (door_wall == "top") {
        space = Rectangle(0, door_y, clearance, door_width);
    } else if (door_wall == "bottom") {
        space = Rectangle(room_width - clearance, door_y, clearance, door_width);
    } else if (door_wall == "left") {
        space = Rectangle(door_x, 0, door_depth, clearance);
    } else if (door_wall == "right") {
        space = Rectangle(door_x, room_depth - clearance, door_depth, clearance);
    }
    
    return space;
}

// Calculate free space before an object
double BathroomScoringFunction::calculate_space_before_object(
    const PlacedObject& obj,
    const std::vector<PlacedObject>& placed_objects,
    const RoomSize& room_size) const {
    
    double min_space = std::numeric_limits<double>::max();
    
    // Determine the direction to check based on wall
    if (obj.wall == "top" || obj.wall.find("top") != std::string::npos) {
        // Check space in front (toward bottom)
        double space_to_room = room_size.width - (obj.x + obj.depth);
        min_space = std::min(min_space, space_to_room);
        
        // Check distance to other objects
        for (const auto& other : placed_objects) {
            if (&other == &obj) continue;
            if (other.x > obj.x + obj.depth && other.y < obj.y + obj.width && other.y + other.width > obj.y) {
                double dist = other.x - (obj.x + obj.depth);
                min_space = std::min(min_space, dist);
            }
        }
    } else if (obj.wall == "bottom" || obj.wall.find("bottom") != std::string::npos) {
        // Check space in front (toward top)
        min_space = std::min(min_space, obj.x);
        
        for (const auto& other : placed_objects) {
            if (&other == &obj) continue;
            if (other.x + other.depth < obj.x && other.y < obj.y + obj.width && other.y + other.width > obj.y) {
                double dist = obj.x - (other.x + other.depth);
                min_space = std::min(min_space, dist);
            }
        }
    } else if (obj.wall == "left" || obj.wall.find("left") != std::string::npos) {
        // Check space in front (toward right)
        double space_to_room = room_size.depth - (obj.y + obj.width);
        min_space = std::min(min_space, space_to_room);
        
        for (const auto& other : placed_objects) {
            if (&other == &obj) continue;
            if (other.y > obj.y + obj.width && other.x < obj.x + obj.depth && other.x + other.depth > obj.x) {
                double dist = other.y - (obj.y + obj.width);
                min_space = std::min(min_space, dist);
            }
        }
    } else if (obj.wall == "right" || obj.wall.find("right") != std::string::npos) {
        // Check space in front (toward left)
        min_space = std::min(min_space, obj.y);
        
        for (const auto& other : placed_objects) {
            if (&other == &obj) continue;
            if (other.y + other.width < obj.y && other.x < obj.x + obj.depth && other.x + other.depth > obj.x) {
                double dist = obj.y - (other.y + other.width);
                min_space = std::min(min_space, dist);
            }
        }
    }
    
    return min_space;
}

// Calculate Euclidean distance between two rectangles
double BathroomScoringFunction::check_euclidean_distance(const Rectangle& rect1, const Rectangle& rect2) const {
    double center1_x = rect1.x + rect1.depth / 2.0;
    double center1_y = rect1.y + rect1.width / 2.0;
    double center2_x = rect2.x + rect2.depth / 2.0;
    double center2_y = rect2.y + rect2.width / 2.0;
    
    double dx = center1_x - center2_x;
    double dy = center1_y - center2_y;
    
    return std::sqrt(dx * dx + dy * dy);
}

// Check if windows/doors overlap with object
bool BathroomScoringFunction::windows_doors_overlap(
    const std::vector<WindowDoor>& windows_doors,
    double x, double y, double z, double width, double depth, double height,
    double room_width, double room_depth,
    const std::tuple<double, double, double, double>& shadow,
    const std::string& name) const {
    
    Rectangle obj_rect(x, y, width, depth);
    
    for (const auto& wd : windows_doors) {
        Rectangle wd_rect(wd.x, wd.y, wd.width, wd.depth);
        if (check_overlap(obj_rect, wd_rect)) {
            return true;
        }
    }
    
    return false;
}

// Check if shower has at least one free side
bool BathroomScoringFunction::has_free_side(
    const Rectangle& shower_rect,
    const std::vector<Rectangle>& objects_rect) const {
    
    const double min_clearance = 60.0;  // 60cm minimum clearance
    
    // Check each side
    bool top_free = true, bottom_free = true, left_free = true, right_free = true;
    
    for (const auto& obj : objects_rect) {
        // Skip if it's the shower itself
        if (std::abs(obj.x - shower_rect.x) < 0.1 && 
            std::abs(obj.y - shower_rect.y) < 0.1 &&
            std::abs(obj.width - shower_rect.width) < 0.1 && 
            std::abs(obj.depth - shower_rect.depth) < 0.1) {
            continue;
        }
        
        // Check if object blocks any side
        if (obj.x < shower_rect.x && obj.x + obj.depth > shower_rect.x - min_clearance) {
            top_free = false;
        }
        if (obj.x > shower_rect.x + shower_rect.depth && obj.x < shower_rect.x + shower_rect.depth + min_clearance) {
            bottom_free = false;
        }
        if (obj.y < shower_rect.y && obj.y + obj.width > shower_rect.y - min_clearance) {
            left_free = false;
        }
        if (obj.y > shower_rect.y + shower_rect.width && obj.y < shower_rect.y + shower_rect.width + min_clearance) {
            right_free = false;
        }
    }
    
    return top_free || bottom_free || left_free || right_free;
}

// Identify available space (simplified version)
AvailableSpace BathroomScoringFunction::identify_available_space(
    const std::vector<PlacedObject>& placed_objects,
    const RoomSize& room_size,
    int grid_size,
    const std::vector<WindowDoor>& windows_doors) const {
    
    AvailableSpace result;
    
    // Create a grid representation
    int grid_width = static_cast<int>(room_size.width / grid_size);
    int grid_depth = static_cast<int>(room_size.depth / grid_size);
    
    std::vector<std::vector<bool>> grid(grid_width, std::vector<bool>(grid_depth, true));
    
    // Mark occupied spaces
    for (const auto& obj : placed_objects) {
        int start_x = static_cast<int>(obj.x / grid_size);
        int start_y = static_cast<int>(obj.y / grid_size);
        int end_x = static_cast<int>((obj.x + obj.depth) / grid_size);
        int end_y = static_cast<int>((obj.y + obj.width) / grid_size);
        
        for (int i = start_x; i < end_x && i < grid_width; ++i) {
            for (int j = start_y; j < end_y && j < grid_depth; ++j) {
                grid[i][j] = false;
            }
        }
    }
    
    // Find contiguous free spaces (simplified)
    for (int i = 0; i < grid_width; ++i) {
        for (int j = 0; j < grid_depth; ++j) {
            if (grid[i][j]) {
                result.without_shadow.push_back(
                    Rectangle(i * grid_size, j * grid_size, grid_size, grid_size)
                );
            }
        }
    }
    
    return result;
}

// Check for enclosed spaces using flood-fill
bool BathroomScoringFunction::check_enclosed_spaces(
    const std::vector<Rectangle>& spaces,
    double room_width, double room_depth,
    int min_distance,
    const std::tuple<std::string, double, double, double>& door_position) const {
    
    if (spaces.empty()) {
        return false;
    }
    
    const int grid_size = 5;
    int grid_width = static_cast<int>(room_width / grid_size);
    int grid_depth = static_cast<int>(room_depth / grid_size);
    
    // Create grid
    std::vector<std::vector<int>> grid(grid_width, std::vector<int>(grid_depth, 0));
    
    // Mark available spaces
    for (const auto& space : spaces) {
        int start_x = std::max(0, static_cast<int>(space.x / grid_size));
        int start_y = std::max(0, static_cast<int>(space.y / grid_size));
        int end_x = std::min(grid_width, static_cast<int>((space.x + space.depth) / grid_size));
        int end_y = std::min(grid_depth, static_cast<int>((space.y + space.width) / grid_size));
        
        for (int i = start_x; i < end_x; ++i) {
            for (int j = start_y; j < end_y; ++j) {
                grid[i][j] = 1;
            }
        }
    }
    
    // Count total free cells
    int total_free = 0;
    for (const auto& row : grid) {
        for (int cell : row) {
            total_free += cell;
        }
    }
    
    if (total_free == 0) {
        return false;
    }
    
    // Flood-fill from door or edges
    std::vector<std::vector<bool>> visited(grid_width, std::vector<bool>(grid_depth, false));
    std::queue<std::pair<int, int>> queue;
    
    // Start from door if specified, otherwise from edges
    std::string door_wall = std::get<0>(door_position);
    if (!door_wall.empty()) {
        double door_x = std::get<1>(door_position);
        double door_y = std::get<2>(door_position);
        double door_width = std::get<3>(door_position);
        
        if (door_wall == "top") {
            int start_y = static_cast<int>(door_y / grid_size);
            int end_y = static_cast<int>((door_y + door_width) / grid_size);
            for (int y = start_y; y <= end_y && y < grid_depth; ++y) {
                if (grid[0][y] == 1) {
                    queue.push({0, y});
                    visited[0][y] = true;
                }
            }
        }
        // Similar for other walls...
    } else {
        // Start from all edges
        for (int i = 0; i < grid_width; ++i) {
            if (grid[i][0] == 1) {
                queue.push({i, 0});
                visited[i][0] = true;
            }
            if (grid[i][grid_depth - 1] == 1) {
                queue.push({i, grid_depth - 1});
                visited[i][grid_depth - 1] = true;
            }
        }
        for (int j = 0; j < grid_depth; ++j) {
            if (grid[0][j] == 1) {
                queue.push({0, j});
                visited[0][j] = true;
            }
            if (grid[grid_width - 1][j] == 1) {
                queue.push({grid_width - 1, j});
                visited[grid_width - 1][j] = true;
            }
        }
    }
    
    // BFS flood-fill
    int reachable = 0;
    while (!queue.empty()) {
        auto [x, y] = queue.front();
        queue.pop();
        reachable++;
        
        // Check 4 neighbors
        const int dx[] = {1, -1, 0, 0};
        const int dy[] = {0, 0, 1, -1};
        
        for (int i = 0; i < 4; ++i) {
            int nx = x + dx[i];
            int ny = y + dy[i];
            
            if (nx >= 0 && nx < grid_width && ny >= 0 && ny < grid_depth &&
                !visited[nx][ny] && grid[nx][ny] == 1) {
                visited[nx][ny] = true;
                queue.push({nx, ny});
            }
        }
    }
    
    // If not all free spaces are reachable, there are enclosed spaces
    return reachable < total_free;
}

// Check corner accessibility
std::tuple<bool, std::map<std::string, std::map<std::string, bool>>> 
BathroomScoringFunction::check_corner_accessibility(
    const std::vector<PlacedObject>& placed_objects,
    double room_width, double room_depth,
    int min_path_width) const {
    
    std::map<std::string, std::map<std::string, bool>> corner_status;
    std::vector<std::string> corners = {"top-left", "top-right", "bottom-left", "bottom-right"};
    
    for (const auto& corner : corners) {
        corner_status[corner]["valid"] = true;  // Simplified - assume valid
    }
    
    return std::make_tuple(true, corner_status);
}

// Check opposite walls distance
std::tuple<bool, std::vector<std::string>> BathroomScoringFunction::check_opposite_walls_distance(
    const std::vector<PlacedObject>& placed_objects,
    const RoomSize& room_size,
    int min_distance) const {
    
    std::vector<std::string> violations;
    
    for (size_t i = 0; i < placed_objects.size(); ++i) {
        for (size_t j = i + 1; j < placed_objects.size(); ++j) {
            const auto& obj1 = placed_objects[i];
            const auto& obj2 = placed_objects[j];
            
            // Check if on opposite walls
            if ((obj1.wall == "top" && obj2.wall == "bottom") ||
                (obj1.wall == "bottom" && obj2.wall == "top") ||
                (obj1.wall == "left" && obj2.wall == "right") ||
                (obj1.wall == "right" && obj2.wall == "left")) {
                
                double distance = 0.0;
                if (obj1.wall == "top" && obj2.wall == "bottom") {
                    distance = obj2.x - (obj1.x + obj1.depth);
                } else if (obj1.wall == "bottom" && obj2.wall == "top") {
                    distance = obj1.x - (obj2.x + obj2.depth);
                } else if (obj1.wall == "left" && obj2.wall == "right") {
                    distance = obj2.y - (obj1.y + obj1.width);
                } else if (obj1.wall == "right" && obj2.wall == "left") {
                    distance = obj1.y - (obj2.y + obj2.width);
                }
                
                if (distance < min_distance) {
                    violations.push_back(obj1.name + " and " + obj2.name);
                }
            }
        }
    }
    
    return std::make_tuple(violations.empty(), violations);
}

// Main scoring function
std::tuple<double, std::map<std::string, double>> BathroomScoringFunction::score(
    const std::vector<PlacedObject>& placed_objects,
    const std::vector<WindowDoor>& windows_doors,
    const RoomSize& room_size,
    const std::vector<std::string>& requested_objects) {
    
    double total_score = 0.0;
    std::map<std::string, double> scores;
    
    // Initialize scoring variables
    double wall_corner_score = 10.0;
    std::map<std::string, double> wall_coverage = {
        {"top", 0}, {"bottom", 0}, {"left", 0}, {"right", 0}
    };
    double corner_coverage_score = 0.0;
    std::map<std::string, std::vector<PlacedObject>> corner_objects;
    double door_sink_score = 10.0;
    double sink_score = 0.0;
    double sink_symmetrial_door_score = 0.0;
    double door_sink_distance_score = 0.0;
    double toilet_to_door_score = 0.0;
    double corner_toilet_score = 0.0;
    double sink_space = 0.0;
    double toilet_space = 0.0;
    int sink_count = 0;
    int toilet_count = 0;
    int shower_count = 0;
    int bathtub_count = 0;
    std::vector<Rectangle> objects_rect;
    double shadow_score = 0.0;
    double bathtub_placement_score = 0.0;
    double bathtub_size_score = 0.0;
    double hidden_sink_score = 10.0;
    double not_enough_space = 10.0;
    double no_overlap_score = 10.0;
    std::string opposite_wall = "";
    std::vector<Rectangle> behind_door_space;
    std::vector<Rectangle> before_door_space;
    double spacing_score = placed_objects.size() * 10.0;
    Rectangle shower_rect;
    
    // Check enclosed spaces
    AvailableSpace available_space = identify_available_space(
        placed_objects, room_size, 1, windows_doors
    );
    
    auto door_pos = std::make_tuple(std::string(""), 0.0, 0.0, 0.0);
    if (check_enclosed_spaces(available_space.without_shadow, room_size.width, 
                             room_size.depth, 60, door_pos)) {
        scores["enclosed_spaces"] = 0.0;
    } else {
        scores["enclosed_spaces"] = 10.0;
    }
    
    // Check corner accessibility
    auto [corners_valid, corner_status] = check_corner_accessibility(
        placed_objects, room_size.width, room_size.depth, 60
    );
    scores["corner_accessibility"] = corners_valid ? 10.0 : 0.0;
    
    // Process doors
    for (const auto& door_window : windows_doors) {
        if (door_window.name.find("door") != std::string::npos) {
            opposite_wall = get_opposite_wall(door_window.wall);
            behind_door_space.push_back(calculate_behind_door_space(
                door_window.x, door_window.y, door_window.width, door_window.depth,
                door_window.wall, door_window.hinge, room_size.width, room_size.depth
            ));
            before_door_space.push_back(calculate_before_door_space(
                door_window.x, door_window.y, door_window.width, door_window.depth,
                door_window.wall, door_window.hinge, room_size.width, room_size.depth
            ));
        }
    }
    
    // Process all objects
    for (size_t i = 0; i < placed_objects.size(); ++i) {
        const auto& obj = placed_objects[i];
        Rectangle obj_rect(obj.x, obj.y, obj.width, obj.depth);
        objects_rect.push_back(obj_rect);
        
        std::string name_lower = obj.name;
        std::transform(name_lower.begin(), name_lower.end(), name_lower.begin(), ::tolower);
        
        if (name_lower == "shower") {
            shower_count++;
            shower_rect = obj_rect;
        }
        if (name_lower == "bathtub") {
            bathtub_count++;
        }
        
        // Wall coverage
        if (obj.wall == "top-left") {
            wall_coverage["top"] += obj.width;
            wall_coverage["left"] += obj.depth;
        } else if (obj.wall == "top-right") {
            wall_coverage["top"] += obj.width;
            wall_coverage["right"] += obj.depth;
        } else if (obj.wall == "bottom-left") {
            wall_coverage["bottom"] += obj.width;
            wall_coverage["left"] += obj.depth;
        } else if (obj.wall == "bottom-right") {
            wall_coverage["bottom"] += obj.width;
            wall_coverage["right"] += obj.depth;
        } else if (wall_coverage.find(obj.wall) != wall_coverage.end()) {
            if (obj.wall == "top" || obj.wall == "bottom") {
                wall_coverage[obj.wall] += obj.width;
            } else {
                wall_coverage[obj.wall] += obj.depth;
            }
        }
        
        // Check window/door overlap
        if (!windows_doors.empty() && windows_doors_overlap(
            windows_doors, obj.x, obj.y, 0, obj.width, obj.depth, obj.height,
            room_size.width, room_size.depth, obj.shadow, obj.name)) {
            no_overlap_score = 0.0;
        }
        
        // Check overlap with before door space
        if (check_overlap(before_door_space, obj_rect)) {
            double overlap = calculate_overlap_area(before_door_space, obj_rect);
            if (name_lower == "bathtub") {
                not_enough_space = 10.0;
            }
        }
        
        // Sink placement
        if (name_lower == "sink" || name_lower == "double sink") {
            if (obj.wall == opposite_wall) {
                sink_score += 10.0;
                
                for (const auto& door_window : windows_doors) {
                    if (door_window.name.find("door") != std::string::npos) {
                        Rectangle behind_space = calculate_behind_door_space(
                            door_window.x, door_window.y, door_window.width, door_window.depth,
                            door_window.wall, door_window.hinge, room_size.width, room_size.depth
                        );
                        
                        // Check symmetry
                        if (door_window.wall == "top" || door_window.wall == "bottom") {
                            if (door_window.y + door_window.width <= obj.y + obj.width && 
                                door_window.y >= obj.y) {
                                sink_symmetrial_door_score += 10.0;
                            }
                        } else if (door_window.wall == "left" || door_window.wall == "right") {
                            if (door_window.x + door_window.depth <= obj.x + obj.depth && 
                                door_window.x >= obj.x) {
                                sink_symmetrial_door_score += 10.0;
                            }
                        }
                        
                        // Check hidden behind door
                        if (check_overlap(behind_space, obj_rect)) {
                            if (door_window.wall != obj.wall) {
                                double overlap = calculate_overlap_area(behind_space, obj_rect);
                                if (overlap > 0) {
                                    hidden_sink_score = -20.0;
                                }
                            }
                            if (door_window.wall == obj.wall) {
                                hidden_sink_score -= 20.0;
                            }
                        } else if (door_window.wall != obj.wall) {
                            door_sink_score += 5.0;
                            
                            Rectangle door_rect(door_window.x, door_window.y, 
                                              door_window.width, door_window.depth);
                            if (check_euclidean_distance(door_rect, obj_rect) < 200.0) {
                                door_sink_distance_score += 10.0;
                            }
                        }
                    }
                }
            }
            
            double space = calculate_space_before_object(obj, placed_objects, room_size);
            sink_space += space;
            sink_count++;
        }
        // Toilet placement
        else if (name_lower == "toilet" || name_lower == "toilet bidet") {
            if (get_opposite_wall(opposite_wall) != obj.wall) {
                door_sink_score += 5.0;
            }
            
            if (obj.wall.find("top") != std::string::npos || 
                obj.wall.find("bottom") != std::string::npos ||
                obj.wall.find("left") != std::string::npos || 
                obj.wall.find("right") != std::string::npos) {
                corner_toilet_score = 10.0;
            } else {
                corner_toilet_score = 0.0;
            }
            
            double space = calculate_space_before_object(obj, placed_objects, room_size);
            toilet_space += space;
            toilet_count++;
            
            for (const auto& door_window : windows_doors) {
                if (door_window.name.find("door") != std::string::npos) {
                    if (door_window.wall == obj.wall) {
                        door_sink_score += 5.0;
                    }
                    
                    if (check_overlap(before_door_space, obj_rect)) {
                        toilet_to_door_score += -10.0;
                    }
                    
                    if (check_overlap(behind_door_space, obj_rect)) {
                        double overlap = calculate_overlap_area(behind_door_space, obj_rect);
                        if (std::abs(overlap - obj.width * obj.depth) < 0.1) {
                            toilet_to_door_score += 20.0;
                            if (door_window.wall == obj.wall) {
                                toilet_to_door_score += 20.0;
                            }
                        } else if (door_window.wall == obj.wall) {
                            toilet_to_door_score += 10.0;
                        }
                    }
                }
            }
        }
        
        scores["no_overlap"] = no_overlap_score;
        total_score += scores["no_overlap"];
        
        // Shadow constraints
        auto [shadow_top, shadow_left, shadow_right, shadow_bottom] = obj.shadow;
        if (obj.x - shadow_top >= 0 && obj.y - shadow_left >= 0 &&
            obj.x + obj.depth + shadow_bottom <= room_size.width &&
            obj.y + obj.width + shadow_right <= room_size.depth) {
            shadow_score += 1.0;
        }
        
        // Bathtub placement
        if (name_lower.find("bathtub") != std::string::npos) {
            std::string door_wall = "";
            for (const auto& wd : windows_doors) {
                if (wd.name.find("door") != std::string::npos) {
                    door_wall = wd.wall;
                    break;
                }
            }
            
            if (!door_wall.empty()) {
                std::string door_opposite_wall = get_opposite_wall(door_wall);
                if (obj.wall.find(door_opposite_wall) != std::string::npos || 
                    door_opposite_wall.find(obj.wall) != std::string::npos) {
                    if ((obj.width > obj.depth && (door_opposite_wall == "top" || door_opposite_wall == "bottom")) ||
                        (obj.width < obj.depth && (door_opposite_wall == "left" || door_opposite_wall == "right"))) {
                        bathtub_placement_score = 10.0;
                    } else {
                        bathtub_placement_score = 0.0;
                    }
                } else {
                    bathtub_placement_score = 10.0;
                }
            }
            
            if (obj.width >= 140.0 || obj.depth >= 140.0) {
                bathtub_size_score = 10.0;
            } else {
                bathtub_size_score = 0.0;
            }
        }
        
        // Check spacing with other objects
        auto corners1 = get_corners(obj.x, obj.y, obj.width, obj.depth);
        for (size_t j = i + 1; j < placed_objects.size(); ++j) {
            const auto& obj2 = placed_objects[j];
            auto corners2 = get_corners(obj2.x, obj2.y, obj2.width, obj2.depth);
            
            double min_dist = min_corner_distance(corners1, corners2);
            if (min_dist > 10.0 && min_dist < 30.0) {
                spacing_score -= 5.0;
            }
            
            Rectangle obj2_rect(obj2.x, obj2.y, obj2.width, obj2.depth);
            if (check_overlap(obj_rect, obj2_rect)) {
                no_overlap_score = 0.0;
                break;
            }
        }
    }
    
    // Calculate wall coverage score
    double wall_coverage_score = 0.0;
    for (const auto& [wall, coverage] : wall_coverage) {
        double coverage_percent = 0.0;
        if (wall == "top" || wall == "bottom") {
            coverage_percent = (coverage / room_size.depth) * 100.0;
        } else if (wall == "left" || wall == "right") {
            coverage_percent = (coverage / room_size.width) * 100.0;
        }
        
        if (coverage_percent >= 70.0) {
            wall_coverage_score += 5.0;
        }
    }
    
    // Normalize door_sink_score
    door_sink_score = (door_sink_score / 15.0) * 10.0;
    
    // Check shower space
    scores["shower_space"] = 10.0;
    if (shower_count > 0) {
        if (has_free_side(shower_rect, objects_rect)) {
            scores["shower_space"] = 10.0;
        }
        else {
            scores["shower_space"] = 0.0;
        }
    }
    
    // Add all scores
    scores["wall_corner_constraints"] = wall_corner_score;
    scores["corner_coverage"] = corner_coverage_score;
    scores["door_sink_toilet"] = std::max(door_sink_score, 0.0);
    scores["sink_opposite_door"] = std::max(sink_score, 0.0);
    scores["sink_symmetrial_door"] = std::max(sink_symmetrial_door_score, 0.0);
    scores["door_sink_distance"] = std::max(door_sink_distance_score, 0.0);
    scores["toilet_to_door"] = toilet_to_door_score;
    scores["corner_toilet"] = corner_toilet_score;
    scores["hidden_sink"] = hidden_sink_score;
    scores["not_enough_space"] = not_enough_space;
    
    if (!placed_objects.empty()) {
        scores["spacing"] = std::max(spacing_score / static_cast<double>(placed_objects.size()), 0.0);
        scores["shadow_constraints"] = std::min((shadow_score / static_cast<double>(placed_objects.size())) * 10.0, 10.0);
    } else {
        scores["spacing"] = 0.0;
        scores["shadow_constraints"] = 0.0;
    }
    
    if (!requested_objects.empty()) {
        scores["requested_objects"] = (static_cast<double>(placed_objects.size()) / 
                                       static_cast<double>(requested_objects.size())) * 10.0;
    } else {
        scores["requested_objects"] = 0.0;
    }
    
    if (bathtub_count > 0) {
        scores["bathtub_placement"] = std::max(bathtub_placement_score, 0.0);
        scores["bathtub_size"] = bathtub_size_score;
        total_score += scores["bathtub_placement"];
        total_score += scores["bathtub_size"];
    }
    
    // Add all scores to total
    total_score += scores["wall_corner_constraints"];
    total_score += scores["corner_coverage"];
    total_score += scores["door_sink_toilet"];
    total_score += scores["sink_opposite_door"];
    total_score += scores["sink_symmetrial_door"];
    total_score += scores["door_sink_distance"];
    total_score += scores["corner_toilet"];
    total_score += scores["spacing"];
    total_score += scores["requested_objects"];
    total_score += scores["shadow_constraints"];
    total_score += scores["hidden_sink"];
    total_score += scores["not_enough_space"];
    total_score += scores["corner_accessibility"];
    total_score += scores["shower_space"];
    
    // Calculate average free space
    double avg_sink_space = sink_count > 0 ? sink_space / sink_count : 0.0;
    double avg_toilet_space = toilet_count > 0 ? toilet_space / toilet_count : 0.0;
    
    double sink_space_score = avg_sink_space > 0 ? std::min(10.0, avg_sink_space / 600.0) : 0.0;
    double toilet_space_score = avg_toilet_space > 0 ? std::min(10.0, avg_toilet_space / 600.0) : 0.0;
    
    scores["toilet_free_space"] = toilet_count > 0 ? toilet_space_score : 0.0;
    
    if (toilet_count > 0) {
        total_score += scores["toilet_free_space"];
        total_score += scores["toilet_to_door"];
    }
    
    // Check opposite walls distance
    auto [has_sufficient_distance, violations] = check_opposite_walls_distance(
        placed_objects, room_size, 60
    );
    scores["opposite_walls_distance"] = has_sufficient_distance ? 10.0 : 0.0;
    total_score += scores["opposite_walls_distance"];
    
    // Critical constraints check
    if (scores["no_overlap"] == 0.0 ||
        scores["wall_corner_constraints"] == 0.0 ||
        scores["opposite_walls_distance"] < 5.0 ||
        scores["corner_accessibility"] == 0.0 ||
        scores["shower_space"] == 0.0) {
        total_score = 0.0;
    } else {
        // Normalize score
        total_score = (total_score / static_cast<double>(scores.size())) * 10.0;
    }
    
    // Additional penalties
    if (scores["door_sink_toilet"] == 0.0 || 
        scores["sink_opposite_door"] == 0.0 || 
        scores["toilet_to_door"] < 0.0) {
        total_score = std::max(total_score - 10.0, 0.0);
    }
    
    // Reject layouts with score < 4
    if (total_score < 4.0) {
        total_score = 0.0;
    }
    
    return std::make_tuple(total_score, scores);
}

} // namespace bathroom_scoring
