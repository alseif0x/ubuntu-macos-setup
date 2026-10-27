# Skins de Wave Task estilo macOS

Rectángulo redondeado translúcido (radio 16 px) que envuelve los iconos, en
variante clara y oscura. El claro es un gris neutro, no blanco: sin desenfoque
ni sombras en los iconos, un fondo blanco ocultaba los iconos claros (papelera,
Dolphin, ChatGPT) y tomaba el color del fondo de escritorio. `tasks.svgz` procede del skin Tahoe de Wave Task (GPL-3.0).
Los PNG se generan con ImageMagick:

    magick -size 64x64 xc:none -fill 'rgba(95,95,102,0.48)' -stroke 'rgba(255,255,255,0.35)' \
      -strokewidth 1 -draw "roundrectangle 0.5,0.5 63.5,63.5 16,16" bg.png      # claro
    magick -size 64x64 xc:none -fill 'rgba(62,62,68,0.58)' -stroke 'rgba(255,255,255,0.22)' \
      -strokewidth 1 -draw "roundrectangle 0.5,0.5 63.5,63.5 16,16" bg.png      # oscuro

Wave Task solo busca skins junto a su paquete; desktop.py los copia a
~/.local/share/macos-setup/wavetask-skins y los referencia con una ruta relativa.
`outsideTopMargin: -5` sube el fondo para que cubra los iconos de 44 px en un
panel de 86 px (el skin se coloca con «altura del panel − 76»).
