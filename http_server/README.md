## **Servidor Web Básico con Autenticación**

Este script implementa un servidor web simple en Python capaz de servir archivos estáticos y proteger directorios específicos mediante autenticación Basic.

### **Funcionalidades Principales**

* **Servidor de Archivos Estáticos**: Sirve archivos desde un directorio raíz configurable (DocumentRoot).  
* **Autenticación Basic**: Protege las rutas que comienzan con /private/. El acceso requiere un usuario y contraseña válidos.  
* **Configuración Externa**: Lee los parámetros del servidor (puerto, directorio raíz) y las credenciales desde un archivo config.ini, permitiendo modificar el comportamiento sin alterar el código.  
* **Seguridad**: Incluye una protección básica contra ataques *Path Traversal*, impidiendo el acceso a archivos fuera del DocumentRoot.  
* **Logging**: Registra eventos importantes como el inicio/detención del servidor, archivos servidos, intentos de autenticación (exitosos y fallidos) y errores. Los logs se guardan en server.log y se muestran en la consola.

### **Configuración**

El servidor se configura a través de un archivo config.ini con la siguiente estructura:

\[Server\]  
Port \= 8080  
DocumentRoot \= webroot

\[Credentials\]  
User \= admin  
Password \= secret

* **Port**: El puerto en el que escuchará el servidor.  
* **DocumentRoot**: El directorio desde el cual se servirán los archivos.  
* **User**: El nombre de usuario para acceder a las rutas privadas.  
* **Password**: La contraseña para el usuario.

### **Uso**

1. Asegúrate de tener un archivo config.ini en el mismo directorio que el script.  
2. Ejecuta el script desde la terminal:  
   python nombre\_del\_script.py

3. El servidor se iniciará en http://localhost:8080 (o el puerto que hayas configurado). Si el directorio DocumentRoot no existe, el script lo creará junto con archivos de ejemplo.

### **Estructura del Código**

* **CustomHTTP(BaseHTTPRequestHandler)**: Clase principal que hereda del manejador de peticiones base de Python y sobreescribe sus métodos para personalizar el comportamiento del servidor.  
* **\_autenticar()**: Método interno que gestiona la lógica de autenticación. Verifica las credenciales enviadas en la cabecera Authorization y responde con los códigos de estado 401 (No autorizado) o 403 (Prohibido) si la autenticación falla.  
* **do\_GET()**: Maneja todas las peticiones GET. Determina si la ruta solicitada es pública o privada, llama al método de autenticación si es necesario, construye la ruta del archivo y lo sirve si existe, o devuelve un error 404 (No encontrado) en caso contrario.