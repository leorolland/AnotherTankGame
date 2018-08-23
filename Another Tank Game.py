########## IMPORTATIONS ##########
import pygame
from pygame.locals import *
import pygame.mixer
from PIL import Image
import time
from operator import add
import socket
import sys
import _thread


########## FONCTIONS GLOBALES ##########
def image_convert(img):
    """********** Fonction convertissant une image PIL en une image pygame **********"""
    mode = img.mode
    size = img.size
    data = img.tobytes()
    return pygame.image.fromstring(data, size, mode)


def load_level(level):
    plateau = open(level, "r")
    for line in plateau:
        if "block" in line:
            type, size, x, y = map(str, line.split(' '))
            n = 1
        else:
            type, n, size, x, y = map(str, line.split(' '))
        x = int(x)
        y = int(y.replace('\n', ''))
        n = int(n)
        if size == 'big':
            size = 256
            texture = "obstacle_big.png"
        elif size == 'medium':
            size = 128
            texture = "obstacle_medium.png"
        elif size == 'small':
            size = 64
            texture = "obstacle_small.png"
        for i in range(n):
            Obstacle(fenetre=fenetre, x=x, y=y, size=size, texture=texture)
            if type == "vertical":
                y += size
            else:
                x += size


########## FONCTIONS DE BOUTONS ##########
def menu_local():
    fenetre.set_state("menu_local")


def menu_multiplayer():
    fenetre.set_state("menu_multiplayer")


def replay_local():
    load_level("level.txt")
    fenetre.set_state("game_local")


def stop():
    fenetre.set_state("menu_main")


def confirm():
    if (fenetre.state == "menu_local" or fenetre.state == "menu_multiplayer") and fenetre.textbox.text != "":
        fenetre.textbox.activated = False
        fenetre.set_state(fenetre.state, fenetre.sub_menu+1)


def quit():
    global running
    running = False


def cancel():
    fenetre.textbox.activated = False
    if fenetre.sub_menu == 0 and fenetre.state == "menu_local":
        fenetre.set_state("menu_main")
    else:
        fenetre.set_state(fenetre.state, fenetre.sub_menu - 1)


########## OBJETS ##########
class SpriteSheet(object):
    """********** Objet définissant un ensemble de sprites à partir d'une image **********"""

    def __init__(self, image: str, columns=1, rows=1, scale=1, alpha=255):
        self.image = Image.open(image)  # image : image originale au format PIL
        self.width, self.height = self.image.size   # width & height : largeur et hauteur de l'image originale
        self.width = self.width * scale
        self.height = self.height * scale
        self.sprites_PIL = []   # sprites_PIl : matrice contenant tout les sprites au format PIL
        self.sprites_pygame = []    # sprites_pygame : matrice contenant tout les sprites au format pygame

        # Redimensionnement de l'image
        self.image = self.image.resize((self.width, self.height))

        # Division de l'image
        for row in range(rows):
            self.sprites_PIL.append([])
            self.sprites_pygame.append([])
            for column in range(columns):
                self.sprites_PIL[row].append(self.image.crop((column/columns*self.width, row/rows*self.height, (column+1)/columns*self.width, (row+1)/rows*self.height)))
                self.sprites_pygame[row].append(image_convert(self.sprites_PIL[row][column]).convert())
                self.sprites_pygame[row][column].set_colorkey((0, 0, 0))
                if alpha != 255:
                    self.sprites_pygame[row][column].set_alpha(alpha)

    # Méthode retournant l'image correspondant à la colonne et la ligne donnée
    def getSprite(self, column=0, row=0):
        return self.sprites_pygame[row][column]


class GameWindow(object):
    """********** Objet définissant une fenêtre **********"""

    def __init__(self, background: str, width=500, height=500, name="GameWindow"):
        pygame.init()
        pygame.key.set_repeat(1, 0)
        self.name = name    # name : Nom de la fenêtre
        pygame.display.set_caption(self.name, "")
        self.state = "menu_main"
        self.sub_menu = 0
        pygame.mouse.set_visible(False)

        self.width = width  # width : largeur de la fenêtre
        self.height = height    # height : hauteur de la fenêtre

        self.root = pygame.display.set_mode((self.width, self.height), FULLSCREEN)  # root : Fenêtre de jeu
        background = Image.open(background).resize((self.width, self.height))
        self.background = image_convert(background).convert()    # background : Image de fond de la fenêtre

        self.local_name_1 = "anonyme"
        self.local_name_2 = "anonyme"
        self.font = pygame.font.Font("LCD_Solid.ttf", 64)
        self.menu_title = "MENU PRINCIPAL"
        self.menu_title_display = self.font.render(self.menu_title, 0, (255, 255, 255))

        self.joueurs = []   # joueurs : Liste contenant l'ensemble des joueurs à rendre
        self.missiles = []  # missiles : Liste contenant l'ensemble des missiles à rendre
        self.obstacles = []
        self.boutons = []

    # Méthode permettant de rendre tous les joueurs avec leur pseudo et vie, ainsi que les missiles
    def render(self):
        self.root.blit(self.background, (0, 0))

        if "menu" in self.state:
            self.root.blit(menu_image, (450, 450))
            self.root.blit(self.menu_title_display, (962-self.font.size(self.menu_title)[0]/2, 480))
            self.root.blit(logo, (450, 0))
            for bouton in self.boutons:
                self.root.blit(bouton.display, bouton.coords)

        if self.state == "menu_local" or self.state == "menu_multiplayer":
            pygame.draw.rect(fenetre.root, (0, 0, 0), self.textbox.background_rect)
            self.root.blit(self.textbox.text_display, self.textbox.coords)

        elif "game" in self.state:

            # Rendu des missiles
            for missile in self.missiles:
                self.root.blit(missile.image, missile.coords)

            # Rendu des obstacles
            for obstacle in self.obstacles:
                self.root.blit(obstacle.image, obstacle.collision)

            # Rendu des joueurs
            for joueur in self.joueurs:
                # Affichage du tank
                if joueur.invulnerability_counter % 8 in [0, 1, 2, 3]:
                    self.root.blit(joueur.tank_display, joueur.coords)
            for joueur in self.joueurs:
                # Affichage de l'explosion
                if joueur.invulnerability_counter > 56:
                    self.root.blit(explosion.getSprite(60-joueur.invulnerability_counter), joueur.coords)
                if joueur.invulnerable:
                    joueur.invulnerability_counter -= 1
                    if joueur.invulnerability_counter == 0:
                        joueur.invulnerable = False
                # Affichage de la vie
                self.root.blit(joueur.life_display, [joueur.coords[0], joueur.coords[1]-32])
                # Affichage du pseudo
                self.root.blit(joueur.pseudo_display, [joueur.coords[0]+64-joueur.font.size(joueur.pseudo)[0]/2, joueur.coords[1]-64])

        pygame.display.flip()

    def set_state(self, state: str, sub_menu=0):

        self.state = state
        self.sub_menu = sub_menu

        self.joueurs = []
        self.missiles = []
        self.obstacles = []
        self.boutons = []

        if "menu" in state:
            pygame.mouse.set_visible(True)
            pygame.key.set_repeat(500, 30)

        if "game" in self.state:
            pygame.mouse.set_visible(False)
            pygame.key.set_repeat(1, 30)

        if state == "game_local":
            global J1, J2
            J1 = Joueur(fenetre=self, texture="tank_blue.png", pseudo=self.local_name_1, coords=[200, 200])
            J2 = Joueur(fenetre=self, texture="tank_red.png", pseudo=self.local_name_2, coords=[800, 800])

        elif state == "game_multiplayer":
            global clients, mySocket
            ######### CREATION SOCKET #########
            # Création du socket
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Envoi de la requête de connexion au serveur
            try:
                mySocket.connect((HOST, PORT))
            except socket.error:
                print("La connexion à échoué.")
                sys.exit()
            print("Connexion établie avec le serveur")
            # Liste des clients
            clients = []

            _thread.start_new_thread(recepteurMessageThread, ())
            mySocket.send( ("place %s %s %s %s"%(pseudo, "200", "200", "right")).encode('utf8'))

        elif state == "menu_main":
            Bouton(fenetre=self, image="play_local.png", command=menu_local, coords=[700, 570])
            Bouton(fenetre=self, image="play_multiplayer.png", command=menu_multiplayer, coords=[700, 720])
            Bouton(fenetre=self, image="quit.png", command=quit, coords=[480, 800])
            self.menu_title = "MENU PRINCIPAL"
            self.menu_title_display = self.font.render(self.menu_title, 0, (255, 255, 255))

        elif state == "menu_local":
            TextZone(fenetre=self, coords=[750, 650], text_lenght=12)
            Bouton(fenetre=self, image="confirm.png", command=confirm, coords=[1310, 800])
            Bouton(fenetre=self, image="cancel.png", command=cancel, coords=[480, 800])
            self.menu_title = "JOUEUR "+str(sub_menu+1)
            if sub_menu == 0:
                self.menu_title_display = self.font.render(self.menu_title, 0, (0, 0, 255))
            elif sub_menu == 1:
                self.menu_title_display = self.font.render(self.menu_title, 0, (255, 0, 0))

        elif state == "menu_multiplayer":
            TextZone(fenetre=self, coords=[750, 650], text_lenght=12)
            Bouton(fenetre=self, image="confirm.png", command=confirm, coords=[1310, 800])
            self.menu_title = "PSEUDO"
            self.menu_title_display = self.font.render(self.menu_title, 0, (255, 255, 255))

        elif state == "menu_end_local":
            Bouton(fenetre=self, image="replay.png", command=replay_local, coords=[700, 600])
            Bouton(fenetre=self, image="stop.png", command=stop, coords=[700, 750])
            if sub_menu == 1:
                self.menu_title = self.local_name_1+" A GAGNE !"
                self.menu_title_display = self.font.render(self.menu_title, 0, (0, 0, 255))
            elif sub_menu == 2:
                self.menu_title = self.local_name_2 + " A GAGNE !"
                self.menu_title_display = self.font.render(self.menu_title, 0, (255, 0, 0))

    def check_buttons(self):
        for bouton in self.boutons:
            bouton.check_mouse()

    def get_text_input(self):
        return self.textbox.get_input()

    def set_local_names(self, name1: str, name2: str):
        self.local_name_1 = name1
        self.local_name_2 = name2


class Joueur(object):
    """********** Objet définissant un personnage *********"""

    def __init__(self, fenetre: GameWindow, texture: str, pseudo="anonyme", coords=[0, 0]):
        self.fenetre = fenetre  # fenetre : Fenêtre pygame associée au joueur
        # Ajout du joueur dans la liste des objets à rendre de la fenêtre
        self.fenetre.joueurs.append(self)

        self.pseudo = pseudo    # pseudo : Nom du joueur
        self.font = pygame.font.Font("LCD_Solid.ttf", 24)   # font : Police d'écriture du pseudo
        self.pseudo_display = self.font.render(self.pseudo, 0, (255, 255, 255)).convert()
        self.pseudo_display.set_alpha(150)  # pseudo_display : Rendu du pseudo avec la police "font"

        self.tank_sprites = SpriteSheet(texture, 4, 4, 4)   # tank_sprites : Objet SpriteSheet contenant tous les sprites du tank
        self.tank_display = self.tank_sprites.getSprite()   # tank_display : Image à afficher lors du prochain rendu

        self.animation_state = -1   # animation_state : Variable définissant l'animation en cours (de 0 à 3 pour droite, gauche, haut et bas)
        self.animation_counter = 0  # animation_counter : Variable définissant le stade le l'animation, de 0 à 3 (chaque animation a 4 sprites)

        self.coords = coords    # coords : Liste [x, y] des coordonnées du joueur sur la fenêtre
        self.direction = "right"    # direction : Variable donnant l'orientation du joueur
        self.movement = [0, 0]
        self.collision = Rect((self.coords[0]+8, self.coords[1]+8), (112, 112))
        self.is_colliding = False   # is_colliding : Si le joueur rentre en collision avec un obstacle ou un joueur

        self.has_shot = False   # has_shot : Booléen permettant de vérifier si le joueur a déjà tiré
        self.invulnerable = False   # invulnerable : Booléen définissant si le joueur est invulnérable
        self.invulnerability_counter = 0    # invulnerability_counter : Compteur de frames d'invincibilité

        self.life_display = life_sprites.getSprite(3)  # life_display : Image de vie à afficher au prochain rendu
        self.life = 3   # life : Vie du joueur, de 3 à 0

    # Méthode permettant de déplacer le joueur, avec gestion de l'animation
    def move(self, direction):
        self.direction = direction
        # Gestion du déplacement
        if direction == "right":
            self.movement = [4, 0]
            self.animation_state = 0
        elif direction == "left":
            self.movement = [-4, 0]
            self.animation_state = 1
        elif direction == "up":
            self.movement = [0, -4]
            self.animation_state = 2
        elif direction == "down":
            self.movement = [0, 4]
            self.animation_state = 3

        for joueur in self.fenetre.joueurs:
            if self.collision.move(self.movement).colliderect(joueur.collision) and joueur != self:
                self.is_colliding = True
        for obstacle in fenetre.obstacles:
            if self.collision.move(self.movement).colliderect(obstacle.collision):
                self.is_colliding = True
        if not self.is_colliding and self.coords[0]+self.movement[0] in range(0, 1792) and self.coords[1]+self.movement[1] in range(0, 952):
            self.coords = list(map(add, self.coords, self.movement))
            self.collision = self.collision.move(self.movement)

        self.is_colliding = False

        # Gestion de l'animation
        if self.animation_counter < 3:
            self.animation_counter += 1
        else:
            self.animation_counter = 0
        self.tank_display = self.tank_sprites.getSprite(self.animation_counter, self.animation_state)

    # Méthode permettant au joueur de tirer un missile
    def shoot(self):
        if not self.has_shot:
            self.has_shot = True
            Missile(fenetre=self.fenetre, owner=self)

    # Méthode à appeler quand le joueur se fait toucher
    def get_hit(self):
        if not self.invulnerable and self.life > 0:
            self.invulnerable = True
            self.invulnerability_counter = 60
            self.life -= 1
            self.life_display = life_sprites.getSprite(self.life)

    # Méthode permettant de changer le nombre de vies du joueur
    def set_life(self, life: int):
        if life < 4 and life >= 0:
            self.life = life
            self.life_display = life_sprites.getSprite(self.life)
        else:
            print("life must be between 0 and 3")

    # Méthode permettant de changer les coordonées du joueur
    def tp(self, coords):
        self.coords = coords

    def get_name(self):
        return self.pseudo


class Missile(object):
    """********** Objet définissant un missile **********"""

    def __init__(self, fenetre: GameWindow,  owner: Joueur, speed=16):
        self.owner = owner  # owner : Joueur ayant tiré le missile
        self.direction = owner.direction    # direction : sens de déplacement du missile
        self.image = Image.open("bullet.png").resize((32, 32))
        self.image = image_convert(self.image).convert_alpha()
        self.coords = [owner.coords[0]+48, owner.coords[1]+48]  # coords : Coordonnées [x, y] du missile
        self.collision = self.image.get_rect().move(self.coords)  # collision : Rectangle (hitbox) permettant de gérer les collisions
        self.fenetre = fenetre
        if self.direction == "right":
            self.coords[0] += 56
        elif self.direction == "left":
            self.coords[0] -= 56
        elif self.direction == "up":
            self.coords[1] -= 56
        elif self.direction == "down":
            self.coords[1] += 56
        self.speed = speed  # speed : Vitesse (pixel/frame) du missile
        self.fenetre.missiles.append(self)

    # Méthode permettant de déplacer le missile
    def move(self):
        if self.coords[0] > 1920 or self.coords[1] > 1080 or self.coords[0] < 0 or self.coords[1] < 0:
            self.owner.has_shot = False
            self.fenetre.missiles.remove(self)
        if self.direction == "right":
            self.coords[0] += self.speed
            self.collision = self.collision.move(self.speed, 0)
        elif self.direction == "left":
            self.coords[0] -= self.speed
            self.collision = self.collision.move(-self.speed, 0)
        elif self.direction == "up":
            self.coords[1] -= self.speed
            self.collision = self.collision.move(0, -self.speed)
        else:
            self.coords[1] += self.speed
            self.collision = self.collision.move(0, self.speed)

        for obstacle in self.fenetre.obstacles:
            if self.collision.colliderect(obstacle.collision):
                self.fenetre.missiles.remove(self)
                self.owner.has_shot = False

        for joueur in self.fenetre.joueurs:
            if self.collision.colliderect(joueur.collision) and joueur != self.owner:
                joueur.get_hit()
                self.owner.has_shot = False
                self.fenetre.missiles.remove(self)


class Obstacle(object):
    """********** Objet définissant un obstacle **********"""

    def __init__(self, fenetre: GameWindow, x: int, y: int, size: int, texture="obstacle.png"):
        fenetre.obstacles.append(self)
        self.image = Image.open(texture).resize((size, size))
        self.image = image_convert(self.image).convert()
        self.collision = Rect(x, y, size, size)


class Bouton(object):
    """********** Objet définissant un bouton **********"""

    def __init__(self, fenetre: GameWindow, image: str, command, coords=[0, 0]):
        self.fenetre = fenetre
        self.fenetre.boutons.append(self)
        self.sprites = SpriteSheet(image, 1, 3, 4)
        self.display = self.sprites.getSprite()
        self.collision = self.display.get_rect().move(coords)
        self.coords = coords
        self.command = command

    def check_mouse(self):
        if self.collision.collidepoint(pygame.mouse.get_pos()):
            if pygame.mouse.get_pressed()[0] and not mouse_pressed:
                self.display = self.sprites.getSprite(0, 2)
                self.command()
            else:
                self.display = self.sprites.getSprite(0, 1)
        else:
            self.display = self.sprites.getSprite()


class TextZone(object):
    """********** Objet définissant une zone pour demander du texte **********"""

    def __init__(self, fenetre, coords=[0, 0], text_lenght=255):
        self.fenetre = fenetre
        self.fenetre.textbox = self
        self.coords = coords
        self.text_length = text_lenght
        self.font = pygame.font.Font("LCD_Solid.ttf", 54)
        self.background_rect = Rect(list(map(add, self.coords, [-10, -10])), list(map(add, self.font.size((self.text_length+1)*"_"), [20, 20])))
        self.text = ""
        self.text_display = self.font.render(self.text, 0, (255, 255, 255))
        self.activated = False
        self.update_start_time = 0
        self._disp = ''

    def get_input(self):
        global mouse_pressed
        self.text = ""
        self.text_display = self.font.render("_", 0, (255, 255, 255))
        self.fenetre.render()
        self.activated = True
        while self.activated:
            self.update()
            keys = pygame.key.get_pressed()
            if keys[K_ESCAPE]:
                self.activated = False
            mouse_pressed = pygame.mouse.get_pressed()[0]
        self.text_display = self.font.render("", 0, (255, 255, 255))
        fenetre.render()
        return self.text

    def update(self):
        if time.time() - self.update_start_time > .2:
            self.update_start_time = time.time()
            if self._disp == "_":
                self._disp = ""
            else:
                self._disp = "_"
        event = pygame.event.poll()
        if event.type == KEYDOWN:
            if event.key == K_BACKSPACE:
                self.text = self.text[0: -1]
            elif event.key == K_RETURN and self.text != "":
                confirm()
            elif len(self.text) < self.text_length and event.unicode in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
                self.text += event.unicode
        self.text_display = self.font.render(self.text+self._disp, 0, (255, 255, 255))
        self.fenetre.check_buttons()
        self.fenetre.render()

########## CREATION FENETRE ##########
fenetre = GameWindow(name="Jeu", width=1920, height=1080, background="background.png")
fenetre.set_state("menu_main")


######### THREAD DE RÉCEPTION MESSAGES #########
def recepteurMessageThread():
    while True:
        # Attente du message du serveur
        msgServeur = mySocket.recv(8192)
        msgServeur = msgServeur.decode('utf8').split(" ")

        if msgServeur[0] == "place":
            print("message place reçu")

            # On crée une liste des pseudos actuels
            pseudos = []
            for client in clients :
                pseudos.append(client.get_name())

            # Si le pseudo n'éxiste pas, on instancie le client
            if msgServeur[1] not in pseudos:
                print('Création d un nouveau joueur')
                clients.append(
                    Joueur(
                        fenetre=fenetre,
                        texture="tank.png",
                        pseudo=msgServeur[1],
                        coords=[ int(msgServeur[2]) , int(msgServeur[3]) ]
                    )
                )
                print("coucou")

            # Si il éxiste, on met à jour ses coordonnées
            else:
                print('Mise à jour d un client')
                # On récupère le numéro du joueur
                index = pseudos.index(msgServeur[1])

                # On met à jour les coordonnées
                clients[index].tp([ int(msgServeur[2]),int(msgServeur[3]) ])

                # Il définit le sens
                # client[index].set_animation_state(msgServeur[4])

        print(msgServeur)
        time.sleep(1/60)

    # _thread.start_new_thread(recepteurMessageThread, ())


########## CONSTANTES ###########
# Adresse IP à définir
HOST = '127.0.0.1'
# Port à modifier sur tous les ordinateurs si l'un est indisponible
PORT = 32000
logo = Image.open("logo.png").resize((1024, 512))
logo = image_convert(logo).convert_alpha()  # logo : Logo du jeu
explosion = SpriteSheet("explosion.png", 4, 1, 4)   # explosion : SpriteSheet pour l'animation d'explosion
life_sprites = SpriteSheet("life.png", 4, 1, 4, 150)    # life : SpriteSheet pour l'affichage de la vie des joueurs
menu_image = Image.open("menu.png").resize((1024, 512))
menu_image = image_convert(menu_image).convert_alpha()  # menu_image : Image de fond des menus


i = 0   # i : Compteur
running = True  # running : Si le programme doit continuer

########## BOUCLE PRINCIPALE ##########
while running:
    frame_start_time = time.time()  # frame_start_time : Temps de début de l'image

    events = pygame.event.get()

    keys = pygame.key.get_pressed() # keys : Touches appuyées
    # Si on appuie sur Echap, le jeu se quitte
    if keys[K_ESCAPE]:
        running = False

    if fenetre.state == "menu_main" or fenetre.state == "menu_end_local":
        fenetre.check_buttons()

    elif fenetre.state == "menu_local":
        if fenetre.sub_menu == 0:
            pseudo1 = fenetre.get_text_input()
        elif fenetre.sub_menu == 1:
            pseudo2 = fenetre.get_text_input()
        elif fenetre.sub_menu == 2:
            fenetre.set_local_names(pseudo1, pseudo2)
            fenetre.set_state("game_local")
            load_level("level.txt")

    elif fenetre.state == "game_local":
        # Réceptionnaire d'événements pour le jeu local
        if keys[K_RETURN]:
            J1.shoot()
        if keys[K_RIGHT]:
            J1.move("right")
        elif keys[K_LEFT]:
            J1.move("left")
        elif keys[K_UP]:
            J1.move("up")
        elif keys[K_DOWN]:
            J1.move("down")

        if keys[K_SPACE]:
            J2.shoot()
        if keys[K_d]:
            J2.move("right")
        elif keys[K_a]:
            J2.move("left")
        elif keys[K_w]:
            J2.move("up")
        elif keys[K_s]:
            J2.move("down")

        # Déplacement des missiles
        for missile in fenetre.missiles:
            missile.move()

        # Tests de fin de jeu
        if J1.life == 0:
            i += 1
            if i > 30:
                fenetre.set_state("menu_end_local", 2)
                i = 0
        elif J2.life == 0:
            i += 1
            if i > 30:
                fenetre.set_state("menu_end_local", 1)
                i = 0

    elif fenetre.state == "menu_multiplayer":
        pseudo = fenetre.get_text_input()
        fenetre.set_state("game_multiplayer")

    elif fenetre.state == "game_multiplayer":
        # Réceptionnaire d'événements pour le jeu multijoueur
        if keys[K_RETURN]:
            pass
        if keys[K_RIGHT]:
            mySocket.send(("place %s %s %s %s"%(pseudo, "150", "150", "left")).encode('utf8'))
        elif keys[K_LEFT]:
            mySocket.send(("place %s %s %s %s" % (pseudo, "300", "150", "left")).encode('utf8'))
        elif keys[K_UP]:
            mySocket.send(("place %s %s %s %s" % (pseudo, "400", "150", "left")).encode('utf8'))
        elif keys[K_DOWN]:
            mySocket.send(("place %s %s %s %s" % (pseudo, "350", "150", "left")).encode('utf8'))

        # Déplacement des missiles
        for missile in fenetre.missiles:
            missile.move()

    mouse_pressed = pygame.mouse.get_pressed()[0]   # mouse_pressed : Si le clic gauche est appuyé
    # Rendu de la fenêtre
    fenetre.render()

    # Délai limitant le jeu à 30FPS
    frame_end_time = time.time()
    if frame_end_time-frame_start_time < 1/30:
        time.sleep(1/30-(frame_end_time-frame_start_time))

pygame.quit()
