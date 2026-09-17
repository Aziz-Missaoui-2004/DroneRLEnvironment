import csv
import random
import time
from pathlib import Path


class AutomaticMode:
    def __init__(self, environment):
        self.environment = environment

    def run(self, csv_file, render=None, delay=1):
        path = self._resolve_path(csv_file)
        if not path.exists():
            print(f"Fichier introuvable: {path}")
            return False

        action_list = [action for _, action in self._read_actions(path)]
        return self.run_automatic_mode(action_list, render=render, delay=delay, scenario_name=path.name)

    def run_automatic_mode(self, action_list, render=None, delay=0.5, scenario_name="liste d'actions"):
        successful_actions = 0
        attempted_actions = 0
        stop_reason = "liste d'actions terminee"
        failed = False

        if render:
            render(0, f"scenario: {scenario_name}")
            time.sleep(delay)
        else:
            print("===== MODE AUTOMATIQUE =====")

        for step, action in enumerate(action_list, start=1):
            attempted_actions += 1

            if self.environment.state.battery == 0:
                stop_reason = "batterie vide"
                failed = True
                self._show_step(render, step, f"Echec: action {action} impossible car la batterie est vide", delay)
                break

            successors = self.environment.next_states(action)
            if not successors:
                stop_reason = self._failure_reason(action)
                failed = True
                self._show_step(render, step, f"Echec: {stop_reason}", delay)
                break

            selector = random.randrange(len(successors))
            self.environment.state = successors[selector]
            successful_actions += 1
            self._show_step(render, step, f"Succes: {action} -> choix aleatoire #{selector}", delay, action, selector)

            if self.environment.state.crashed:
                stop_reason = "crash detecte"
                break

            if self.environment.state.battery == 0:
                stop_reason = "batterie vide"
                break

        self._print_summary(successful_actions, attempted_actions, stop_reason)
        return not failed

    def _resolve_path(self, csv_file):
        path = Path(csv_file)
        if path.exists():
            return path

        scenario_path = Path("scenarios") / csv_file
        if scenario_path.exists():
            return scenario_path

        return path

    def _read_actions(self, path):
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            step = 0

            for row in reader:
                if not row:
                    continue

                action = row[0].strip().lower()
                if not action or action.startswith("#"):
                    continue

                step += 1
                yield step, action

    def _show_step(self, render, step, message, delay, action=None, selector=None):
        if render:
            render(step, message)
            time.sleep(delay)
            return

        if action is not None and selector is not None:
            self._print_state(step, action, selector)
        else:
            print(f"Etape {step}: {message}")

    def _failure_reason(self, action):
        state = self.environment.state
        canonical_action = self.environment.ACTION_ALIASES.get(action.strip().lower())

        if canonical_action is None:
            return f"Action {action} inconnue"
        if state.crashed:
            return f"Action {action} impossible car le drone est crashe"
        if canonical_action in {"move_step", "avoid_maneuver", "return_home"}:
            if not state.airborne:
                return f"Action {action} impossible car le drone est au sol"
            if state.docked:
                return f"Action {action} impossible car le drone est arrime"
            if state.battery <= 0:
                return f"Action {action} impossible car la batterie est vide"
        if canonical_action == "takeoff" and state.airborne:
            return f"Action {action} impossible car le drone est deja en vol"
        if canonical_action == "takeoff" and state.docked:
            return f"Action {action} impossible car le drone est arrime"
        if canonical_action == "takeoff" and state.battery <= 0:
            return f"Action {action} impossible car la batterie est vide"
        if canonical_action == "dock" and not state.is_at_base():
            return f"Action {action} impossible car le drone n'est pas a la base"
        if canonical_action == "dock" and not state.airborne:
            return f"Action {action} impossible car le drone n'est pas en vol"
        if canonical_action == "undock" and not state.docked:
            return f"Action {action} impossible car le drone n'est pas arrime"
        if canonical_action == "charge_step" and not state.docked:
            return f"Action {action} impossible car le drone n'est pas arrime"
        return f"Action {action} impossible dans l'etat courant"

    def _print_state(self, step, action, selector):
        state = self.environment.state
        print(
            f"Etape {step}: Succes {action}[{selector}] -> "
            f"pos=({state.pos_x},{state.pos_y}) battery={state.battery} "
            f"airborne={state.airborne} docked={state.docked} "
            f"crashed={state.crashed} zones={sorted(state.visited_zones)}"
        )

    def _print_summary(self, successful_actions, attempted_actions, stop_reason):
        state = self.environment.state
        print("\n===== RESUME MODE AUTOMATIQUE =====")
        print(f"Actions tentees: {attempted_actions}")
        print(f"Actions reussies: {successful_actions}")
        print(f"Batterie restante: {state.battery}%")
        print(f"Zones visitees: {sorted(state.visited_zones)}")
        print(f"Etat final: pos=({state.pos_x},{state.pos_y}) crashed={state.crashed} docked={state.docked}")
        print(f"Arret: {stop_reason}")
