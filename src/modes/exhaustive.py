from collections import defaultdict

from src.environment.environment import Environment


class ExhaustiveMode:
    def __init__(self, environment: Environment):
        self.environment = environment
        self.reset()

    def reset(self):
        self.visited = set()
        self.graph = defaultdict(list)
        self.states = {}
        self.stats = {
            "states_explored": 0,
            "terminal_states": 0,
            "crash_states": 0,
            "deadlock_states": 0,
            "depth_limit_states": 0,
            "transitions": 0,
            "max_depth_reached": 0,
            "max_visited_zones": 0,
            "max_branching_factor": 0,
            "nondeterministic_actions": 0,
            "max_successors_for_action": 0,
            "depth_counts": {},
            "action_counts": {},
        }

    def run(self, max_depth=20, max_breadth=-1, verbose=False):
        self.reset()
        initial = self.environment.get_state()
        self._explore(initial, max_depth, max_breadth, depth=0, verbose=verbose)
        return self.stats

    def _explore(self, state, remaining_depth, max_breadth, depth, verbose=False):
        key = self.environment.state_key(state)

        if key in self.visited:
            return

        self.visited.add(key)
        self.states[key] = state.copy()
        self.stats["states_explored"] += 1
        self.stats["max_depth_reached"] = max(self.stats["max_depth_reached"], depth)
        self.stats["max_visited_zones"] = max(self.stats["max_visited_zones"], len(state.visited_zones))
        self.stats["depth_counts"][depth] = self.stats["depth_counts"].get(depth, 0) + 1

        if state.crashed:
            self.stats["terminal_states"] += 1
            self.stats["crash_states"] += 1
            return

        if remaining_depth != -1 and remaining_depth <= 0:
            self.stats["depth_limit_states"] += 1
            return

        transitions = self._transitions(state)
        self.stats["max_branching_factor"] = max(self.stats["max_branching_factor"], len(transitions))

        if not transitions:
            self.stats["terminal_states"] += 1
            self.stats["deadlock_states"] += 1
            return

        count = 0
        for action, next_state in transitions:
            if max_breadth != -1 and count >= max_breadth:
                break

            next_key = self.environment.state_key(next_state)
            self.graph[key].append((action, next_key))
            self.stats["transitions"] += 1
            self.stats["action_counts"][action] = self.stats["action_counts"].get(action, 0) + 1

            next_depth = -1 if remaining_depth == -1 else remaining_depth - 1
            if verbose:
                print(f"{depth}: {action} -> {next_key}")

            self._explore(next_state, next_depth, max_breadth, depth + 1, verbose)
            count += 1

    def _transitions(self, state):
        transitions = []
        actions = self.environment.available_actions(state)

        for action in actions:
            next_states = self.environment.next_states(action, state)
            self.stats["max_successors_for_action"] = max(
                self.stats["max_successors_for_action"],
                len(next_states),
            )

            if len(next_states) > 1:
                self.stats["nondeterministic_actions"] += 1

            for next_state in next_states:
                transitions.append((action, next_state))

        return transitions

    def get_graph(self):
        return dict(self.graph)

    def get_states(self):
        return dict(self.states)

    def summary(self):
        return self.stats.copy()
