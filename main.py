import pygame
import pytmx
from pytmx.util_pygame import load_pygame


class Slope:

    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
            self.pos = (x, y)

        def __repr__(self):
            return (self.x, self.y)
        
        def pos_offset(self, offset):
            return (self.x, self.y + offset)

    def __init__(self, start, end, s_type):
        self.start = self.Point(start[0], start[1])
        self.end = self.Point(end[0], end[1])
        self.type = s_type
        self.slope = self.calc_slope()

    def calc_slope(self):
        return (self.end.y - self.start.y) / (self.end.x - self.start.x) * -1

    def correct_points(self):
        if self.start.y < self.end.y:
            temp = self.start
            self.start = self.end
            self.end = temp


class Rectangle:
    def __init__(self, coords, width, height, line_type):
        self.x = coords[0]
        self.y = coords[1]
        self.width = width
        self.height = height
        self.rect = pygame.FRect((self.x, self.y), (self.width, self.height))
        self.type = line_type


def load_env(file_path):
    data = load_pygame(file_path)
    image = None
    rects = []
    slopes = []
    for layer in data.layers:
        if isinstance(layer, pytmx.TiledImageLayer):
            image = layer.image
        elif isinstance(layer, pytmx.TiledObjectGroup):
            if layer.name == "platforms":
                for obj in layer:
                    start = (obj.x, obj.y)
                    rect = Rectangle(start, obj.width, obj.height, obj.type)
                    rects.append(rect)
            if layer.name == "slopes":
                for obj in layer:
                    start_point = obj.points[0]
                    end_point = obj.points[1]
                    slopes.append(Slope(start_point, end_point, None))

    return image, rects, slopes


def basic_collision(player_rect, velocity, collisions, floor, ceiling, walls):
    # Go through collisions as normal no need for extra checks.
    if collisions[0]:
        player_rect.bottom = floor.rect.top
    if collisions[1]:
        player_rect.top = ceiling.rect.bottom
    if collisions[2]:
        for wall in walls:
            if wall.type == "l":
                player_rect.right = wall.rect.left
            else:
                player_rect.left = wall.rect.right

    return player_rect


def check_collisions(player, rects, velocity):

    collisions = [False, False, False]  # [Floor, Ceiling, Wall]
    collided_floor = None
    collided_ceiling = None
    collided_walls = []

    player_rect = pygame.FRect(
        (player[0] + velocity[0], player[1] + velocity[1]), (50, 50))
    for rect in rects:
        if player_rect.colliderect(rect.rect):
            if rect.type == "c":
                if (collided_ceiling and collided_ceiling.y > rect.y) or not collided_ceiling:
                    velocity[1] = 0
                    collisions[1] = True
                    collided_ceiling = rect
            if rect.type == "f":
                if (collided_floor and collided_floor.y < rect.y) or not collided_floor:
                    velocity[1] = 0
                    collisions[0] = True
                    collided_floor = rect
            if rect.type == "l" or rect.type == "r":
                velocity[0] = 0
                collisions[2] = True
                collided_walls.append(rect)

    # Add Slope logic

    if sum(collisions) == 1:
        # Only colliding with a single line
        player_rect = basic_collision(
            player_rect, velocity, collisions, collided_floor, collided_ceiling, collided_walls)
    elif collisions[0] and collisions[2] and len(collided_walls) > 1:
        # When there are 2 wall collisions i.e. standing on small point

        # Check if standing on small ledge
        if collided_walls[0].type == collided_walls[1].type:
            wall1 = collided_walls[0]
            wall2 = collided_walls[1]

            if wall1.type == "l":
                if wall1.rect.left > wall2.rect.left:
                    player_rect.right = wall1.rect.left
                else:
                    player_rect.right = wall2.rect.left
            else:
                if wall1.rect.right < wall2.rect.right:
                    player_rect.left = wall1.rect.right
                else:
                    player_rect.left = wall2.rect.right
        # Update y pos
        player_rect.bottom = collided_floor.rect.top
    elif collisions[1] and collisions[2] and len(collided_walls) > 1:
        # When colliding with 2 walls when hitting head off a small point

        # Check if hitting underside of small ledge
        if collided_walls[0].type == collided_walls[1].type:
            wall1 = collided_walls[0]
            wall2 = collided_walls[1]

            if wall1.type == "l":
                if wall1.rect.left > wall2.rect.left:
                    player_rect.right = wall1.rect.left
                else:
                    player_rect.right = wall2.rect.left
            else:
                if wall1.rect.right < wall2.rect.right:
                    player_rect.left = wall1.rect.right
                else:
                    player_rect.left = wall2.rect.right

        player_rect.top = collided_ceiling.rect.bottom
    elif (collided_floor and player_rect.centerx > collided_floor.rect.centerx and collided_walls and collided_walls[0].type == "l"):
        # On floor and colliding with wall above floor (right of player)
        player_rect = basic_collision(
            player_rect, velocity, collisions, collided_floor, collided_ceiling, collided_walls)
    elif (collided_floor and player_rect.centerx < collided_floor.rect.centerx and collided_walls and collided_walls[0].type == "r"):
        # On floor and colliding with wall above floor (left of player)
        player_rect = basic_collision(
            player_rect, velocity, collisions, collided_floor, collided_ceiling, collided_walls)
    elif (collided_ceiling and player_rect.centerx > collided_ceiling.rect.centerx and collided_walls and collided_walls[0].type == "l"):
        # Hit ceiling and wall below ceiling at same time (wall right of player)
        player_rect = basic_collision(
            player_rect, velocity, collisions, collided_floor, collided_ceiling, collided_walls)
    elif (collided_ceiling and player_rect.centerx < collided_ceiling.rect.centerx and collided_walls and collided_walls[0].type == "r"):
        # Hit ceiling and wall below ceiling at same time (wall left of player)
        player_rect = basic_collision(
            player_rect, velocity, collisions, collided_floor, collided_ceiling, collided_walls)

    elif collisions[0] and collisions[2]:
        # Colliding with a corner of a wall and floor
        vertical = player_rect.bottom - collided_floor.rect.top
        if collided_walls[0].type == "l":
            horizontal = player_rect.right - collided_walls[0].rect.left
            if vertical > horizontal:
                player_rect.right = collided_walls[0].rect.left
            else:
                player_rect.bottom = collided_floor.rect.top
        else:
            horizontal = collided_walls[0].rect.right - player_rect.left
            if vertical > horizontal:
                player_rect.left = collided_walls[0].rect.right
            else:
                player_rect.bottom = collided_floor.rect.top

    elif collisions[1] and collisions[2]:
        # Colliding with a corner of a wall and ceiling
        vertical = collided_ceiling.rect.bottom - player_rect.top
        if collided_walls[0].type == "l":
            horizontal = player_rect.right - collided_walls[0].rect.left
            if vertical > horizontal:
                player_rect.right = collided_walls[0].rect.left
            else:
                player_rect.top = collided_ceiling.rect.bottom
        else:
            horizontal = collided_walls[0].rect.right - player_rect.left
            if vertical > horizontal:
                player_rect.left = collided_walls[0].rect.right
            else:
                player_rect.top = collided_ceiling.rect.bottom

    return [player_rect.x, player_rect.y], velocity


def run():
    pygame.init()
    screen = pygame.display.set_mode((1200, 900))

    player = [600.00, 900 * 42.00]
    # Center of player determines level
    current_lvl = int((player[1] + 25) / 900)
    offset = current_lvl * (-screen.height)

    player_velocity = [0, 0]
    map_image, map_rects, map_slopes = load_env("./Jump-King-Tiled/jump-king-map.tmx")
    clock = pygame.Clock()

    running = True
    MOVEMENT_VELOCITY = 3

    rec_colour = {
        "f": "blue",
        "c": "red",
        "l": "green",
        "r": "yellow"
    }

    while running:
        # player_velocity[1] = min(5, player_velocity[1] + 0.1)

        # Center of player determines level
        current_lvl = int((player[1] + 25) / 900)
        if current_lvl < 0:
            current_lvl = 0
        if current_lvl > 42:
            current_lvl = 42
        offset = current_lvl * (-screen.height)
        screen.blit(map_image, (0, offset))

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT]:
            MOVEMENT_VELOCITY = 10
        if keys[pygame.K_s]:
            player_velocity[1] = MOVEMENT_VELOCITY
        if keys[pygame.K_w]:
            player_velocity[1] = -MOVEMENT_VELOCITY
        if keys[pygame.K_d]:
            player_velocity[0] = MOVEMENT_VELOCITY
        if keys[pygame.K_a]:
            player_velocity[0] = -MOVEMENT_VELOCITY

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_s:
                    player_velocity[1] = 0
                if event.key == pygame.K_w:
                    player_velocity[1] = 0
                if event.key == pygame.K_a:
                    player_velocity[0] = 0
                if event.key == pygame.K_d:
                    player_velocity[0] = 0
                if event.key == pygame.K_LSHIFT:
                    MOVEMENT_VELOCITY = 3

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_press = pygame.mouse.get_pos()
                player = [mouse_press[0], mouse_press[1] + abs(offset)]

        for rect in map_rects:
            colour = rec_colour.get(rect.type)
            pygame.draw.rect(screen, colour, pygame.FRect(rect.x, rect.y + offset, rect.width, rect.height), 3)
        
        for slope in map_slopes:
            pygame.draw.line(screen, "blue", slope.start.pos_offset(offset), slope.end.pos_offset(offset), 3)

        player, player_velocity = check_collisions(
            player, map_rects, player_velocity)
        player = [player[0] + player_velocity[0],
                  player[1] + player_velocity[1]]
        pygame.draw.rect(screen, "blue", pygame.FRect(
            (player[0], player[1] + offset), (50, 50)))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run()
