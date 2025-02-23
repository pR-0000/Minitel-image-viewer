# Minitel Image Viewer

*Minitel Image Viewer* is a Python script with a graphical user interface that converts an image into a mosaic of characters compatible with Minitel terminals. The script resizes the source image to a resolution of 80×72 pixels (suitable for Minitel display) and converts it into character blocks using the Minitel color palette. The converted image can then be sent to the Minitel via a serial connection.

## Features

- **Image Conversion**: Resizes the source image to 80×72 pixels and converts it into Minitel blocks.
- **Resizing Modes**:
  - **Stretch (fill screen)**: The image is stretched to fill the entire resolution (distortion may occur).
  - **Crop and center**: The image is resized while preserving its aspect ratio, then centered on a configurable background.
- **Preview**: Interactive display of the converted image in color or grayscale.
- **Serial Communication**: Sends the converted image to the Minitel terminal via a serial connection.
- **Graphical Interface**: Built with Tkinter for user-friendly operation.

## Requirements
- **Python 3.8+** (the application will install required libraries if they are not present).

## Usage
1. Connect your Minitel to your computer using a compatible RS232/USB adapter.
2. Run the application by double-clicking on `minitel_image_viewer.pyw` or, alternatively, run it via the command line:
   ```bash
   python "minitel_image_viewer.pyw"
   ```
3. Image Selection: Click the "Select file" button to choose an image from your system. The selected file name will be displayed.
4. Resizing Mode: Choose between "Stretch (fill screen)" and "Crop and center" to define the image processing method.
5. Background Color: For the "Crop and center" mode, select the desired background color from the dropdown menu.
6. Preview Mode: Select "Color" or "Grayscale" to view the converted image in color or grayscale.
7. Preview: The converted image (80×72 pixels) is displayed in the preview frame, which has a fixed maximum size to prevent excessive resizing.
8. Configure the serial settings to match your Minitel model.
9. Send Image: Click "Send image to Minitel" to send the converted image to the Minitel terminal via the serial connection.

## Troubleshooting
- Ensure the correct COM port is selected and that no other application is using it.
- For best results, consult your Minitel manual to verify compatibility and settings.

---

# Minitel Image Viewer

*Minitel Image Viewer* est un script Python doté d'une interface graphique qui permet de convertir une image en une mosaïque de caractères compatible avec les terminaux Minitel. Le script redimensionne l'image source à une résolution de 80×72 pixels (adaptée à l'affichage du Minitel) et la convertit en blocs de caractères en utilisant la palette de couleurs du Minitel. Il est ensuite possible d'envoyer cette image convertie au Minitel via une connexion série.

## Fonctionnalités

- **Conversion d'image** : Redimensionnement de l'image source à 80×72 pixels et conversion en blocs Minitel.
- **Modes de redimensionnement** :
  - **Stretch (fill screen)** : L'image est étirée pour remplir toute la résolution (déformation possible).
  - **Crop and center** : L'image est redimensionnée en conservant son ratio d'aspect, puis centrée sur un fond configurable.
- **Prévisualisation** : Affichage interactif de l'image convertie en couleur ou en niveaux de gris.
- **Communication série** : Envoi de l'image convertie au terminal Minitel via une connexion série.
- **Interface graphique** : Conçue avec Tkinter pour une utilisation conviviale.

## Exigences
- **Python 3.8+** (l'application installera les bibliothèques nécessaires si elles ne sont pas présentes).

## Utilisation
1. Connectez votre Minitel à votre ordinateur à l'aide d'un adaptateur RS232/USB compatible.
2. Lancez l'application en double-cliquant sur `minitel_image_viewer.pyw` ou, alternativement, via la ligne de commande :
   ```bash
   python "minitel_image_viewer.pyw"
   ```
3. Sélection d'image : Cliquez sur le bouton "Select file" pour choisir une image sur votre système. Le nom du fichier sélectionné s'affiche.
4. Mode de redimensionnement : Choisissez entre "Stretch (fill screen)" et "Crop and center" pour définir la méthode de traitement de l'image.
5. Couleur de fond : Pour le mode "Crop and center", sélectionnez la couleur de fond souhaitée dans le menu déroulant.
6. Mode de prévisualisation : Sélectionnez "Color" ou "Grayscale" pour voir l'image convertie en couleur ou en niveaux de gris.
7. Prévisualisation : L'image convertie (80×72 pixels) est affichée dans le cadre de prévisualisation, qui dispose d'une taille maximale fixe pour éviter des redimensionnements excessifs.
8. Configurez les paramètres de communication série pour correspondre à votre modèle de Minitel.
9. Envoi de l'image : Cliquez sur "Send image to Minitel" pour envoyer l'image convertie au terminal Minitel via la connexion série.

## Dépannage
- Vérifiez que le bon port COM est sélectionné et qu'aucune autre application ne l'utilise.
- Pour de meilleurs résultats, consultez le manuel de votre Minitel afin de vérifier la compatibilité et les réglages.
