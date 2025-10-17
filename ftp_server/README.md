## **Servidor FTP Básico**

Este script implementa un servidor FTP (Protocolo de Transferencia de Archivos) simple en Python, capaz de manejar múltiples clientes de forma concurrente para realizar operaciones básicas de archivos.

### **Funcionalidades Principales**

* **Gestión de Conexiones Múltiples**: Utiliza hilos (threading) para atender a varios clientes simultáneamente sin que uno bloquee a los otros.  
* **Autenticación de Usuarios**: Requiere que los clientes inicien sesión con un nombre de usuario y contraseña (USER, PASS) antes de poder ejecutar otros comandos. Las credenciales están definidas dentro del código.  
* **Operaciones de Archivos**: Soporta los comandos FTP esenciales:  
  * LIST: Listar los archivos y directorios.  
  * RETR: Descargar un archivo del servidor al cliente.  
  * STOR: Subir un archivo desde el cliente al servidor.  
  * DELE: Eliminar un archivo del servidor.  
* **Navegación de Directorios**: Permite a los clientes ver su directorio actual (PWD) y cambiar a otros subdirectorios (CWD).  
* **Seguridad (Enjaulamiento)**: Restringe el acceso del usuario a un directorio base (ftp\_server\_files) y sus subdirectorios, previniendo ataques de *Path Traversal* que intenten acceder a otras partes del sistema de archivos.

### **Configuración**

A diferencia del servidor web anterior, la configuración de este servidor FTP está definida directamente en el código, dentro del método \_\_init\_\_ de la clase FTPServer:

* **Host y Puerto**: host='127.0.0.1', port=2121  
* **Credenciales**: self.users \= {'user': '12345'}. Para añadir más usuarios o cambiar la contraseña, se debe modificar este diccionario.  
* **Directorio Raíz**: self.base\_dir \= os.path.join(os.getcwd(), "ftp\_server\_files"). Todos los archivos se almacenarán aquí.

### **Uso**

1. Guarda el código en un archivo Python (por ejemplo, ftp\_server.py).  
2. Ejecuta el script desde la terminal:  
   python ftp\_server.py

3. El servidor se iniciará y creará automáticamente la carpeta ftp\_server\_files si no existe. Estará listo para aceptar conexiones en 127.0.0.1:2121.

### **Cómo Conectarse desde CMD (Windows)**

Puedes usar el cliente FTP que viene incorporado en la línea de comandos de Windows para conectarte:

1. Abre una terminal (cmd).  
2. Ejecuta el siguiente comando para conectarte al servidor:  
````
ftp
open 127.0.0.1 2121
````

3. El servidor te pedirá un usuario. Escribe user y presiona Enter.  
4. Luego te pedirá la contraseña. Escribe 12345 y presiona Enter.  
5. Una vez conectado, puedes usar comandos como:  
   * ls: Listar archivos.  
   * get nombre\_del\_archivo.txt: Descargar un archivo.  
   * put C:\\ruta\\a\\tu\\archivo.txt: Subir un archivo.  
   * delete archivo\_a\_borrar.txt: Eliminar un archivo.  
   * quit: Desconectarse del servidor.

> **_NOTA:_**  Los comandos listados difieren con los definidos en el FTP. Esto es porque el cliente FTP estos comandos más simples en los comandos FTP reales.

### **Estructura del Código**

* **FTPServer**: La clase principal que encapsula toda la lógica del servidor.  
* **start()**: Inicia el servidor, lo pone a escuchar en el puerto configurado y acepta nuevas conexiones en un bucle infinito, creando un hilo para cada una.  
* **handle\_client()**: Gestiona el ciclo de vida de la conexión de un único cliente. Recibe, interpreta y responde a los comandos FTP.  
* **\_handle\_LIST(), \_handle\_RETR(), \_handle\_STOR(), \_handle\_DELE()**: Métodos auxiliares que contienen la lógica específica para cada uno de los comandos FTP principales que involucran una conexión de datos.