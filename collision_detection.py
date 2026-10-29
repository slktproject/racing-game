###############################################
### Copyright 2026 shuluo.group
###############################################

from arcade.types import Point2List
from shapely.geometry import Polygon

class TrackShape():
    def __init__(self, outer:Point2List, inner:Point2List):
        self.poly_outer = Polygon(outer)
        self.poly_inner = Polygon(inner)

def collision_track(track:TrackShape, obj_points:Point2List):
    obj_poly = Polygon(obj_points)
    intersect1 = polygon_intersection(track.poly_inner, obj_poly)
    if intersect1.area > 1.0:
        return intersect1
    else:
        intersect2 = polygon_intersection(track.poly_outer, obj_poly)
        diff = obj_poly.difference(intersect2)
        return diff

def polygon_intersection(poly1:Polygon, poly2:Polygon):
    return poly1.intersection(poly2)

def polygon_intersection_points(points1, points2):
    poly1 = Polygon(points1)
    poly2 = Polygon(points2)
    return poly1.intersection(poly2)