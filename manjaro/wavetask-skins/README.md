# Skins de Wave Task estilo macOS

Rectángulo redondeado translúcido (radio 16 px) que envuelve los iconos, en
variante clara y oscura. `tasks.svgz` procede del skin Tahoe de Wave Task (GPL-3.0).
Los PNG se generan con ImageMagick:

    magick -size 64x64 xc:none -fill 'rgba(246,246,246,0.62)' -stroke 'rgba(255,255,255,0.55)' \
      -strokewidth 1 -draw "roundrectangle 0.5,0.5 63.5,63.5 16,16" bg.png      # claro
    magick -size 64x64 xc:none -fill 'rgba(36,36,38,0.60)' -stroke 'rgba(255,255,255,0.16)' \
      -strokewidth 1 -draw "roundrectangle 0.5,0.5 63.5,63.5 16,16" bg.png      # oscuro

Wave Task solo busca skins junto a su paquete; desktop.py los copia a
~/.local/share/macos-setup/wavetask-skins y los referencia con una ruta relativa.
`outsideTopMargin: -5` sube el fondo para que cubra los iconos de 44 px en un
panel de 86 px (el skin se coloca con «altura del panel − 76»).
