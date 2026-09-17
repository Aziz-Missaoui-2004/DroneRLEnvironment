class InteractiveMode:
    """
    Mode console manuel.
    L'utilisateur choisit une action, puis choisit un successeur
    quand l'action est non déterministe.
    """

    def __init__(self, environment):
        self.environment = environment

    def run(self):
        print("===== MODE INTERACTIF =====")
        print("Actions: takeoff, move, avoid, return_home, dock, undock, charge, emergency_stop, reset, show, quit")

        while True:
            self._print_state()
            action = input("\nAction: ").strip().lower()

            if action in {"quit", "q", "exit"}:
                break

            if action == "show":
                continue

            if action == "reset":
                self.environment.reset()
                continue

            successors = self.environment.next_states(action)
            if not successors:
                print("Action impossible dans l'état courant.")
                continue

            if len(successors) == 1:
                self.environment.state = successors[0]
                continue

            print("Successeurs possibles:")
            for i, s in enumerate(successors):
                print(
                    f"[{i}] pos=({s.pos_x},{s.pos_y}) battery={s.battery} "
                    f"airborne={s.airborne} docked={s.docked} crashed={s.crashed} "
                    f"zones={sorted(s.visited_zones)}"
                )

            try:
                idx = int(input("Choix du successeur: ").strip())
            except ValueError:
                idx = 0

            idx = max(0, min(idx, len(successors) - 1))
            self.environment.state = successors[idx]

        print("Fin du mode interactif.")

    def _print_state(self):
        s = self.environment.state
        print(
            f"\npos=({s.pos_x},{s.pos_y}) base=({s.base_x},{s.base_y}) "
            f"battery={s.battery} obstacle={s.obstacle_distance} "
            f"docked={s.docked} airborne={s.airborne} crashed={s.crashed} "
            f"zones={sorted(s.visited_zones)}"
        )