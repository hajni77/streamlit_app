#ifndef BATHROOM_SCORING_H
#define BATHROOM_SCORING_H

#include <vector>
#include <string>
#include <map>
#include <tuple>
#include <cmath>
#include <algorithm>
#include <limits>

namespace bathroom_scoring {

/**
 * Structure representing a placed object in the bathroom.
 */
struct PlacedObject {
    double x;
    double y;
    double width;
    double depth;
    double height;
    std::string name;
    std::string wall;
    bool must_be_corner;
    bool must_be_against_wall;
    std::tuple<double, double, double, double> shadow;  // top, left, right, bottom
    
    PlacedObject() : x(0), y(0), width(0), depth(0), height(0), 
                     must_be_corner(false), must_be_against_wall(false),
                     shadow(std::make_tuple(0, 0, 0, 0)) {}
};

/**
 * Structure representing a window or door.
 */
struct WindowDoor {
    double x;
    double y;
    double width;
    double depth;
    double height;
    std::string name;
    std::string wall;
    std::string hinge;
    std::string way;
    
    WindowDoor() : x(0), y(0), width(0), depth(0), height(0) {}
};

/**
 * Structure representing room dimensions.
 */
struct RoomSize {
    double width;
    double depth;
    double height;
    
    RoomSize() : width(0), depth(0), height(0) {}
    RoomSize(double w, double d, double h) : width(w), depth(d), height(h) {}
};

/**
 * Structure representing a rectangular space.
 */
struct Rectangle {
    double x;
    double y;
    double width;
    double depth;
    
    Rectangle() : x(0), y(0), width(0), depth(0) {}
    Rectangle(double x_, double y_, double w, double d) : x(x_), y(y_), width(w), depth(d) {}
};

/**
 * Structure representing available space.
 */
struct AvailableSpace {
    std::vector<Rectangle> with_shadow;
    std::vector<Rectangle> without_shadow;
};

/**
 * Main scoring class for bathroom layouts.
 */
class BathroomScoringFunction {
public:
    BathroomScoringFunction();
    ~BathroomScoringFunction();
    
    /**
     * Score a bathroom layout.
     * 
     * Args:
     *     placed_objects: Vector of placed objects
     *     windows_doors: Vector of windows and doors
     *     room_size: Room dimensions
     *     requested_objects: Vector of requested object names
     * 
     * Returns:
     *     Tuple of (total_score, score_breakdown)
     */
    std::tuple<double, std::map<std::string, double>> score(
        const std::vector<PlacedObject>& placed_objects,
        const std::vector<WindowDoor>& windows_doors,
        const RoomSize& room_size,
        const std::vector<std::string>& requested_objects
    );
    
private:
    // Helper functions
    std::vector<std::tuple<double, double>> get_corners(double x, double y, double width, double depth) const;
    double min_corner_distance(const std::vector<std::tuple<double, double>>& corners1,
                               const std::vector<std::tuple<double, double>>& corners2) const;
    
    bool check_overlap(const Rectangle& rect1, const Rectangle& rect2) const;
    bool check_overlap(const std::vector<Rectangle>& rects, const Rectangle& rect) const;
    
    double calculate_overlap_area(const std::vector<Rectangle>& rects, const Rectangle& rect) const;
    double calculate_overlap_area(const Rectangle& rect1, const Rectangle& rect2) const;
    
    bool is_corner_placement(double x, double y, double room_width, double room_depth,
                            double obj_width, double obj_depth) const;
    
    std::string get_opposite_wall(const std::string& wall) const;
    
    Rectangle calculate_behind_door_space(double door_x, double door_y, double door_width,
                                         double door_depth, const std::string& door_wall,
                                         const std::string& hinge, double room_width,
                                         double room_depth) const;
    
    Rectangle calculate_before_door_space(double door_x, double door_y, double door_width,
                                         double door_depth, const std::string& door_wall,
                                         const std::string& hinge, double room_width,
                                         double room_depth) const;
    
    double calculate_space_before_object(const PlacedObject& obj,
                                        const std::vector<PlacedObject>& placed_objects,
                                        const RoomSize& room_size) const;
    
    double check_euclidean_distance(const Rectangle& rect1, const Rectangle& rect2) const;
    
    bool windows_doors_overlap(const std::vector<WindowDoor>& windows_doors,
                              double x, double y, double z, double width, double depth,
                              double height, double room_width, double room_depth,
                              const std::tuple<double, double, double, double>& shadow,
                              const std::string& name) const;
    
    bool has_free_side(const Rectangle& shower_rect,
                      const std::vector<Rectangle>& objects_rect) const;
    
    AvailableSpace identify_available_space(const std::vector<PlacedObject>& placed_objects,
                                           const RoomSize& room_size,
                                           int grid_size,
                                           const std::vector<WindowDoor>& windows_doors) const;
    
    bool check_enclosed_spaces(const std::vector<Rectangle>& spaces,
                              double room_width, double room_depth,
                              int min_distance,
                              const std::tuple<std::string, double, double, double>& door_position) const;
    
    std::tuple<bool, std::map<std::string, std::map<std::string, bool>>> check_corner_accessibility(
        const std::vector<PlacedObject>& placed_objects,
        double room_width, double room_depth,
        int min_path_width) const;
    
    std::tuple<bool, std::vector<std::string>> check_opposite_walls_distance(
        const std::vector<PlacedObject>& placed_objects,
        const RoomSize& room_size,
        int min_distance) const;
};

} // namespace bathroom_scoring

#endif // BATHROOM_SCORING_H
