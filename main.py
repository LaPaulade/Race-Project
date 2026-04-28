import sys
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import csv

def resource_path(relative_path):
    """Retourne le chemin absolu d'une ressource, compatible PyInstaller"""
    try:
        # PyInstaller crée une variable temporaire _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Classe représentant un rider avec son numéro, nom et score total
class Rider:
    def __init__(self, number, name):
        self.number = number
        self.name = name
        self.total_points = 0

    def __str__(self):
        return f"#{self.number} {self.name} ({self.total_points} pts)"

# Classe représentant une pool de 4 riders avec les résultats saisis par l'utilisateur
class Pool:
    def __init__(self, riders):
        self.riders = riders  # Liste des 4 riders dans cette pool
        self.results = [0] * len(riders)  # Résultats (positions 1 à 4)
        self.entries = []  # Champs d'entrée associés dans l'UI

    def set_results_from_entries(self):
        # Vérifie que les entrées sont valides et uniques entre 1 et 4
        seen = set()
        values = []
        for entry in self.entries:
            entry.config(bg="white")  # Réinitialise la couleur
            val = entry.get()
            if val not in {'1', '2', '3', '4'}:
                entry.config(bg="red")
                raise ValueError("Les positions doivent être 1, 2, 3 ou 4")
            if val in seen:
                entry.config(bg="red")
                raise ValueError("Chaque position doit être unique dans une pool")
            seen.add(val)
            values.append(int(val))
        self.results = values

# Classe principale qui gère toute l'application graphique et la logique
class LongboardRaceManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion Course Longboard")

        # Chargement du logo si possible
        try:
            self.logo_img = Image.open(resource_path("Cover.png")).resize((300, 100), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(self.logo_img)
        except Exception as e:
            print(f"Erreur lors du chargement du logo: {e}")
            self.logo = None

        self.riders = []  # Liste de tous les riders
        self.pools = []  # Liste de pools actuelles
        self.pool_frames = []  # Références UI pour les frames des pools
        self.round = 0  # Compteur de rounds

        # Configuration des éléments de l'interface utilisateur
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)

        if self.logo:
            logo_label = tk.Label(self.main_frame, image=self.logo)
            logo_label.pack(pady=5)

        self.start_button = tk.Button(self.main_frame, text="Nouvelle Course", command=self.setup_race)
        self.start_button.pack(pady=10)

        self.status = tk.Label(self.main_frame, text="Prêt.")
        self.status.pack(pady=10)

        # Zone scrollable pour les pools
        self.scroll_canvas = tk.Canvas(self.root, height=300)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_frame = tk.Frame(self.scroll_canvas)

        self.scroll_frame.bind("<Configure>", lambda e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

        self.scroll_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.score_frame = tk.Frame(self.root)
        self.score_frame.pack(padx=10, pady=10)

        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side="bottom", fill="x", pady=10)

    def setup_race(self):
        # Initialise une nouvelle course
        self.riders.clear()
        self.round = 0

        # Cacher le bouton "Nouvelle Course"
        self.start_button.pack_forget()

        self.status.config(text="Chargement des riders...")
        self.import_riders_from_csv()

        if not self.riders:
            self.status.config(text="Import annulé ou aucun rider chargé.")
            return

        self.initial_pooling()
        self.start_round()

    def import_riders_from_csv(self):
        # Importation des riders depuis un fichier CSV (séparateur ;)
        filename = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        try:
            with open(filename, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                self.riders = []
                for row in reader:
                    if len(row) >= 3:
                        prenom, nom, numero = row[0].strip(), row[1].strip(), row[2].strip()
                        full_name = f"{prenom} {nom}"
                        self.riders.append(Rider(int(numero), full_name))
            self.status.config(text=f"{len(self.riders)} riders importés.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier: {e}")
            return
        self.riders.sort(key=lambda r: r.number)

    def initial_pooling(self):
        # Crée les premières pools de 4 riders chacune
        self.pools = []
        for i in range(0, len(self.riders), 4):
            self.pools.append(Pool(self.riders[i:i+4]))

    def start_round(self):
        # Lance un nouveau round et affiche les pools
        self.round += 1
        self.status.config(text=f"Round {self.round}")
        self.display_pools()
        self.display_scores()

    def display_pools(self):
        # Affiche les pools dans l'interface graphique
        for frame in self.pool_frames:
            frame.destroy()
        self.pool_frames.clear()
        for widget in self.control_frame.winfo_children():
            widget.destroy()
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for i, pool in enumerate(self.pools):
            row = i // 4
            col = i % 4
            frame = tk.LabelFrame(self.scroll_frame, text=f"Pool {i+1}", padx=10, pady=10, borderwidth=2, relief="groove")
            frame.grid(row=row, column=col, padx=15, pady=15, sticky="n")
            entries = []
            for j in range(4):
                row_frame = tk.Frame(frame, pady=3)
                row_frame.pack(fill="x", pady=2)
                if j < len(pool.riders):
                    rider = pool.riders[j]
                    label = tk.Label(row_frame, text=f"#{rider.number} {rider.name} ({rider.total_points} pts)", width=35, anchor="w")
                    entry = tk.Entry(row_frame, width=5)
                    entry.insert(0, "")
                else:
                    label = tk.Label(row_frame, text="(vide)", width=35, anchor="w")
                    entry = tk.Entry(row_frame, width=5, state="disabled")
                label.pack(side="left")
                entry.pack(side="right")
                entries.append(entry)
            pool.entries = entries
            self.pool_frames.append(frame)

        # Boutons de contrôle sous les pools
        validate_btn = tk.Button(self.control_frame, text="Valider les résultats du round", command=self.validate_round)
        validate_btn.pack(side="left", padx=5)
        # edit_btn = tk.Button(self.control_frame, text="Modifier les résultats", command=self.edit_results)
        # edit_btn.pack(side="left", padx=5)
        export_btn = tk.Button(self.control_frame, text="Exporter résultats CSV", command=self.export_csv)
        export_btn.pack(side="left", padx=5)

    def edit_results(self):
        # Réactive la saisie des résultats
        for pool in self.pools:
            for entry in pool.entries:
                entry.config(state="normal")

    def display_scores(self):
        # Affiche le classement actuel des riders
        for widget in self.score_frame.winfo_children():
            widget.destroy()
        canvas = tk.Canvas(self.score_frame, height=700)
        scrollbar = tk.Scrollbar(self.score_frame, orient="vertical", command=canvas.yview)
        inner_frame = tk.Frame(canvas)
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        tk.Label(inner_frame, text="Classement actuel", font=("Arial", 14, "bold")).pack(pady=5)
        sorted_riders = sorted(self.riders, key=lambda r: (-r.total_points, r.number))
        for i, rider in enumerate(sorted_riders):
            tk.Label(inner_frame, text=f"{i+1}. {rider}", anchor="w").pack(fill="x")

    def validate_round(self):
        # Valide les résultats, met à jour les points et les pools
        try:
            for pool in self.pools:
                pool.set_results_from_entries()
                for entry in pool.entries:
                    entry.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur dans la saisie des positions : {e}")
            return
        self.update_points()
        self.recalculate_pools_montante_descendante()
        self.display_scores()
        self.ask_next_round()

    def update_points(self):
        # Mise à jour du score de chaque rider selon leur position globale dans ce round
        current_ranking = []
        for pool in self.pools:
            ordered = sorted(zip(pool.results, pool.riders))
            current_ranking.extend([r for _, r in ordered])
        for i, rider in enumerate(current_ranking):
            rider.total_points += (len(current_ranking) - i)

    def recalculate_pools_montante_descendante(self):
        # Réorganise les pools selon les règles montante/descendante
        num_pools = len(self.pools)
        new_pool_lists = [[] for _ in range(num_pools)]

        for idx, pool in enumerate(self.pools):
            ordered = sorted(zip(pool.results, pool.riders))
            for rank, (pos, rider) in enumerate(ordered):
                if rank == 0:
                    if idx == 2:
                        new_index = 1
                    else:
                        new_index = max(0, idx - 2)
                elif rank == 1:
                    new_index = max(0, idx - 1)
                elif rank == 2:
                    if idx == num_pools - 1:
                        new_index = num_pools - 2
                    else:
                        new_index = min(num_pools - 1, idx + 1)
                else:
                    new_index = min(num_pools - 1, idx + 2)
                new_pool_lists[new_index].append(rider)

        self.pools = [Pool(riders) for riders in new_pool_lists]

    def ask_next_round(self):
        # Demande à l'utilisateur s'il veut continuer au round suivant
        if len(self.riders) < 4:
            self.status.config(text="Course terminée (moins de 4 riders).")
            self.start_button.pack(pady=10)
            return
        response = messagebox.askyesno("Round suivant ?", "Voulez-vous lancer le round suivant ?")
        if response:
            self.start_round()
        else:
            confirm = messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir terminer la course ?")
            if confirm:
                self.status.config(text="Course terminée.")
                self.display_scores()
                self.export_csv()
                self.start_button.pack(pady=10)

    def export_csv(self):
        # Exporte le classement actuel dans un fichier CSV
        if not self.riders:
            messagebox.showwarning("Avertissement", "Aucun résultat à exporter.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Position", "Numéro", "Nom", "Points Totaux"])
                sorted_riders = sorted(self.riders, key=lambda r: (-r.total_points, r.number))
                for pos, rider in enumerate(sorted_riders, start=1):
                    writer.writerow([pos, rider.number, rider.name, rider.total_points])
            messagebox.showinfo("Export", f"Résultats exportés dans {filename}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export CSV: {e}")

# Point d'entrée principal
if __name__ == "__main__":
    root = tk.Tk()
    app = LongboardRaceManager(root)
    root.mainloop()
