# Minitel Image Viewer

![Screenshot](https://github.com/pR-0000/Minitel-image-viewer/blob/main/GUI.png?raw=true)

*Minitel Image Viewer* is a Python app with a graphical interface that converts an image into the Minitel’s G1 mosaic character set and sends it to the terminal over serial. The image is prepared at **80×72 pixels** (2×3 pixel tiles per character, 40×24 chars) using the **fixed 8-color Minitel palette**, then encoded with efficient RLE.

## Features

* **Accurate Minitel conversion**

  * Fixed **8-color palette** (RGB → indexed palette), optional **Floyd–Steinberg dithering**.
  * G1 mosaic encoding (2×3 pixels per character) with **run-length repeats (DC2)**.
  * Correct handling of “empty” blocks using **mosaic space (0x20)** so background color is actually rendered.
* **Resizing modes**

  * **Stretch (fill screen)**: fills 80×72 (can distort).
  * **Crop and center**: preserves aspect ratio and pads with a chosen background color.
* **Preview** in Color or Grayscale.
* **Serial send** with logging (payload size & rough ETA), non-blocking UI.
* **Port management**: list & **Refresh** available COM ports.
* **Init sequence included** (on send & on export): disables local echo, hides cursor, clears screen, **clears line 0**, selects G1.
* **Export to .vdt** (Videotex stream)

  * Saves exactly what is sent to the terminal (init + image payload).
  * Optional **STX/ETX** wrapping for players that expect it.
* **Manual serial format** preserved

  * Keep using your preferred 7E1/8N1 settings manually; speed auto-detection does **not** force a parity/data-bits change.

## What’s new (since early versions)

* Added **.vdt export** (replaces the older raw .bin export).
* Dithering toggle, **Refresh ports** button.
* More robust color handling after cursor moves; preservation of **line-0 clearing**.
* Faster encoder (precompiled tables, bytearray assembly, palette indices).
* Better logs (size + estimated time).

## Requirements

* **Python 3.8+** (the app auto-installs required libraries if missing).
* Dependencies: **Pillow**, **pyserial** (installed automatically at first run).

## Usage

1. Connect your Minitel with a RS232/USB adapter.
2. Launch:

   ```bash
   python "minitel_image_viewer.pyw"
   ```
3. **Select file** and choose a **Resizing mode**:

   * *Stretch* or *Crop and center* (pick a background color for centering).
4. Toggle **Dithering** (on/off). For clean flats, turn it off.
5. Choose **Preview mode** (Color/Grayscale).
6. Pick the **COM port** (use **Refresh** if needed).
7. Set **baud rate**; adjust **7/8 data bits**, **parity**, **stop bits** if required by your setup.
8. Click **Send image to Minitel**.

   * The app sends an **init sequence**: disable echo, hide cursor, **clear screen**, **clear line 0**, select **G1**, then the encoded image.
9. (Optional) Click **Export .vdt (Videotex)** to save the exact serial stream

   * Tick **Add STX/ETX** if your viewer/player expects a framed stream.

## Notes on the encoder

* The converter works in **palette mode (“P”)** for speed and fidelity.
* “Empty” blocks (all background) are printed with **mosaic space (0x20)** after setting **PAPER** (background color), so every cell really takes color (no black holes).
* Repeats use **DC2 (0x12)** with a max chunk of 63; long runs are chunked automatically.
* Cursor jumps are handled carefully; after any jump the encoder re-emits **PAPER/INK** before drawing.

## Troubleshooting

* If you see unexpected black cells in large flats, ensure you’re using the latest version (empty-run handling was fixed).
* Verify the selected COM port isn’t used by another app.
* If your model is picky about serial format, set **7E1/8N1** manually in the GUI (speed auto-detect won’t change it).
* Disable dithering to debug color blocks more easily.

---

# Minitel Image Viewer

![Screenshot](https://github.com/pR-0000/Minitel-image-viewer/blob/main/GUI.png?raw=true)

*Minitel Image Viewer* est une application Python avec interface graphique qui convertit une image vers le jeu de caractères mosaïque **G1** du Minitel et l’envoie au terminal via la liaison série. L’image est préparée en **80×72 px** (tuiles 2×3 par caractère, 40×24 caractères) avec la **palette Minitel 8 couleurs**, puis encodée avec RLE.

## Fonctionnalités

* **Conversion fidèle Minitel**

  * Palette fixe **8 couleurs**, **tramage Floyd–Steinberg** optionnel.
  * Encodage mosaïque G1 (2×3 px) avec **répétitions RLE (DC2)**.
  * Gestion correcte des blocs « vides » via **espace mosaïque (0x20)** pour appliquer réellement la couleur de fond.
* **Modes de redimensionnement**

  * **Stretch (fill screen)** : remplit 80×72 (peut déformer).
  * **Crop and center** : conserve le ratio et ajoute des bandes de la couleur de fond choisie.
* **Prévisualisation** en couleur ou niveaux de gris.
* **Envoi série** avec journal (taille + estimation de durée), UI non bloquante.
* **Gestion des ports** : liste & **Rafraîchir** les ports disponibles.
* **Séquence d’initialisation** incluse (à l’envoi et à l’export) : désactive l’écho local, masque le curseur, efface l’écran, **efface la ligne 0**, sélectionne G1.
* **Export .vdt** (flux Videotex)

  * Sauvegarde **exactement** ce qui est envoyé au terminal (init + image).
  * Option **STX/ETX** pour les lecteurs qui l’exigent.
* **Réglages manuels série** conservés

  * Le choix **7E1/8N1** reste manuel ; l’auto-détection de vitesse ne force pas de changement de parité/bits.

## Nouveautés (depuis les premières versions)

* Export **.vdt** (remplace l’ancien .bin brut).
* Case **Dithering**, bouton **Rafraîchir** les ports.
* Rendu couleur robuste après déplacements de curseur ; **effacement de la ligne 0** conservé.
* Encodeur plus rapide (tables précompilées, `bytearray`, indices palette).
* Journaux plus informatifs (taille + estimation).

## Exigences

* **Python 3.8+** (les dépendances **Pillow** et **pyserial** sont installées automatiquement au premier lancement).

## Utilisation

1. Reliez le Minitel via un adaptateur RS232/USB.
2. Lancez :

   ```bash
   python "minitel_image_viewer.pyw"
   ```
3. **Select file** : choisissez une image.
4. Sélectionnez un **mode de redimensionnement** (Stretch ou Crop and center) et la **couleur de fond** si nécessaire.
5. Activez/désactivez le **Dithering**.
6. Choisissez le **mode de prévisualisation** (Color/Grayscale).
7. Sélectionnez le **port COM** (bouton **Refresh** si besoin).
8. Réglez le **débit** et, si nécessaire, **7/8 bits**, **parité**, **bits de stop**.
9. Cliquez sur **Send image to Minitel**.

   * L’application envoie d’abord une **séquence d’init** : désactivation de l’écho, masquage du curseur, **clear screen**, **clear ligne 0**, sélection **G1**, puis l’image encodée.
10. (Optionnel) Cliquez sur **Export .vdt (Videotex)** pour sauvegarder le flux exact

    * Cochez **Ajouter STX/ETX** si votre lecteur attend un flux encadré.

## Notes sur l’encodeur

* Conversion en **mode palette (“P”)** pour rapidité et fidélité.
* Les blocs « vides » sont imprimés avec **0x20** après réglage du **PAPER** (couleur de fond) : chaque cellule reçoit bien sa couleur (pas de “trous” noirs).
* Répétitions via **DC2 (0x12)** (paquets ≤63, segmentés au-delà).
* Après un saut de curseur, **PAPER/INK** sont ré-émis avant de tracer.

## Dépannage

* Si vous constatez des cellules noires dans de grands aplats, mettez à jour vers la dernière version (gestion des blocs vides corrigée).
* Vérifiez que le bon port COM est sélectionné et qu’il n’est pas utilisé ailleurs.
* Certains modèles exigent un format série particulier : ajustez **7E1/8N1** manuellement dans l’interface.
* Désactivez le tramage pour faciliter le diagnostic des aplats/couleurs.
