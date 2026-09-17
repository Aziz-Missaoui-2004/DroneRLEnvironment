from __future__ import annotations

from typing import Optional

from src.config import *
from src.environment.grid import Grid
from src.environment.state import State


class Environment:
    ACTION_ALIASES = {
        "takeoff": "takeoff",
        "takeoff_cmd": "takeoff",
        "m": "move_step",
        "move": "move_step",
        "move_step": "move_step",
        "a": "avoid_maneuver",
        "avoid": "avoid_maneuver",
        "avoid_maneuver": "avoid_maneuver",
        "h": "return_home",
        "return_home": "return_home",
        "d": "dock",
        "dock": "dock",
        "dock_cmd": "dock",
        "u": "undock",
        "undock": "undock",
        "undock_cmd": "undock",
        "c": "charge_step",
        "charge": "charge_step",
        "charge_step": "charge_step",
        "x": "emergency_stop",
        "emergency_stop": "emergency_stop",
    }

    def __init__(self):
        self.grid = Grid(MAX_X, MAX_Y)
        for x, y in DANGER_SET:
            self.grid.set_dangerous(x, y)
        self.reset()

    def reset(self):
        self.state = State(
            pos_x=BASE_X,
            pos_y=BASE_Y,
            base_x=BASE_X,
            base_y=BASE_Y,
            battery=BATTERY_INITIAL,
            obstacle_distance=0 if (BASE_X, BASE_Y) in DANGER_SET else 2,
        )
        self.state.visited_zones.add(self.grid.zoneOf(BASE_X, BASE_Y))

    def get_state(self) -> State:
        return self.state.copy()

    @staticmethod
    def state_key(state: State):
        return (
            state.pos_x,
            state.pos_y,
            state.base_x,
            state.base_y,
            state.battery,
            state.obstacle_distance,
            state.docked,
            state.airborne,
            state.crashed,
            tuple(sorted(state.visited_zones)),
        )

    def check_invariant(self, state: Optional[State] = None) -> tuple[bool, str]:
        s = self.state if state is None else state

        if not (0 <= s.pos_x <= MAX_X and 0 <= s.pos_y <= MAX_Y):
            return False, "Position hors bornes"
        if not (0 <= s.base_x <= MAX_X and 0 <= s.base_y <= MAX_Y):
            return False, "Base hors bornes"
        if not (0 <= s.battery <= BATTERY_MAX):
            return False, "Batterie hors bornes"
        if s.obstacle_distance < 0:
            return False, "obstacle_distance négatif"
        if not isinstance(s.docked, bool) or not isinstance(s.airborne, bool) or not isinstance(s.crashed, bool):
            return False, "Indicateurs booléens invalides"
        if not all(1 <= z <= ZONE_COUNT for z in s.visited_zones):
            return False, "Zone visitée invalide"
        if s.crashed and s.airborne:
            return False, "crashed et airborne incompatibles"
        if s.docked and s.airborne:
            return False, "docked et airborne incompatibles"
        if s.docked and not s.is_at_base():
            return False, "docked implique position à la base"
        if s.crashed and s.docked:
            return False, "crashed et docked incompatibles"
        return True, "OK"

    def _spawn(self, state: State, **updates) -> State:
        new_state = state.copy()
        for key, value in updates.items():
            setattr(new_state, key, value)
        ok, msg = self.check_invariant(new_state)
        if not ok:
            raise ValueError(f"Invariant violé après transition: {msg}")
        return new_state

    def _can_takeoff(self, state: State) -> bool:
        return (not state.crashed and not state.airborne and not state.docked and state.battery > 0)

    def _can_fly(self, state: State) -> bool:
        return (not state.crashed and state.airborne and not state.docked and state.battery > 0)

    def _can_dock(self, state: State) -> bool:
        return (not state.crashed and state.airborne and not state.docked and state.is_at_base())

    def _can_undock(self, state: State) -> bool:
        return (not state.crashed and state.docked and state.battery > 0)

    def _can_charge(self, state: State) -> bool:
        return (not state.crashed and state.docked)

    def _set_obstacle_distance(self, state: State, x: int, y: int) -> int:
        return 0 if self.grid.is_dangerous(x, y) else 2

    def check_crash(self, state: Optional[State] = None) -> State:
        s = self.state if state is None else state
        if s.obstacle_distance == 0:
            crashed_state = self.emergency_stop(s)[0]
            if state is None:
                self.state = crashed_state
            return crashed_state
        return s

    def _move_to_cell(
        self,
        state: State,
        x: int,
        y: int,
        battery_cost: int,
        obstacle_distance: Optional[int] = None,
    ) -> State:
        is_dangerous = self.grid.is_dangerous(x, y)
        new_state = self._spawn(
            state,
            pos_x=x,
            pos_y=y,
            battery=state.battery - battery_cost,
            obstacle_distance=0 if is_dangerous else (2 if obstacle_distance is None else obstacle_distance),
        )
        new_state.visited_zones.add(self.grid.zoneOf(x, y))
        new_state = self.check_crash(new_state)

        ok, msg = self.check_invariant(new_state)
        if not ok:
            raise ValueError(f"Invariant violé après déplacement: {msg}")

        return new_state

    def next_states(self, action: str, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        action = self.ACTION_ALIASES.get(action.strip().lower(), "")

        if action == "takeoff":
            return self.takeoff_cmd(s)
        if action == "move_step":
            return self.move_step(s)
        if action == "avoid_maneuver":
            return self.avoid_maneuver(s)
        if action == "return_home":
            return self.return_home(s)
        if action == "dock":
            return self.dock_cmd(s)
        if action == "undock":
            return self.undock_cmd(s)
        if action == "charge_step":
            return self.charge_step(s)
        if action == "emergency_stop":
            return self.emergency_stop(s)

        return []

    def available_actions(self, state: Optional[State] = None) -> list[str]:
        s = self.state if state is None else state
        actions = []

        if self._can_takeoff(s):
            actions.append("takeoff")
        if self._can_fly(s):
            actions.append("move_step")
            actions.append("avoid_maneuver")
            actions.append("return_home")
        if self._can_dock(s):
            actions.append("dock_cmd")
        if self._can_undock(s):
            actions.append("undock_cmd")
        if self._can_charge(s):
            actions.append("charge_step")

        actions.append("emergency_stop")
        return actions

    def apply_action(self, action: str, selector: int = 0) -> bool:
        successors = self.next_states(action, self.state)
        if not successors:
            return False

        selector = max(0, min(selector, len(successors) - 1))
        self.state = successors[selector]
        return True

    def takeoff_cmd(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_takeoff(s):
            return []

        new_state = self._spawn(
            s,
            airborne=True,
            obstacle_distance=self._set_obstacle_distance(s, s.pos_x, s.pos_y),
        )
        return [self.check_crash(new_state)]

    def move_step(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_fly(s):
            return []

        successors = []
        for nx, ny in self.grid.neighbors(s.pos_x, s.pos_y):
            successors.append(self._move_to_cell(s, nx, ny, MOVE_COST))

        return successors

    def avoid_maneuver(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_fly(s) or s.battery <= 1:
            return []

        neighbors = self.grid.neighbors(s.pos_x, s.pos_y)
        safe_neighbors = [(x, y) for x, y in neighbors if not self.grid.is_dangerous(x, y)]
        candidates = safe_neighbors if safe_neighbors else neighbors

        successors = []
        for nx, ny in candidates:
            successors.append(
                self._move_to_cell(
                    s,
                    nx,
                    ny,
                    AVOID_COST,
                    obstacle_distance=2 if safe_neighbors else None,
                )
            )

        return successors

    def return_home(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_fly(s):
            return []

        nx = s.pos_x
        ny = s.pos_y

        if s.pos_x < s.base_x:
            nx += 1
        elif s.pos_x > s.base_x:
            nx -= 1

        if s.pos_y < s.base_y:
            ny += 1
        elif s.pos_y > s.base_y:
            ny -= 1

        return [self._move_to_cell(s, nx, ny, MOVE_COST)]

    def dock_cmd(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_dock(s):
            return []

        new_state = self._spawn(
            s,
            docked=True,
            airborne=False,
        )
        return [new_state]

    def undock_cmd(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_undock(s):
            return []

        new_state = self._spawn(
            s,
            docked=False,
            airborne=True,
        )
        new_state.visited_zones.add(self.grid.zoneOf(s.base_x, s.base_y))

        ok, msg = self.check_invariant(new_state)
        if not ok:
            raise ValueError(f"Invariant violé après undock_cmd: {msg}")

        return [new_state]

    def charge_step(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        if not self._can_charge(s):
            return []

        new_battery = s.battery + CHARGE_STEP if s.battery <= 95 else BATTERY_MAX
        new_state = self._spawn(
            s,
            battery=new_battery,
        )
        return [new_state]

    def emergency_stop(self, state: Optional[State] = None) -> list[State]:
        s = self.state if state is None else state
        new_state = self._spawn(
            s,
            crashed=True,
            airborne=False,
            docked=False,
            obstacle_distance=0,
        )
        return [new_state]
