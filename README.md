# Robot d'inspection autonome après un séisme (simulation)

Projet de fin d'études : un robot **TurtleBot3** explore un bâtiment endommagé
dans **Gazebo**, construit une carte, et doit ensuite faire une ronde le long des
murs en prenant des photos. Ces photos servent à détecter les fissures avec une IA
(partie des coéquipiers B et C).

## Où en est le projet ?

**Ça marche :**
- Un monde de simulation : murs, fissures, débris, dalle effondrée, colonnes, textures
- Le robot TurtleBot3 *waffle* avec laser et caméra
- Une carte du bâtiment faite avec SLAM Toolbox (en conduisant à la main)
- Nav2 : le robot est allé tout seul vers un point choisi dans RViz

**Pas encore fini / pas testé :**
- `patrol.py` (ronde + photos automatiques) n'a **jamais été lancé avec succès** : il est écrit mais non testé
- Il faut redonner la position du robot à Nav2 à chaque lancement (c'est pénible, voir plus bas)
- Il faut plus de variété de dégâts (fissures sur tous les murs, plus de gravats)
- Les photos pour l'IA ne sont pas encore prises

## Outils utilisés

| Outil | Rôle |
|---|---|
| Ubuntu 22.04 (WSL2 sous Windows) | Le système où tout tourne |
| ROS 2 Humble | Le "système nerveux" du robot (les programmes se parlent par des topics) |
| Gazebo 11 | Le simulateur (le monde et le robot) |
| SLAM Toolbox | Construit la carte pendant que le robot roule |
| Nav2 | Fait rouler le robot tout seul sur la carte |
| RViz2 | Affiche la carte, le laser et le chemin |
| TurtleBot3 waffle | Le robot (le modèle *waffle* a une caméra) |

## Installation

1. Installer ROS 2 Humble sur Ubuntu 22.04, puis les paquets :
```
sudo apt install ros-humble-desktop ros-humble-gazebo-ros-pkgs \
  ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-slam-toolbox ros-humble-turtlebot3*
```
2. Copier le projet **dans `~/earthquake_ws`** (les scripts utilisent ce chemin) :
```
git clone https://github.com/SiriusRalph/earthquake-inspection-robot.git ~/earthquake_ws
```
3. Corriger les chemins des textures pour TON ordinateur :
```
cd ~/earthquake_ws
./setup_paths.sh
```

## Lancer la simulation

Chaque commande va dans un **terminal Ubuntu différent**.

**Terminal 1 : Gazebo (le monde et le robot)**
```
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
ros2 launch ~/earthquake_ws/launch/damaged_building.launch.py
```

**Terminal 2 : Nav2 avec la carte** (RViz s'ouvre tout seul)
```
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle
export LIBGL_ALWAYS_SOFTWARE=1
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=true map:=$HOME/earthquake_ws/damaged_building_map_filled.yaml
```
Attendre ~15 secondes, puis dans RViz : bouton **2D Pose Estimate**, cliquer où est le
robot (regarder Gazebo) et glisser dans la direction où il regarde. Les points du laser
doivent tomber sur les murs. Le panneau doit afficher `Localization: active`.

**Terminal 3 : la ronde avec photos** (pas encore testé)
```
source /opt/ros/humble/setup.bash
python3 ~/earthquake_ws/patrol.py
```
Les photos sont enregistrées dans `photos/run_.../` (ce dossier n'est pas sur GitHub).

## Refaire la carte (si on change le monde)

1. Lancer Gazebo (terminal 1), puis SLAM : `ros2 launch slam_toolbox online_async_launch.py use_sim_time:=true`
2. Ouvrir RViz (`rviz2`) et conduire le robot avec `ros2 run turtlebot3_teleop teleop_keyboard`
   (avancer, `s` pour arrêter, tourner, `s`... doucement)
3. Sauvegarder : `ros2 run nav2_map_server map_saver_cli -f ~/earthquake_ws/damaged_building_map`
4. Remplir les "trous" inconnus à l'intérieur de la pièce : `python3 fill_map.py`
   (puis copier le `.yaml` en changeant le nom de l'image, voir `damaged_building_map_filled.yaml`)
5. Recalculer les points de la ronde : `python3 make_waypoints.py`

## Les fichiers

| Fichier / dossier | À quoi ça sert |
|---|---|
| `worlds/damaged_building.world` | Le bâtiment endommagé (murs, fissures, débris, dalle, colonnes) |
| `launch/damaged_building.launch.py` | Lance Gazebo avec notre monde et le robot |
| `models/damaged_textures/` | Les textures (stuc, sol) |
| `damaged_building_map_filled.pgm/.yaml` | La carte utilisée par Nav2 (trous remplis) |
| `damaged_building_map.pgm/.yaml` | La carte brute de SLAM (sauvegarde) |
| `fill_map.py` | Remplit les zones inconnues à l'intérieur de la pièce |
| `make_waypoints.py` | Trouve les murs sur la carte et choisit 4 points de ronde (`waypoints.txt`) |
| `patrol.py` | Envoie le robot à chaque point à travers Nav2 et prend une photo |

## Problèmes connus (et pourquoi)

- **La carte avait des zones "inconnues" au milieu** : le laser ne voit qu'à environ 3,5 m
  et ne marque le sol libre que le long de ses rayons. Solution : `fill_map.py`.
- **RViz plante parfois sous WSL** : lancer avec `export LIBGL_ALWAYS_SOFTWARE=1`,
  ne pas cliquer pendant les 15 premières secondes, fermer les autres programmes lourds.
- **Nav2 dit `aborted`** : en général le but est dans une zone de sécurité (halo coloré)
  ou le robot est mal placé. Choisir un but en zone blanche, loin des obstacles.
- **Nav2 n'est plus là** (`NavigateToPose action server not available`) : le terminal de
  Nav2 a été fermé. Le relancer, puis refaire la pose initiale.
- **Textures blanches** : on a oublié `./setup_paths.sh`.

## Pour les coéquipiers

- Les photos viennent du topic `/camera/image_raw` (robot waffle).
- Pour voir la caméra : `ros2 run rqt_image_view rqt_image_view`
- Les dégâts (fissures, gravats, dalle) sont décrits dans `worlds/damaged_building.world`.
  Pour en ajouter, copier un bloc `<model>` et changer sa position (`<pose>`).

## Références (à compléter)

- Article USGS sur les dégâts de séisme : *(titre, lien, date de consultation)*
- Textures : Poly Haven (licence CC0)
- Documentation ROS 2 Humble, Gazebo, Nav2, SLAM Toolbox *(liens + date)*

## Utilisation de l'IA

*(À compléter : dire clairement quelle partie a été faite avec l'aide d'un assistant IA
et ce que l'équipe a compris et vérifié elle-même.)*
