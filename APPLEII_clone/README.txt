APPLEII_clone

Ce projet consiste a 'recreer' un APPLE][ a partir d'un kit 65C02 base
sur la serie Youtube de Ben Eater
Le PCB d'origne possede un PIA qui ne sera pas utilise.
Le mapping memoire sur le kit d'origine est base sur un 74HC00 qui defini
les plage suivante
  0000..3FFF RAM
  4000..7FFF Periph (avec ram en ghost)
  8000..FFFF PROM
Le nouveau mappage des adresses reprendra celui de APPLE][ et sera 
realise pr un circuit externe base sur un GAL16V8
  0000..3FFF RAM residente sur la carte
  4000..BFFF RAM externe
  C000..CFFF periperiques
  D000..FFFF PROM
  
E/S clavier et ecran
Cette fonction sera realise par un arduino nano couple a un MC68A22.
D'origine les sortie ecran sont realisees par le systeme video de 
l'APPLE ][ en utilisant les plage 400..7FF et 800..CFF
l'implementation presente ajoute un interface serie tty.
les adresses d'acces de ce peripherique sont
C000	keyboard data    (d'origine sur APPLE ][)
C010    keyboard strobe  (idem...)
C001	disp date	 (adresse non utilise APPLE ][)
C011	disp ready       (idem...)
les elements consistutif de cette fonction sont rassemble dans le
repertoire PIA68A22
 
