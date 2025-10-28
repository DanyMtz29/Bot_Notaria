# ESCTRUCTURA PARA QUE EL BOT NO BATALLE

Carpeta principal donde tiene todos los actos guardados. Por ejemplo:
C:\Users\dani\Actos\

Dentro de la ruta principal ya estarian los distintos actos/proyectos de la siguiente manera:

/NOMBRE_DEL_ACTO
 /PARTES_INVOLUCRADAS
  /COMPRADOR
   /DOCUMENTOS DEL COMPRADOR
   /ESPOSA -> Aplica dependiendo si esta casado
  /VENDEDOR
  /ACREEDOR
  /ADEUDOR
  /...*depende de las partes que apliquen en el acto*
 /DOCUMENTOS GENERALES
  /SOLICITUD_DE_AVALUO.pdf
  /AVALUO.pdf
  /...

Documentos del cliente que empiecen por primerApellido_primerNombre-doc, si es sociedad, nombre de la sociedad como tal
Ejemplo:
/JUAREZ_DANIEL <- Carpeta
 /JUAREZ_DANIEL-CURP.pdf
 /JUAREZ_DANIEL-ACTA-DE-NACIMIENTO.pdf
 /JUAREZ_DANIEL-ACTA-DE-MATRIMONIO.pdf
 /JUAREZ_DANIEL-COMP-DE-DOMICILIO.pdf
 /JUAREZ_DANIEL-CSF.pdf