#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/operators.h>
#include "bathroom_scoring.h"

namespace py = pybind11;
using namespace bathroom_scoring;

/**
 * Pybind11 bindings for the C++ bathroom scoring module.
 * 
 * This module provides Python bindings for the high-performance C++ implementation
 * of the bathroom layout scoring function.
 */
PYBIND11_MODULE(cpp_bathroom_scoring, m) {
    m.doc() = "C++ implementation of bathroom layout scoring with pybind11 bindings";

    // PlacedObject structure
    py::class_<PlacedObject>(m, "PlacedObject", "Represents a placed object in the bathroom")
        .def(py::init<>())
        .def_readwrite("x", &PlacedObject::x, "X position in cm")
        .def_readwrite("y", &PlacedObject::y, "Y position in cm")
        .def_readwrite("width", &PlacedObject::width, "Width in cm")
        .def_readwrite("depth", &PlacedObject::depth, "Depth in cm")
        .def_readwrite("height", &PlacedObject::height, "Height in cm")
        .def_readwrite("name", &PlacedObject::name, "Object name (e.g., 'sink', 'toilet')")
        .def_readwrite("wall", &PlacedObject::wall, "Wall placement (e.g., 'top', 'left', 'top-left')")
        .def_readwrite("must_be_corner", &PlacedObject::must_be_corner, "Whether object must be in corner")
        .def_readwrite("must_be_against_wall", &PlacedObject::must_be_against_wall, "Whether object must be against wall")
        .def_readwrite("shadow", &PlacedObject::shadow, "Shadow/clearance space (top, left, right, bottom)")
        .def("__repr__", [](const PlacedObject& obj) {
            return "<PlacedObject name='" + obj.name + "' pos=(" + 
                   std::to_string(obj.x) + ", " + std::to_string(obj.y) + ") " +
                   "size=(" + std::to_string(obj.width) + "x" + std::to_string(obj.depth) + ")>";
        });

    // WindowDoor structure
    py::class_<WindowDoor>(m, "WindowDoor", "Represents a window or door")
        .def(py::init<>())
        .def_readwrite("x", &WindowDoor::x, "X position in cm")
        .def_readwrite("y", &WindowDoor::y, "Y position in cm")
        .def_readwrite("width", &WindowDoor::width, "Width in cm")
        .def_readwrite("depth", &WindowDoor::depth, "Depth in cm")
        .def_readwrite("height", &WindowDoor::height, "Height in cm")
        .def_readwrite("name", &WindowDoor::name, "Name (e.g., 'door', 'window')")
        .def_readwrite("wall", &WindowDoor::wall, "Wall location")
        .def_readwrite("hinge", &WindowDoor::hinge, "Hinge side ('left' or 'right')")
        .def_readwrite("way", &WindowDoor::way, "Opening direction")
        .def("__repr__", [](const WindowDoor& wd) {
            return "<WindowDoor name='" + wd.name + "' wall='" + wd.wall + "'>";
        });

    // RoomSize structure
    py::class_<RoomSize>(m, "RoomSize", "Represents room dimensions")
        .def(py::init<>())
        .def(py::init<double, double, double>(),
             py::arg("width"), py::arg("depth"), py::arg("height"))
        .def_readwrite("width", &RoomSize::width, "Room width in cm")
        .def_readwrite("depth", &RoomSize::depth, "Room depth in cm")
        .def_readwrite("height", &RoomSize::height, "Room height in cm")
        .def("__repr__", [](const RoomSize& rs) {
            return "<RoomSize " + std::to_string(rs.width) + "x" + 
                   std::to_string(rs.depth) + "x" + std::to_string(rs.height) + ">";
        });

    // Rectangle structure
    py::class_<Rectangle>(m, "Rectangle", "Represents a rectangular space")
        .def(py::init<>())
        .def(py::init<double, double, double, double>(),
             py::arg("x"), py::arg("y"), py::arg("width"), py::arg("depth"))
        .def_readwrite("x", &Rectangle::x)
        .def_readwrite("y", &Rectangle::y)
        .def_readwrite("width", &Rectangle::width)
        .def_readwrite("depth", &Rectangle::depth)
        .def("__repr__", [](const Rectangle& r) {
            return "<Rectangle pos=(" + std::to_string(r.x) + ", " + std::to_string(r.y) + 
                   ") size=(" + std::to_string(r.width) + "x" + std::to_string(r.depth) + ")>";
        });

    // AvailableSpace structure
    py::class_<AvailableSpace>(m, "AvailableSpace", "Represents available space in the room")
        .def(py::init<>())
        .def_readwrite("with_shadow", &AvailableSpace::with_shadow, "Spaces including shadow areas")
        .def_readwrite("without_shadow", &AvailableSpace::without_shadow, "Spaces excluding shadow areas");

    // BathroomScoringFunction class
    py::class_<BathroomScoringFunction>(m, "BathroomScoringFunction", 
        "Main scoring class for bathroom layouts\n\n"
        "This class provides high-performance C++ implementation of the bathroom\n"
        "layout scoring algorithm. It evaluates layouts based on multiple criteria\n"
        "including fixture placement, accessibility, spacing, and user requirements.")
        .def(py::init<>(), "Constructor")
        .def("score", &BathroomScoringFunction::score,
             py::arg("placed_objects"),
             py::arg("windows_doors"),
             py::arg("room_size"),
             py::arg("requested_objects") = std::vector<std::string>(),
             R"pbdoc(
                Score a bathroom layout based on various criteria.
                
                This function evaluates a bathroom layout and returns a total score
                along with a detailed breakdown of individual scoring components.
                
                Args:
                    placed_objects (list[PlacedObject]): List of placed objects in the bathroom
                    windows_doors (list[WindowDoor]): List of windows and doors
                    room_size (RoomSize): Room dimensions (width, depth, height)
                    requested_objects (list[str], optional): List of requested object names
                
                Returns:
                    tuple: (total_score: float, score_breakdown: dict)
                        - total_score: Overall layout score (0-100, layouts < 4 are rejected)
                        - score_breakdown: Dictionary with individual component scores
                
                Score Breakdown Components:
                    - wall_corner_constraints: Objects placed according to wall/corner requirements
                    - corner_coverage: Coverage of room corners
                    - door_sink_toilet: Optimal placement relative to door
                    - sink_opposite_door: Sink placed opposite to door
                    - sink_symmetrial_door: Sink symmetrically aligned with door
                    - door_sink_distance: Distance between door and sink
                    - toilet_to_door: Toilet visibility and accessibility from door
                    - corner_toilet: Toilet placed in corner
                    - hidden_sink: Penalty for sink hidden behind door
                    - not_enough_space: Sufficient clearance before door
                    - spacing: Optimal spacing between objects
                    - shadow_constraints: Shadow/clearance requirements met
                    - requested_objects: Requested objects included
                    - bathtub_placement: Bathtub orientation and position
                    - bathtub_size: Bathtub size optimization
                    - shower_space: Shower has at least one free side
                    - toilet_free_space: Free space in front of toilet
                    - opposite_walls_distance: Minimum distance between opposite walls
                    - corner_accessibility: All corners accessible or occupied
                    - no_overlap: No overlaps between objects or with windows/doors
                
                Example:
                    >>> scorer = BathroomScoringFunction()
                    >>> 
                    >>> # Create objects
                    >>> sink = PlacedObject()
                    >>> sink.name = "sink"
                    >>> sink.x, sink.y = 0, 100
                    >>> sink.width, sink.depth, sink.height = 60, 50, 85
                    >>> sink.wall = "top"
                    >>> 
                    >>> toilet = PlacedObject()
                    >>> toilet.name = "toilet"
                    >>> toilet.x, toilet.y = 200, 0
                    >>> toilet.width, toilet.depth, toilet.height = 50, 60, 75
                    >>> toilet.wall = "left"
                    >>> 
                    >>> # Create door
                    >>> door = WindowDoor()
                    >>> door.name = "door"
                    >>> door.x, door.y = 150, 0
                    >>> door.width, door.height = 80, 210
                    >>> door.wall = "left"
                    >>> door.hinge = "left"
                    >>> 
                    >>> # Score layout
                    >>> room = RoomSize(300, 250, 270)
                    >>> score, breakdown = scorer.score([sink, toilet], [door], room)
                    >>> print(f"Total score: {score}")
                    >>> print(f"Breakdown: {breakdown}")
             )pbdoc");

    // Helper function to create PlacedObject from dict
    m.def("create_placed_object_from_dict", [](py::dict d) {
        PlacedObject obj;
        if (d.contains("x")) obj.x = d["x"].cast<double>();
        if (d.contains("y")) obj.y = d["y"].cast<double>();
        if (d.contains("width")) obj.width = d["width"].cast<double>();
        if (d.contains("depth")) obj.depth = d["depth"].cast<double>();
        if (d.contains("height")) obj.height = d["height"].cast<double>();
        if (d.contains("name")) obj.name = d["name"].cast<std::string>();
        if (d.contains("wall")) obj.wall = d["wall"].cast<std::string>();
        if (d.contains("must_be_corner")) obj.must_be_corner = d["must_be_corner"].cast<bool>();
        if (d.contains("must_be_against_wall")) obj.must_be_against_wall = d["must_be_against_wall"].cast<bool>();
        if (d.contains("shadow")) obj.shadow = d["shadow"].cast<std::tuple<double, double, double, double>>();
        return obj;
    }, py::arg("dict"), "Create PlacedObject from Python dictionary");

    // Helper function to create WindowDoor from dict
    m.def("create_window_door_from_dict", [](py::dict d) {
        WindowDoor wd;
        if (d.contains("x")) wd.x = d["x"].cast<double>();
        if (d.contains("y")) wd.y = d["y"].cast<double>();
        if (d.contains("width")) wd.width = d["width"].cast<double>();
        if (d.contains("depth")) wd.depth = d["depth"].cast<double>();
        if (d.contains("height")) wd.height = d["height"].cast<double>();
        if (d.contains("name")) wd.name = d["name"].cast<std::string>();
        if (d.contains("wall")) wd.wall = d["wall"].cast<std::string>();
        if (d.contains("hinge")) wd.hinge = d["hinge"].cast<std::string>();
        if (d.contains("way")) wd.way = d["way"].cast<std::string>();
        return wd;
    }, py::arg("dict"), "Create WindowDoor from Python dictionary");

    // Version info
    m.attr("__version__") = "1.0.0";
    m.attr("__author__") = "Bathroom Layout Generator";
}
