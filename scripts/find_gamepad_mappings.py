# Contenu de find_gamepad_mappings.py

import pygame

# Initialisation de Pygame
pygame.init()

# Vérification et initialisation de la manette
if pygame.joystick.get_count() == 0:
    print("ERREUR: Aucune manette détectée.")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Manette détectée : {joystick.get_name()}")
print("Appuyez sur les boutons et bougez les joysticks pour voir leur numéro.")
print("Appuyez sur CTRL+C dans le terminal ou fermez la fenêtre pour quitter.")
print("-" * 30)

# Créer une petite fenêtre. Pygame a besoin d'une fenêtre active
# pour gérer correctement les événements.
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("Testeur de Manette")

# Boucle principale
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- Détection des AXES ---
        if event.type == pygame.JOYAXISMOTION:
            # Arrondir la valeur pour une meilleure lisibilité
            axis_value = round(event.value, 3)
            print(f"--- AXE Mouvement ---  Numéro: {event.axis}  |  Valeur: {axis_value}")

        # --- Détection des BOUTONS ---
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"--- BOUTON Pressé ---  Numéro: {event.button}")

        if event.type == pygame.JOYBUTTONUP:
            print(f"--- BOUTON Relâché --  Numéro: {event.button}")

        # --- Détection du D-Pad (Hat) ---
        if event.type == pygame.JOYHATMOTION:
            print(f"--- D-PAD (Hat) ---  Numéro: {event.hat}  |  Valeur: {event.value}")

# Nettoyage
pygame.quit()