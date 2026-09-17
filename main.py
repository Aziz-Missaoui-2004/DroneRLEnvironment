import random
import sys
import os
from pathlib import Path
sys.path.append('.')

from src.config import DANGER_SET, MAX_X, MAX_Y
from src.environment.environment import Environment
from src.modes.automatic import AutomaticMode
from src.modes.exhaustive import ExhaustiveMode

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()


ACTION_KEYS = {
    "t": "takeoff",
    "m": "move_step",
    "a": "avoid_maneuver",
    "h": "return_home",
    "d": "dock_cmd",
    "u": "undock_cmd",
    "c": "charge_step",
    "x": "emergency_stop",
}

ACTION_LABELS = {
    "takeoff": ("t", "decoller"),
    "move_step": ("m", "bouger"),
    "avoid_maneuver": ("a", "eviter"),
    "return_home": ("h", "retour base"),
    "dock_cmd": ("d", "arrimer"),
    "undock_cmd": ("u", "desarrimer"),
    "charge_step": ("c", "charger"),
    "emergency_stop": ("x", "crash stop"),
}


def setup_environment():
    return Environment()


def cell_symbol(env, x, y):
    state = env.state
    is_drone = state.pos_x == x and state.pos_y == y
    is_base = state.base_x == x and state.base_y == y
    is_danger = env.grid.is_dangerous(x, y)
    is_visited = env.grid.zoneOf(x, y) in state.visited_zones

    if is_drone:
        return "D"
    if is_base:
        return "B"
    if is_danger:
        return "X"
    if is_visited:
        return str(env.grid.zoneOf(x, y))
    return "."


def drone_status(state):
    if state.crashed:
        return "crashe"
    if state.docked:
        return "arrime"
    if state.airborne:
        return "en vol"
    return "au sol"


def print_grid(env, step=0, last_action=None, title="MODE INTERACTIF"):
    state = env.state
    print(f"===== {title} =====")
    print(f"Etape {step} | Statut: {drone_status(state)} | Batterie: {state.battery}% | Zones: {sorted(state.visited_zones)}")
    print(f"Position: ({state.pos_x},{state.pos_y}) | Base: ({state.base_x},{state.base_y}) | Obstacle: {state.obstacle_distance}")
    if last_action:
        print(f"Derniere action: {last_action}")

    print("\nGrille:")
    print("     " + " ".join(str(x) for x in range(env.grid.max_x + 1)))
    print("   +" + "--" * (env.grid.max_x + 1) + "+")

    for y in range(env.grid.max_y, -1, -1):
        row = [cell_symbol(env, x, y) for x in range(env.grid.max_x + 1)]
        print(f"{y:>2} | " + " ".join(row) + " |")

    print("   +" + "--" * (env.grid.max_x + 1) + "+")
    print("Legende: D=drone, B=base, X=danger, 1-4=zone visitee, .=non visite")


def action_prompt(actions):
    parts = []
    for action in actions:
        key, label = ACTION_LABELS[action]
        parts.append(f"[{key}] {label}")

    return "  ".join(parts)


def print_available_scenarios():
    files = sorted(Path("scenarios").glob("*.csv"))
    if not files:
        print("Aucun fichier CSV trouve dans scenarios/.")
        return

    print("\nScenarios disponibles:")
    for path in files:
        print(f"- {path.name}")


def render_automatic_step(env, step, message):
    clear_console()
    print_grid(env, step, message, title="MODE AUTOMATIQUE")


def print_exhaustive_report(stats, max_depth, max_breadth):
    print("\n===== RAPPORT EXPLORATION EXHAUSTIVE =====")
    print(f"Grille: 0..{MAX_X} x 0..{MAX_Y}")
    print(f"Zones dangereuses: {sorted(DANGER_SET)}")
    print(f"Profondeur maximale demandee: {max_depth} (-1 = sans limite)")
    print(f"Largeur maximale demandee: {max_breadth} (-1 = sans limite)")

    print("\nPrincipe:")
    print("- DFS recursif depuis l'etat initial")
    print("- les transitions sont parcourues selon l'algorithme Explore(s, S, maxDepth, maxBreadth)")
    print("- les actions non deterministes generent tous leurs successeurs")
    print("- les etats deja visites ne sont pas explores deux fois")

    print("\nSynthese:")
    print(f"- Etats uniques explores: {stats['states_explored']}")
    print(f"- Transitions generees: {stats['transitions']}")
    print(f"- Profondeur maximale atteinte: {stats['max_depth_reached']}")
    print(f"- Zones visitees au maximum: {stats['max_visited_zones']}/4")
    print(f"- Facteur de branchement max: {stats['max_branching_factor']}")
    print(f"- Successeurs max pour une action: {stats['max_successors_for_action']}")

    print("\nEtats d'arret:")
    print(f"- Etats crash: {stats['crash_states']}")
    print(f"- Etats sans successeur: {stats['deadlock_states']}")
    print(f"- Etats non developpes car profondeur limite atteinte: {stats['depth_limit_states']}")

    print("\nNon-determinisme:")
    print(f"- Actions avec plusieurs successeurs rencontrees: {stats['nondeterministic_actions']}")
    print("- Interactif/automatique: un successeur est tire aleatoirement")
    print("- Exhaustif: tous les successeurs sont conserves dans le graphe")

    print("\nTransitions par action:")
    for action, count in sorted(stats["action_counts"].items()):
        print(f"- {action}: {count}")

    print("\nEtats par profondeur:")
    for depth, count in sorted(stats["depth_counts"].items()):
        print(f"- profondeur {depth}: {count} etat(s)")


def run_interactive_console(env):
    step = 0
    last_action = None

    while True:
        clear_console()
        print_grid(env, step, last_action)

        actions = env.available_actions()
        print("\nActions:", action_prompt(actions))
        print("Commandes: [r] reset  [q] quitter")
        user_input = input("> ").strip().lower()

        if user_input in {"quit", "q", "exit"}:
            break

        if user_input in {"reset", "r"}:
            env.reset()
            step = 0
            last_action = "reset"
            continue

        action = ACTION_KEYS.get(user_input, user_input)
        successors = env.next_states(action)
        if not successors:
            input("Action impossible dans l'etat courant. Entree pour continuer...")
            continue

        selector = random.randrange(len(successors))
        env.state = successors[selector]
        step += 1
        last_action = f"{action} -> choix aleatoire #{selector}"

        if env.state.crashed:
            clear_console()
            print_grid(env, step, last_action)
            input("\nCrash: etat terminal atteint. Entree pour quitter...")
            break


def main():
    clear_console()
    print(" ====================== ")
    print("|| SIMULATEUR DE DRONE ||")
    print(" ====================== ")

    env = setup_environment()
    
    print("""\nModes:
    1. Interactive
    2. Automatique (fichier CSV)
    3. Exhaustif (exploration de tous les états)
    4. Quitter
    """)
    
    choice = input("Choisissez un mode (1-4): ").strip()
    
    match choice:
        case "1":
            run_interactive_console(env)
        
        case "2":
            print_available_scenarios()
            csv_file = input("Entrez le nom du fichier CSV: ").strip()
            mode = AutomaticMode(env)
            mode.run(
                csv_file,
                render=lambda step, message: render_automatic_step(env, step, message),
                delay=0.5,
            )
        
        case "3":
            try:
                maxDepth = int(input("entrer la profondeur maximale (-1 = sans limite, ex: 15): "))
            except ValueError:
                print("Valeur invalide, utilisation de 15 par défaut.")
                maxDepth = 15

            try:
                maxBreadth = int(input("entrer la largeur maximale (-1 = sans limite, ex: -1): "))
            except ValueError:
                print("Valeur invalide, utilisation de -1 par défaut.")
                maxBreadth = -1

            mode = ExhaustiveMode(env)
            stats = mode.run(max_depth=maxDepth, max_breadth=maxBreadth)
            print_exhaustive_report(stats, maxDepth, maxBreadth)
        
        case "4":
            print("Quitter...")
        
        case _:
            print("Choix invalide. Veuillez réessayer.")


if __name__ == "__main__":
    main()
