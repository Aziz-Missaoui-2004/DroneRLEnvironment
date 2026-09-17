from dataclasses import dataclass, field


@dataclass
class State:
    pos_x: int
    pos_y: int
    base_x: int
    base_y: int
    battery: int

    obstacle_distance: int = 2
    docked: bool = False
    airborne: bool = False
    crashed: bool = False
    visited_zones: set[int] = field(default_factory=set)

    def copy(self) -> "State":
        return State(
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            base_x=self.base_x,
            base_y=self.base_y,
            battery=self.battery,
            obstacle_distance=self.obstacle_distance,
            docked=self.docked,
            airborne=self.airborne,
            crashed=self.crashed,
            visited_zones=self.visited_zones.copy(),
        )

    def is_at_base(self) -> bool:
        return self.pos_x == self.base_x and self.pos_y == self.base_y