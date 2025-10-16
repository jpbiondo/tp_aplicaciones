import pika
import json
import threading
import logging
import os
import time
from datetime import datetime
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_client.log'),
        logging.StreamHandler()
    ]
)


class ChatClient:
    def __init__(self, username, host='localhost'):
        self.username = username
        self.host = host
        self.connection = None
        self.channel = None
        self.current_channel = 'general'
        self.channels = []
        self.subscribed_channels = set()
        self.profile = {
            'name': username,
            'bio': '',
            'status': 'online'
        }

        # Crear directorios
        Path('client_files').mkdir(exist_ok=True)
        Path('client_conversations').mkdir(exist_ok=True)

        self.running = True
        self.listener_thread = None
        logging.info(f"Cliente iniciado para usuario: {username}")

    def connect(self):
        """Conectar al servidor AMQP"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.host,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )
            )
            self.channel = self.connection.channel()

            # Declarar exchange
            self.channel.exchange_declare(
                exchange='chat_exchange',
                exchange_type='topic',
                durable=True
            )

            logging.info(f"Conectado a RabbitMQ en {self.host}")
            return True
        except Exception as e:
            logging.error(f"Error al conectar: {e}")
            print(f"\n❌ Error: No se pudo conectar al servidor RabbitMQ")
            print(f"Asegúrate de que RabbitMQ esté corriendo en {self.host}")
            return False

    def register(self):
        """Registrar usuario en el servidor"""
        msg = {
            'type': 'register',
            'username': self.username,
            'profile': self.profile,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key='server.register',
            body=json.dumps(msg)
        )

        logging.info(f"Registro enviado para {self.username}")

    def listen_messages(self):
        """Escuchar mensajes entrantes en un hilo separado"""

        def callback(ch, method, properties, body):
            try:
                data = json.loads(body.decode())
                self.process_message(data)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logging.error(f"Error procesando mensaje: {e}")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            # Cola privada y exclusiva del usuario. Todos los mensajes llegarán aquí.
            result = self.channel.queue_declare(queue=f'user.{self.username}', durable=True)
            queue_name = result.method.queue

            # Binding para mensajes privados (dirigidos específicamente a este usuario)
            self.channel.queue_bind(
                exchange='chat_exchange',
                queue=queue_name,
                routing_key=f'user.{self.username}.*'
            )

            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback
            )

            # Procesar mensajes con timeout para poder verificar self.running
            while self.running:
                self.connection.process_data_events(time_limit=1)

        except Exception as e:
            if self.running:
                logging.error(f"Error en listener: {e}")
                print(f"\n⚠️  Conexión perdida. Intenta reconectar.")

    def process_message(self, data):
        """Procesar mensajes recibidos"""
        msg_type = data.get('type')

        if msg_type == 'register_response':
            self.channels = data.get('channels', [])
            print(f"\n✅ Registrado exitosamente")
            print(f"📢 Canales disponibles: {', '.join(self.channels)}")

        elif msg_type == 'channel_message':
            if data['from'] != self.username:
                print(f"\n[{data['channel']}] {data['from']}: {data['message']}")
                print(f"[{self.current_channel}]> ", end='', flush=True)
                self.save_message(f"channel_{data['channel']}", data)

        elif msg_type == 'private_message':
            print(f"\n💬 [PRIVADO] {data['from']}: {data['message']}")
            print(f"[{self.current_channel}]> ", end='', flush=True)
            self.save_message(f"private_{data['from']}", data)

        elif msg_type == 'file_notification':
            print(f"\n📎 Archivo recibido de {data['from']}: {data['filename']}")
            self.save_received_file(data)
            print(f"[{self.current_channel}]> ", end='', flush=True)

        elif msg_type == 'users_list':
            print(f"\n👥 Usuarios conectados: {', '.join(data['users'])}")
            print(f"[{self.current_channel}]> ", end='', flush=True)

    def subscribe_to_channel(self, channel_name):
        """Suscribirse a un canal (sin duplicate consumer)"""
        if channel_name in self.subscribed_channels:
            return

        try:
            self.channel.queue_bind(
                exchange='chat_exchange',
                queue=f'user.{self.username}',
                routing_key=f'channel.{channel_name}.*'
            )

            # Crear callback específico para este canal
            def channel_callback(ch, method, properties, body):
                try:
                    data = json.loads(body.decode())
                    if data['from'] != self.username and data['channel'] == self.current_channel:
                        print(f"\n[{data['channel']}] {data['from']}: {data['message']}")
                        print(f"[{self.current_channel}]> ", end='', flush=True)
                        self.save_message(f"channel_{data['channel']}", data)
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception as e:
                    logging.error(f"Error en canal {channel_name}: {e}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            self.subscribed_channels.add(channel_name)
            logging.info(f"Suscrito al canal: {channel_name}")

        except Exception as e:
            logging.error(f"Error suscribiéndose al canal {channel_name}: {e}")

    def join_channel(self, channel_name):
        """Unirse a un canal"""
        self.current_channel = channel_name

        # Suscribirse si no lo está ya
        if channel_name not in self.subscribed_channels:
            self.subscribe_to_channel(channel_name)

        print(f"📢 Unido al canal: {channel_name}")

    def send_channel_message(self, message):
        """Enviar mensaje a un canal"""
        msg = {
            'type': 'channel_message',
            'from': self.username,
            'channel': self.current_channel,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key='server.channel_message',
            body=json.dumps(msg)
        )

        # Guardar mensaje propio
        self.save_message(f"channel_{self.current_channel}", msg)

    def send_private_message(self, to_user, message):
        """Enviar mensaje privado"""
        msg = {
            'type': 'private_message',
            'from': self.username,
            'to': to_user,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key='server.private_message',
            body=json.dumps(msg)
        )

        # Guardar mensaje propio
        self.save_message(f"private_{to_user}", msg)
        print(f"✉️  Mensaje privado enviado a {to_user}")

    def send_file(self, to_user, filepath):
        """Enviar archivo a un usuario"""
        try:
            if not os.path.exists(filepath):
                print(f"❌ Archivo no encontrado: {filepath}")
                return

            with open(filepath, 'rb') as f:
                file_data = f.read().hex()

            filename = os.path.basename(filepath)

            msg = {
                'type': 'file_transfer',
                'from': self.username,
                'to': to_user,
                'filename': filename,
                'file_data': file_data,
                'timestamp': datetime.now().isoformat()
            }

            self.channel.basic_publish(
                exchange='chat_exchange',
                routing_key='server.file_transfer',
                body=json.dumps(msg)
            )

            print(f"📤 Archivo '{filename}' enviado a {to_user}")
            logging.info(f"Archivo enviado: {filename} a {to_user}")
        except Exception as e:
            print(f"❌ Error enviando archivo: {e}")
            logging.error(f"Error enviando archivo: {e}")

    def update_profile(self, bio=None, photo_path=None):
        """Actualizar perfil de usuario"""
        if bio:
            self.profile['bio'] = bio

        if photo_path and os.path.exists(photo_path):
            with open(photo_path, 'rb') as f:
                self.profile['photo'] = f.read().hex()

        msg = {
            'type': 'update_profile',
            'username': self.username,
            'profile': self.profile,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key='server.update_profile',
            body=json.dumps(msg)
        )

        print("✅ Perfil actualizado")

    def get_users(self):
        """Solicitar lista de usuarios conectados"""
        msg = {
            'type': 'get_users',
            'from': self.username,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key='server.get_users',
            body=json.dumps(msg)
        )

    def save_message(self, conv_id, message):
        """Guardar mensaje en archivo local"""
        conv_file = f"client_conversations/{self.username}_{conv_id}.json"

        conversations = []
        if os.path.exists(conv_file):
            with open(conv_file, 'r') as f:
                conversations = json.load(f)

        conversations.append(message)

        with open(conv_file, 'w') as f:
            json.dump(conversations, f, indent=2)

    def save_received_file(self, data):
        """Guardar archivo recibido"""
        filename = data['filename']
        file_data = data['file_data']

        filepath = f"client_files/{self.username}_{filename}"
        with open(filepath, 'wb') as f:
            f.write(bytes.fromhex(file_data))

        print(f"💾 Archivo guardado en: {filepath}")

    def show_help(self):
        """Mostrar comandos disponibles"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                    COMANDOS DISPONIBLES                      ║
╠══════════════════════════════════════════════════════════════╣
║ /join <canal>          - Unirse a un canal                   ║
║ /private <usuario>     - Enviar mensaje privado              ║
║ /file <usuario> <ruta> - Enviar archivo a usuario            ║
║ /users                 - Ver usuarios conectados             ║
║ /profile <bio>         - Actualizar biografía                ║
║ /history               - Ver historial del canal actual      ║
║ /help                  - Mostrar esta ayuda                  ║
║ /quit                  - Salir del chat                      ║
╠══════════════════════════════════════════════════════════════╣
║ Para enviar mensajes: escribe directamente en el canal      ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(help_text)

    def show_history(self):
        """Mostrar historial del canal actual"""
        conv_file = f"client_conversations/{self.username}_channel_{self.current_channel}.json"

        if not os.path.exists(conv_file):
            print("📭 No hay historial para este canal")
            return

        with open(conv_file, 'r') as f:
            messages = json.load(f)

        print(f"\n📜 Historial de #{self.current_channel} (últimos 20 mensajes):")
        print("=" * 60)
        for msg in messages[-20:]:
            timestamp = msg.get('timestamp', '')[:19]
            print(f"[{timestamp}] {msg['from']}: {msg['message']}")
        print("=" * 60)

    def start(self):
        """Iniciar cliente"""
        if not self.connect():
            return

        self.register()

        # Iniciar listener en hilo separado
        self.listener_thread = threading.Thread(target=self.listen_messages, daemon=True)
        self.listener_thread.start()

        # Esperar un momento para el registro
        time.sleep(1)

        # Unirse al canal general por defecto
        self.join_channel('general')

        self.show_welcome()
        self.show_help()

        # Loop principal de comandos
        try:
            while self.running:
                user_input = input(f"[{self.current_channel}]> ")

                if not user_input.strip():
                    continue

                if user_input.startswith('/'):
                    self.process_command(user_input)
                else:
                    self.send_channel_message(user_input)

        except KeyboardInterrupt:
            print("\n\n👋 Saliendo del chat...")
        except Exception as e:
            logging.error(f"Error en loop principal: {e}")
            print(f"\n❌ Error: {e}")
        finally:
            self.stop()

    def show_welcome(self):
        """Mostrar mensaje de bienvenida"""
        print("\n" + "=" * 60)
        print(f"🎉 Bienvenido al Chat AMQP, {self.username}!")
        print("=" * 60)

    def process_command(self, command):
        """Procesar comandos del usuario"""
        parts = command.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd == '/quit':
            self.running = False
            print("👋 Hasta luego!")

        elif cmd == '/help':
            self.show_help()

        elif cmd == '/join' and len(parts) > 1:
            self.join_channel(parts[1])

        elif cmd == '/private' and len(parts) > 1:
            to_user = parts[1]
            print(f"💬 Modo privado con {to_user}. Escribe tu mensaje:")
            message = input("> ")
            if message:
                self.send_private_message(to_user, message)

        elif cmd == '/file' and len(parts) > 2:
            to_user = parts[1]
            filepath = parts[2]
            self.send_file(to_user, filepath)

        elif cmd == '/users':
            self.get_users()

        elif cmd == '/profile' and len(parts) > 1:
            bio = parts[1]
            self.update_profile(bio=bio)

        elif cmd == '/history':
            self.show_history()

        else:
            print("❌ Comando no reconocido. Usa /help para ver los comandos disponibles")

    def stop(self):
        """Detener cliente"""
        self.running = False
        time.sleep(1)  # Dar tiempo al listener para terminar
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
            except:
                pass
        logging.info(f"Cliente {self.username} desconectado")


if __name__ == '__main__':
    print("=" * 60)
    print("CLIENTE DE CHAT AMQP")
    print("=" * 60)
    username = input("Ingresa tu nombre de usuario: ").strip()

    if not username:
        print("❌ Nombre de usuario inválido")
        exit(1)

    client = ChatClient(username)
    client.start()