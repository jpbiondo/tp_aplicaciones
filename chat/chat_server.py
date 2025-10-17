import pika
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chat_server.log'),
        logging.StreamHandler()
    ]
)


class ChatServer:
    def __init__(self, host='localhost'):
        self.host = host
        self.connection = None
        self.channel = None
        self.users = {}  # {username: {profile, status}}
        self.channels = ['general', 'random', 'anuncios']  # Canales predefinidos

        # Crear directorio para archivos
        Path('server_files').mkdir(exist_ok=True)
        Path('server_profiles').mkdir(exist_ok=True)

        logging.info("Servidor de chat inicializado")

    def connect(self):
        """Conectar al servidor RabbitMQ"""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=self.host)
            )
            self.channel = self.connection.channel()

            # Declarar exchanges
            self.channel.exchange_declare(
                exchange='chat_exchange',
                exchange_type='topic',
                durable=True
            )

            # Declarar cola para el servidor
            self.channel.queue_declare(queue='server_queue', durable=True)
            self.channel.queue_bind(
                exchange='chat_exchange',
                queue='server_queue',
                routing_key='server.*'
            )

            # Crear canales predefinidos
            for ch in self.channels:
                self.channel.queue_declare(queue=f'channel.{ch}', durable=True)
                self.channel.queue_bind(
                    exchange='chat_exchange',
                    queue=f'channel.{ch}',
                    routing_key=f'channel.{ch}.*'
                )

            logging.info(f"Conectado a RabbitMQ en {self.host}")
            return True
        except Exception as e:
            logging.error(f"Error al conectar: {e}")
            return False

    def handle_message(self, ch, method, properties, body):
        """Procesar mensajes recibidos"""
        try:
            data = json.loads(body.decode())
            msg_type = data.get('type')

            logging.info(f"Mensaje recibido - Tipo: {msg_type}, De: {data.get('from')}")

            if msg_type == 'register':
                self.handle_register(data)
            elif msg_type == 'channel_message':
                self.handle_channel_message(data)
            elif msg_type == 'private_message':
                self.handle_private_message(data)
            elif msg_type == 'file_transfer':
                self.handle_file_transfer(data)
            elif msg_type == 'update_profile':
                self.handle_update_profile(data)
            elif msg_type == 'get_users':
                self.handle_get_users(data)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logging.error(f"Error procesando mensaje: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    def handle_register(self, data):
        """Registrar un nuevo usuario"""
        username = data['username']
        profile = data.get('profile', {})

        self.users[username] = {
            'profile': profile,
            'status': 'online',
            'registered_at': datetime.now().isoformat()
        }

        # Crear cola privada para el usuario
        self.channel.queue_declare(queue=f'user.{username}', durable=True)
        self.channel.queue_bind(
            exchange='chat_exchange',
            queue=f'user.{username}',
            routing_key=f'user.{username}.*'
        )

        logging.info(f"Usuario registrado: {username}")

        # Enviar confirmación
        response = {
            'type': 'register_response',
            'success': True,
            'channels': self.channels,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key=f'user.{username}.response',
            body=json.dumps(response)
        )

    def handle_channel_message(self, data):
        """Reenviar mensaje a un canal"""
        channel_name = data['channel']
        msg = {
            'type': 'channel_message',
            'from': data['from'],
            'channel': channel_name,
            'message': data['message'],
            'timestamp': datetime.now().isoformat()
        }

        # Guardar en log del canal
        self.save_conversation(f'channel_{channel_name}', msg)

        # Publicar en el canal
        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key=f'channel.{channel_name}.message',
            body=json.dumps(msg)
        )

        logging.info(f"Mensaje en canal '{channel_name}' de {data['from']}")

    def handle_private_message(self, data):
        """Reenviar mensaje privado"""
        msg = {
            'type': 'private_message',
            'from': data['from'],
            'to': data['to'],
            'message': data['message'],
            'timestamp': datetime.now().isoformat()
        }

        # Guardar conversación
        conv_id = f"private_{min(data['from'], data['to'])}_{max(data['from'], data['to'])}"
        self.save_conversation(conv_id, msg)

        # Enviar al destinatario
        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key=f"user.{data['to']}.message",
            body=json.dumps(msg)
        )

        logging.info(f"Mensaje privado de {data['from']} a {data['to']}")

    def handle_file_transfer(self, data):
        """Gestionar transferencia de archivos"""
        filename = data['filename']
        file_data = data['file_data']
        from_user = data['from']
        to_user = data['to']

        # Guardar archivo en el servidor
        filepath = f"server_files/{from_user}_{filename}"
        with open(filepath, 'wb') as f:
            f.write(bytes.fromhex(file_data))

        logging.info(f"Archivo recibido: {filename} de {from_user} para {to_user}")

        # Notificar al destinatario
        msg = {
            'type': 'file_notification',
            'from': from_user,
            'filename': filename,
            'file_data': file_data,
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key=f"user.{to_user}.message",
            body=json.dumps(msg)
        )

    def handle_update_profile(self, data):
        """Actualizar perfil de usuario"""
        username = data['username']
        profile = data['profile']

        if username in self.users:
            self.users[username]['profile'] = profile

            # Guardar foto de perfil si existe
            if 'photo' in profile:
                photo_path = f"server_profiles/{username}.jpg"
                with open(photo_path, 'wb') as f:
                    f.write(bytes.fromhex(profile['photo']))
                profile['photo_path'] = photo_path

            logging.info(f"Perfil actualizado para {username}")

    def handle_get_users(self, data):
        """Enviar lista de usuarios"""
        requester = data['from']
        users_list = {
            'type': 'users_list',
            'users': list(self.users.keys()),
            'timestamp': datetime.now().isoformat()
        }

        self.channel.basic_publish(
            exchange='chat_exchange',
            routing_key=f"user.{requester}.response",
            body=json.dumps(users_list)
        )

    def save_conversation(self, conv_id, message):
        """Guardar conversación en archivo"""
        conv_file = f"conversations/{conv_id}.json"
        Path('conversations').mkdir(exist_ok=True)

        conversations = []
        if os.path.exists(conv_file):
            with open(conv_file, 'r') as f:
                conversations = json.load(f)

        conversations.append(message)

        with open(conv_file, 'w') as f:
            json.dump(conversations, f, indent=2)

    def start(self):
        """Iniciar el servidor"""
        if not self.connect():
            return

        print("=" * 60)
        print("SERVIDOR DE CHAT AMQP")
        print("=" * 60)
        print(f"Estado: Escuchando en {self.host}")
        print(f"Canales disponibles: {', '.join(self.channels)}")
        print("Presiona Ctrl+C para detener el servidor")
        print("=" * 60)

        self.channel.basic_consume(
            queue='server_queue',
            on_message_callback=self.handle_message
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logging.info("Servidor detenido por el usuario")
            self.stop()

    def stop(self):
        """Detener el servidor"""
        if self.connection:
            self.connection.close()
        logging.info("Servidor finalizado")


if __name__ == '__main__':
    server = ChatServer()
    server.start()