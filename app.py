###############################################
### Copyright 2026 shuluo.group
###############################################

import arcade
import math
import datetime
import numpy as np
from pyglet.math import Vec2, Vec3, Mat3
from PIL import Image
from HitBoxAlg import CustomHitBoxAlgorithm
import collision_detection
from arcade.types import LBWH


WINDOW_TITLE = "game"
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 720

CHARACTER_SCALING = 0.5

SPEED_INIT = 0.0
MAX_SPEED = 12.0
MAX_BACK_SPEED = -3.4
ACC_DELTA_SPEED = 0.1
TEXI_DELTA_SPEED = -0.05
BREAK_DELTA_SPEED = -0.5
MAX_TURN_ANGLE = 1.5
DELTA_TURN_ANGLE = 0.1
TURN_DEACC_RATE = 0.986


class GameView(arcade.View):

    def __init__(self):
        super().__init__()

        self.camera_sprites = arcade.Camera2D()

        self.camera_bounds = self.window.rect

        self.camera_gui = arcade.Camera2D()

        self.scene = arcade.Scene()

        self.track_sprite = arcade.Sprite("imgs/track.jpg", scale=1)

        self.startline_sprite = arcade.Sprite("imgs/start_line.png", scale=1)

        player_texture = arcade.texture.default_texture_cache.load_or_get_texture("imgs/auto.png", hit_box_algorithm=arcade.hitbox.PymunkHitBoxAlgorithm(detail=1.0))
        self.player_sprite = arcade.Sprite(player_texture, scale=CHARACTER_SCALING)
    
        mask = Image.open("imgs/track_mask.png").convert('RGBA')

        hitboxAlg = CustomHitBoxAlgorithm()
        points = hitboxAlg.calculate(mask, hit_box_detail=1.0)
        self.track_shape = collision_detection.TrackShape(points[0], points[1])

        self.score = 0
        self.turn_angle = 0.0
        self.speed = SPEED_INIT
        self.lap = 0

        self.time_start = None
        self.time = None
        self.time_finish = None
        self.line_state = 0

        self.left_key_down = False
        self.right_key_down = False
        self.forward_key_down = False
        self.back_key_down = False

        self.score_display = arcade.Text(
            "Score: 0",
            x=500,
            y=10,
            color=arcade.csscolor.WHITE,
            font_size=18,
        )
        self.speed_display = arcade.Text(
            "Speed: 0",
            x=10,
            y=10,
            color=arcade.csscolor.WHITE,
            font_size=18,
        )
        self.time_display = arcade.Text(
            "Time:",
            x=250,
            y=10,
            color=arcade.csscolor.WHITE,
            font_size=18,
        )

    def reset(self):
        self.score = 0

        self.scene = arcade.Scene()

        self.scene.add_sprite("Track", self.track_sprite)
        self.scene.add_sprite("Start_Line", self.startline_sprite)
    
        self.player_sprite.position = (-600, 1020)
        self.player_sprite.angle = 90
    
        self.scene.add_sprite("Player", self.player_sprite)


    def on_draw(self):
        self.clear()

        with self.camera_sprites.activate():
            self.scene.draw()

        with self.camera_gui.activate():
            arcade.draw_rect_filled(LBWH(0,0,self.window.width, 40), (100,100,100))

            self.speed_display.text = f"Speed: {int(abs(self.speed * 15))}"
            self.speed_display.draw()

            if self.time or self.time_finish:
                t = self.time_finish or self.time
                formatted_time = str((t.seconds//60)%60).zfill(2)+":"+str(t.seconds%60).zfill(2)+":"+str(int(t.microseconds//1E4)).zfill(2)
                self.time_display.text = f"Time {formatted_time}"
                if self.time_finish:
                    self.time_display.color = arcade.csscolor.ORANGE
                else:
                    self.time_display.color = arcade.csscolor.WHITE
                self.time_display.draw()
            else:
                self.time_display.text = f"Time 00:00.00"
                self.time_display.draw()

    def player_delta_move(self, delta_move:Vec2):
        pos = self.player_sprite.position
        pos_vec = Vec2(pos[0], pos[1])
        global_pos = loc_to_glb_transform(pos_vec, math.radians(self.player_sprite.angle), delta_move)
        delta_global = global_pos - pos_vec
        self.player_sprite.position = global_pos
        return delta_global

    def update_player(self):
        if self.forward_key_down and not self.back_key_down:
            if self.speed < 0:
                if self.speed > BREAK_DELTA_SPEED:
                    self.speed = 0
                    self.forward_key_down = False
                else:
                    self.speed -= BREAK_DELTA_SPEED
            elif self.speed >= MAX_SPEED:
                self.speed = MAX_SPEED
            else:
                self.speed += ACC_DELTA_SPEED
        elif self.back_key_down and not self.forward_key_down:
            if self.speed > 0:
                if self.speed < -BREAK_DELTA_SPEED:
                    self.speed = 0
                    self.back_key_down = False
                else:
                    self.speed += BREAK_DELTA_SPEED
            elif self.speed <= MAX_BACK_SPEED:
                self.speed = MAX_BACK_SPEED
            else:
                self.speed -= ACC_DELTA_SPEED
        else:
            if self.speed > TEXI_DELTA_SPEED and self.speed < 0 or self.speed < -TEXI_DELTA_SPEED and self.speed > 0:
                self.speed = 0
            elif self.speed < 0:
                self.speed -= TEXI_DELTA_SPEED
            elif self.speed > 0:
                self.speed += TEXI_DELTA_SPEED

        if self.left_key_down and not self.right_key_down:
            if self.turn_angle < -MAX_TURN_ANGLE:
                self.turn_angle = -MAX_TURN_ANGLE
            else:
                self.turn_angle -= DELTA_TURN_ANGLE
        elif self.right_key_down and not self.left_key_down:
            if self.turn_angle > MAX_TURN_ANGLE:
                self.turn_angle = MAX_TURN_ANGLE
            else:
                self.turn_angle += DELTA_TURN_ANGLE
        else:
            if np.abs(self.turn_angle) <= DELTA_TURN_ANGLE:
                    self.turn_angle = 0
            else:
                self.turn_angle += -float(np.sign(self.turn_angle)) * DELTA_TURN_ANGLE

        if self.turn_angle != 0:
            self.speed = (1.0 - (1.0-TURN_DEACC_RATE) * math.fabs(self.turn_angle) / MAX_TURN_ANGLE) * self.speed

        prev_pos = self.player_sprite.position
        delta_move = Vec2(0.0, 1.0)
        delta_move = delta_move.__mul__(self.speed)
        if self.speed > 0:
            delta_move = delta_move.rotate(-math.radians(self.turn_angle))
        else:
            delta_move = delta_move.rotate(math.radians(self.turn_angle))
        delta_global = self.player_delta_move(delta_move)

        if delta_global.x != 0 and delta_global.y != 0:
            if self.speed > 0:
                radian = math.atan2(delta_global.x, delta_global.y)
            else:
                radian = math.atan2(delta_global.x, delta_global.y) + math.pi
            self.player_sprite.angle = math.degrees(radian)

        intersection = collision_detection.collision_track(self.track_shape, self.player_sprite.hit_box.get_adjusted_points())
        if intersection.area > 1.0:
            self.speed = float(np.clip(self.speed, 0, MAX_SPEED*0.1))
            self.player_sprite.position = prev_pos
            self.speed = 0
            pos = self.player_sprite.position
            centroid = intersection.centroid
            centroid_vec = Vec2(centroid.x, centroid.y)
            player_pos = Vec2(pos[0], pos[1])
            loc_pos = glb_to_loc_transform(player_pos, math.radians(self.player_sprite.angle), centroid_vec)
            if loc_pos.y < 0:
                global_move = Vec2(pos[0] - centroid_vec.x, pos[1] - centroid_vec.y)
                global_move = global_move.__mul__(0.1)
                self.player_sprite.position = (player_pos.x + global_move.x, player_pos.y + global_move.y)


    def update_time(self):
        line_mid_x = (self.startline_sprite.hit_box.left + self.startline_sprite.hit_box.right) / 2
        if not self.player_sprite.collides_with_sprite(self.startline_sprite):
            self.line_state = 0
        elif self.player_sprite.position[0] < line_mid_x:
            if self.line_state == 0 and self.lap == 1:
                if not self.time_finish:
                    self.time_finish = datetime.datetime.now() - self.time_start
            if self.line_state == 2:
                self.lap -= 1
            self.line_state = 1
        else:
            if self.line_state == 1:
                if not self.time_start:
                    self.time_start = datetime.datetime.now()
                self.lap += 1
            self.line_state = 2
        
        if self.time_start is not None and self.time_finish is None:
            self.time = datetime.datetime.now() - self.time_start


    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.forward_key_down = True

        if key == arcade.key.DOWN:
            self.back_key_down = True

        elif key == arcade.key.LEFT:
            self.left_key_down = True

        elif key == arcade.key.RIGHT:
            self.right_key_down = True


    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP:
            self.forward_key_down = False

        if key == arcade.key.DOWN:
            self.back_key_down = False

        elif key == arcade.key.LEFT:
            self.left_key_down = False

        elif key == arcade.key.RIGHT:
            self.right_key_down = False


    def center_camera_to_player(self):
        self.camera_sprites.position = self.player_sprite.position
        self.camera_sprites.angle = self.player_sprite.angle


    def on_update(self, delta_time: float):
        self.update_player()

        self.update_time()

        self.center_camera_to_player()

    def on_resize(self, width: int, height: int):
        super().on_resize(width, height)
        self.camera_sprites.match_window()
        self.camera_gui.match_window(position=True)

def apply_transform(vec:Vec2, mat:Mat3) -> Vec2:
    vec3 = Vec3(vec.x, vec.y, 1)
    vec3 = mat.__matmul__(vec3)
    return Vec2(vec3.x, vec3.y)

def loc_to_glb_transform(pos:Vec2, radian:float, vec:Vec2) -> Vec2:
    mat = Mat3()
    mat = mat.translate(-pos.x, pos.y)
    mat = mat.rotate(-math.degrees(radian))
    return apply_transform(vec, mat)

def glb_to_loc_transform(pos:Vec2, radian:float, vec:Vec2) -> Vec2:
    mat = Mat3()
    mat = mat.rotate(math.degrees(radian))
    mat = mat.translate(pos.x, -pos.y)
    return apply_transform(vec, mat)

def main():
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game = GameView()
    game.reset()

    window.show_view(game)
    arcade.run()

if __name__ == "__main__":
    main()