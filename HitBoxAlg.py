import pymunk
from PIL.Image import Image
from pymunk import Vec2d
from pymunk.autogeometry import (
    PolylineSet,
    march_soft,
    simplify_curves,
)

from arcade.types import RGBA255, Point2, Point2List

from arcade.hitbox.base import HitBoxAlgorithm


class CustomHitBoxAlgorithm(HitBoxAlgorithm):
    default_detail = 4.5

    def __init__(self, *, detail: float | None = None):
        super().__init__()
        self.detail = detail or self.default_detail
        self._cache_name += f"|detail={self.detail}"

    def __call__(self, *, detail: float | None = None) -> "CustomHitBoxAlgorithm":
        return CustomHitBoxAlgorithm(detail=detail or self.detail)

    def calculate(self, image: Image, detail: float | None = None, **kwargs):
        hit_box_detail = detail or self.detail

        line_sets = self.trace_image(image)
        if len(line_sets) == 0:
            raise Exception("no mask calculated.")

        lines = self.select_line_set(line_sets)

        points_list = []
        for line in lines:
            if len(line) > 4:
                line = simplify_curves(line, hit_box_detail)
                points = self.to_points_list(image, line)
                points_list.append(points)

        return points_list

    def to_points_list(self, image: Image, line_set: list[Vec2d]) -> Point2List:
        hh = image.height / 2.0
        hw = image.width / 2.0
        points = []
        for vec2 in line_set:
            point_tuple = (
                float(round(vec2.x - hw)),
                float(round(image.height - (vec2.y - hh) - image.height)),
            )
            points.append(point_tuple)

        if len(points) > 1 and points[0] == points[-1]:
            points.pop()

        return tuple(points)

    def trace_image(self, image: Image) -> PolylineSet:
        def sample_func(sample_point: Point2) -> int:
            if (
                sample_point[0] < 0
                or sample_point[1] < 0
                or sample_point[0] >= image.width
                or sample_point[1] >= image.height
            ):
                return 0

            point_tuple = int(sample_point[0]), int(sample_point[1])
            color: RGBA255 = image.getpixel(point_tuple)  # type: ignore

            return 255 if color[3] > 0 else 0

        logo_bb = pymunk.BB(-1, -1, image.width, image.height)

        down_res = 5
        horizontal_samples = int(image.width / down_res)
        vertical_samples = int(image.height / down_res)

        return march_soft(logo_bb, horizontal_samples, vertical_samples, 99, sample_func)

    def select_line_set(self, line_sets: PolylineSet) -> list[list[Vec2d]]:

        if len(line_sets) == 1:
            return line_sets[0]

        largest_area = -1.0
        smallest_area = float("inf")
        largest_idx = 0
        smallest_idx = 0

        for i, line_set in enumerate(line_sets):
            min_x = None
            min_y = None
            max_x = None
            max_y = None
            for point in line_set:
                if min_x is None or point.x < min_x:
                    min_x = point.x
                if max_x is None or point.x > max_x:
                    max_x = point.x
                if min_y is None or point.y < min_y:
                    min_y = point.y
                if max_y is None or point.y > max_y:
                    max_y = point.y

            if min_x is None or max_x is None or min_y is None or max_y is None:
                raise ValueError("No points in bounding box.")

            area = (max_x - min_x) * (max_y - min_y)
            if area > largest_area:
                largest_area = area
                largest_idx = i
            elif area < smallest_area:
                smallest_area = area
                smallest_idx = i

        return (line_sets[largest_idx], line_sets[smallest_idx])
