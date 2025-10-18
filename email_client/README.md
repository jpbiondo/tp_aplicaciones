## Email Client

Cliente de correo que implementa las siguientes funcionalidades:
- Reenviar correos
- Responder correos
- Eliminar correos
- Búsqueda de correos por distintos criterios (cuerpo del mail, destinatario, etc).

### Configuración
Para utilizar el este cliente necesitás tu _dirección de correo_ (por ej. la de gmail) y una _contraseña de aplicación_.
Para conseguir tu _contraseña de aplicación_ en gmail tenés que:
1. Activar la [verificación en dos pasos](https://support.google.com/accounts/answer/185839?sjid=8773938299224853416-SA).
2. Crear tu [contraseña de aplicación acá](https://myaccount.google.com/apppasswords). Deberías conseguir una contraseña de esta forma `xxxx xxxx xxxx xxxx`, copiala.

Ahora abrí con un editor de texto el archivo `.env.example` y cambiá `EMAIL_ADDRESS` por tu dirección de correo electrónico y `EMAIL_PASSWORD` por la contraseña de aplicación que obtuviste.
Cambiá el nombre del archivo `.env.example` a `.env`.

Con esto ya podés correr el cliente, probarlo y ver desastre.

### Protocolos utilizados
Las funcionalidades se deben lograr con los protocolos STMP, IMAP y POP3. Python provee librerías estándar para
comunicarse utilizando cualquiera de los protocolos.
#### SMTP
Es un protocolo para enviar los mensajes entre distintos clientes.
![img](https://acf.geeknetic.es/imgri/imagenes/auto/21/09/22/i6w-que-es-smtp-y-para-que-sirve.png?f=webp)
#### POP 3
Protocolo creado con el propósito principal de la lectura de mensajes desde el servidor del correo. Es maleta
para operaciones como eliminar y modificar.
![img](https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ6m4R_1Iz8QZMFquFmlQZNGVj9Oy7aoJrrZw&s)
#### IMAP
Protocolo para la lectura de mensajes desde el servidor de correos. Ofrece una estructura
de carpetas como `INBOX`, `SPAM` y qsy, por este motivo es ideal para realizar búsquedas avanzadas.
Además admite operaciones eliminar y modificar, cada correo tiene su UID.
![img](https://ghost-images.chamaileon.io/2023/02/3.webp)

### TODO
- [ ] Probar si anda todo
- [ ] Cómo integrar POP3?