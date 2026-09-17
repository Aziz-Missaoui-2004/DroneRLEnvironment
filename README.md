# Drone RL Environment

A discrete drone patrol simulator for exploring coverage, energy management and
safety decisions. The environment models a drone on a 2D grid, with a fixed base,
limited battery capacity and dangerous cells.

The project currently provides a simulation engine, a console interface, CSV
scenario playback and state-space exploration. A graphical interface and a
reinforcement learning agent are planned; no trained model or reward function is
included yet.

## Features

- A configurable grid split into four patrol zones.
- Takeoff, movement, obstacle avoidance, return to base, docking and charging.
- Battery consumption and automatic crashes when entering dangerous cells.
- State invariant checks after transitions.
- Interactive console control and CSV scenario playback.
- A transition graph explorer with optional depth and branching limits.
- Direct Python access to states, available actions and possible successors.

## Quick start

Requires **Python 3.10 or newer**. The current simulator uses only the Python
standard library; no third-party packages are needed.

```bash
git clone https://github.com/Aziz-Missaoui-2004/DroneRLEnvironment.git
cd DroneRLEnvironment
python main.py
```

Use `python3` if that is the name of your Python executable. Run the commands from
the repository root so that imports and scenario paths resolve correctly.

Choose one of the three modes in the menu:

| Mode | Purpose |
| --- | --- |
| Interactive | Choose actions and inspect the grid after each transition. |
| Automatic | Run a sequence of actions from a CSV file. |
| Exhaustive | Explore reachable states and collect transition statistics. |

For a first demonstration, select automatic mode and enter `energy_cycle.csv`.
It demonstrates movement, return to base, charging and departure.

## Console controls

| Key | Action |
| --- | --- |
| `t` | Take off |
| `m` | Move to a neighboring cell |
| `a` | Perform an avoidance maneuver |
| `h` | Take a step toward the base |
| `d` | Dock at the base |
| `u` | Undock and resume flight |
| `c` | Charge the battery |
| `x` | Trigger an emergency stop / crash |
| `r` | Reset the interactive simulation |
| `q` | Exit interactive mode |

The grid displays `D` for the drone, `B` for the base and `X` for dangerous cells.
Numbers `1` through `4` mark visited patrol zones; they do not indicate that every
cell in that zone has been visited. The base zone is visited at initialization.

## Simulation rules

The default map has 6 by 6 cells, coordinates from 0 to 5, and a base at `(0, 0)`.
Dangerous cells are `(2, 2)`, `(3, 3)` and `(4, 1)`. The battery starts at 100.
Configuration is defined in [`src/config.py`](src/config.py).

- Regular movement generates all valid cardinal neighbors and costs one battery unit.
- Avoidance generates safe neighbors when available and costs two units. If every
  neighbor is dangerous, it still generates moves to those cells.
- Return to base reduces the distance on each coordinate simultaneously and costs
  one unit. It can move diagonally and does not plan a safe route around obstacles.
- Docking requires the drone to be in flight at the base. Charging adds five units,
  capped at 100. Undocking returns the drone directly to flight.
- Entering a dangerous cell triggers a crash and ends the normal mission.

For movement and avoidance, the console and automatic modes choose a successor
uniformly at random. The user chooses the action type rather than the direction.
The graph explorer considers every generated successor, subject to its limits.

## Use the engine from Python

```python
from src.environment.environment import Environment

env = Environment()
env.apply_action("takeoff")

state = env.get_state()
print(env.available_actions(state))

for successor in env.next_states("move_step", state):
    print(successor.pos_x, successor.pos_y, successor.battery)
```

`get_state()` returns a copy. `next_states()` generates successors without changing
the current state. `apply_action(action, selector=0)` applies the selected successor;
its default is the first successor, rather than a random one.

## Scenarios and graph exploration

Scenario files contain one action per line. Blank lines and lines beginning with
`#` are ignored. Examples are available in [`scenarios/`](scenarios/).
Playback stops when the sequence ends, an action cannot be executed, a crash
occurs or the battery reaches zero. Random successor selection means that replaying
the same file can produce different trajectories.

For graph exploration, `-1` disables the corresponding depth or branching limit.
The branching limit caps outgoing transitions considered per state, rather than
the number of states at a depth. Begin with a small depth to inspect the output.

## Current limitations

- This is a discrete decision environment, without flight physics or real drone control.
- The obstacle signal is an abstract indicator: 0 on dangerous cells, 2 otherwise.
- Coverage records visited zones, not individual cells. Full coverage does not
  automatically end the simulation.
- The depth-limited DFS can miss states reachable within the requested depth,
  because it does not revisit states reached later through a shorter path.
- Battery depletion handling and automatic-mode success reporting need refinement.
  In particular, playback can report success after a crash and blocks charging
  at zero battery even when the drone is docked.
- Avoidance can appear in the available action list at battery level 1 even though
  it cannot execute. These engine issues are scheduled for the reliability phase.

## Project structure

```text
main.py                    Console menu and grid rendering
pyproject.toml             Project metadata and Python requirement
src/config.py              Map and battery configuration
src/environment/state.py   Drone state representation
src/environment/grid.py    Grid geometry, zones and dangerous cells
src/environment/environment.py
                           Action preconditions, transitions and invariants
src/modes/                 Playback, exploration and legacy manual interface
scenarios/                 CSV demonstrations
```

## Next milestones

1. Strengthen engine consistency, reproducibility and automated validation.
2. Add a dynamic graphical view with a trajectory, battery status and playback controls.
3. Define the learning task, integrate an RL agent and evaluate it against a baseline.

The simulator originated as an academic environment-modeling project and is being
developed into a portfolio project. Licensing has not yet been selected.
