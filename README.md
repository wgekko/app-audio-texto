# app-audio-texto
app que transcribe audio a texto

nos encontramos con varias posibilidades de uso 
1- app transcribe audio a texto desarrollado con  libreria tkinter
accion muy basica de escuchar audio y transcribe a texto 
para ejecutar se escribre en la terminal - python audio-tkinter.py

2- app transcibre audio a texto con steamlit 
aqui tenemos librerias mas complejas que entran en juego 
se puede subir un audio pre grabado (formato mp3-wav-ogg) 
se trasncribe y se puede desacargar en formato txt
otra opcion es grabar un audio en tiempo real 
(al app detecta los dispositivos habilitados despliegua 
una lista de ellos para elegir uno y grabar) y una vez
que tiene el audio lo transcribe, despliega un text area
para dar la posiblidad de modificar el texto y una vez 
modificado o no, se puede descargar tanto el texto como 
el audio (se usa libreria whisper-nivel medio
- para mejor precision en la transcipción )


3- app que mantiene las funcionalidades de la app anteior 
y ademas de agrega la posibilidad de volver a grabar otro
audio y trascribirlo a texto, esto abre la posibilidad
de hacer un historial de audio grabados y luego modificar o 
no el texto y descargarlo



4- app que mantiene las mejora de la app anterior 
pero ahora agrega la posibilidad de descargar todos
los audios y archivos de texto y crear un carpeta con formato 
zip. Y luego de hacer
 ese proceso habilita a enviar los archivos
por mail

video primer app 

https://github.com/user-attachments/assets/9aad3f97-a45b-4a2e-9c86-bd63cff0aa05


video de app mas completa 



https://github.com/user-attachments/assets/63803b35-b187-4a12-ae90-0353e7d8284c






