#!/bin/bash
# Remplace /home/sara par TON dossier personnel (pour que les textures s'affichent)
cd "$(dirname "$0")"
grep -rl "/home/sara" worlds models launch 2>/dev/null | xargs -r sed -i "s|/home/sara|$HOME|g"
echo "Chemins corriges pour : $HOME"
