---
applyTo: '**'
---
Cuando tengas que compilar migraciones, siempre hazlo dentro del entorno Docker, porque este proyecto está trabajando y ejecutándose en Docker, tanto la base de datos como el sistema. Específicamente, cuando debas ejecutar comandos de migrate o de actualización de base de datos.
Nunca debes cambiar a otra base de datos que no sea la que ya se está utilizando, que es PostgreSQL. Por más que haya equivocaciones, nunca intentes pasar a otra tecnología de base de datos, como por ejemplo SQLite. Indícame qué hacer en esos casos.
Espera el tiempo prudente cuando envíes a levantar el Docker, porque puede demorar hasta 300 segundos para continuar con las interacciones de comandos.
Cuando tengas que probar algo y quieras abrir la web y el puerto para explorar, no abras el explorador de contenido simple en VSCode. Mejor consulta con curl en la línea de comandos y envía ahí los parámetros o la URL necesarios para que responda. Es preferible hacerlo tanto para el frontend como para el backend cuando sientas necesidad de verificar si está levantado el sitio o algo así.
Si solo cambias codigo del framework o de backend o apis y nada de infraestructura, no es necesario que vuelvas a reinicializar o iniciar o indiques que levante el Docker. Solo indícame que ejecute el comando que necesites.
Cuando hagas cualquier modificación en el código por favor revisa los logs de los contenedores para verificar si no existe algun problema en lo realizado al menos los 20 últimos, pero utiliza un timer para espera antes de ver de al menos 60 segundos.
No intentes verificar por web ni por comando si una funcion esta activa en vista de que no tienes la posibilidad de interactuar con la web y no vas a saber, en cambio preguntame a mi que yo si veo y si funciona o no funciona la funcionalidad que asumes que deberia valer o no.

