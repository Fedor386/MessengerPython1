# server_fixed.py
import socket
import threading
import json
from datetime import datetime
import argparse
import sys

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.clients = []
        self.nicknames = []
        self.server_socket = None
        self.running = False
        
    def start_server(self):
        try:
            # Исправлено: правильное создание сокета
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            print(f"🔄 Попытка запуска сервера на {self.host}:{self.port}")
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # Добавлен backlog
            self.running = True
            
            print("=" * 50)
            print("🎯 ЧАТ-СЕРВЕР ЗАПУЩЕН")
            print(f"📡 Адрес: {self.host}:{self.port}")
            print(f"🌐 Для подключения извне используйте ваш IP: {self.get_local_ip()}")
            print("⏹️  Для остановки нажмите Ctrl+C")
            print("=" * 50)
            
            self.accept_connections()
            
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"❌ Ошибка: Порт {self.port} уже занят!")
                print("💡 Попробуйте другой порт или закройте программу, использующую этот порт")
            else:
                print(f"❌ Ошибка запуска сервера: {e}")
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
        finally:
            self.stop_server()
    
    def get_local_ip(self):
        """Получает локальный IP адрес"""
        try:
            # Подключаемся к внешнему серверу чтобы узнать наш IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def accept_connections(self):
        """Принимает входящие подключения"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"🔗 Новое подключение от {address}")
                
                # Запускаем обработку клиента в отдельном потоке
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"⚠️  Ошибка при принятии подключения: {e}")
    
    def handle_client(self, client_socket, address):
        """Обрабатывает подключение клиента"""
        nickname = None
        try:
            # Запрос ника у клиента
            client_socket.send("NICK".encode('utf-8'))
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            
            if not nickname:
                nickname = f"Гость_{address[0]}"
            
            # Проверяем уникальность ника
            original_nickname = nickname
            counter = 1
            while nickname in self.nicknames:
                nickname = f"{original_nickname}_{counter}"
                counter += 1
            
            # Добавляем клиента в списки
            self.nicknames.append(nickname)
            self.clients.append(client_socket)
            
            print(f"👤 Пользователь {nickname} присоединился к чату")
            print(f"📊 Сейчас онлайн: {len(self.clients)} пользователей")
            
            # Отправляем приветственное сообщение
            welcome_msg = {
                "sender": "SERVER",
                "message": f"Добро пожаловать в чат, {nickname}!",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "type": "welcome"
            }
            client_socket.send(json.dumps(welcome_msg).encode('utf-8'))
            
            # Уведомляем всех о новом пользователе
            self.broadcast_message(f"{nickname} присоединился к чату!", "SERVER")
            
            # Основной цикл получения сообщений
            while self.running:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        break
                    
                    message_data = json.loads(message)
                    
                    if message_data.get('type') == 'message':
                        print(f"💬 {nickname}: {message_data['content']}")
                        self.broadcast_message(
                            message_data['content'], 
                            nickname
                        )
                        
                except json.JSONDecodeError:
                    print(f"⚠️  Неверный формат сообщения от {nickname}")
                except ConnectionResetError:
                    break
                except Exception as e:
                    print(f"⚠️  Ошибка с клиентом {nickname}: {e}")
                    break
                    
        except Exception as e:
            print(f"❌ Ошибка обработки клиента {address}: {e}")
        finally:
            if nickname:
                self.remove_client(client_socket, nickname)
    
    def broadcast_message(self, message, sender="SERVER"):
        """Отправляет сообщение всем клиентам"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message_data = {
            "sender": sender,
            "message": message,
            "timestamp": timestamp,
            "type": "message"
        }
        
        disconnected_clients = []
        for client in self.clients:
            try:
                client.send(json.dumps(message_data).encode('utf-8'))
            except:
                disconnected_clients.append(client)
        
        # Удаляем отключившихся клиентов
        for client in disconnected_clients:
            index = self.clients.index(client)
            nick = self.nicknames[index]
            self.remove_client(client, nick)
    
    def remove_client(self, client_socket, nickname):
        """Удаляет клиента из списков"""
        if client_socket in self.clients:
            index = self.clients.index(client_socket)
            self.clients.remove(client_socket)
            self.nicknames.remove(nickname)
            
            print(f"👋 Пользователь {nickname} покинул чат")
            print(f"📊 Осталось онлайн: {len(self.clients)} пользователей")
            
            if self.running:
                self.broadcast_message(f"{nickname} покинул чат", "SERVER")
            
            try:
                client_socket.close()
            except:
                pass
    
    def stop_server(self):
        """Останавливает сервер"""
        self.running = False
        print("\n🛑 Остановка сервера...")
        
        # Отправляем сообщение о закрытии
        shutdown_msg = {
            "sender": "SERVER",
            "message": "Сервер останавливается...",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": "shutdown"
        }
        
        for client in self.clients:
            try:
                client.send(json.dumps(shutdown_msg).encode('utf-8'))
                client.close()
            except:
                pass
        
        if self.server_socket:
            self.server_socket.close()
        
        print("✅ Сервер остановлен")

def check_port_availability(port):
    """Проверяет доступность порта"""
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('localhost', port))
        test_socket.close()
        return True
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description='Чат-сервер')
    parser.add_argument('--host', default='0.0.0.0', help='Хост (по умолчанию: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5555, help='Порт (по умолчанию: 5555)')
    parser.add_argument('--check-port', action='store_true', help='Проверить доступность порта')
    
    args = parser.parse_args()
    
    # Проверка порта
    if args.check_port or not check_port_availability(args.port):
        if not check_port_availability(args.port):
            print(f"❌ Порт {args.port} занят!")
            print("💡 Попробуйте:")
            print(f"   python server_fixed.py --port {args.port + 1}")
            print("   netstat -ano | findstr :5555  # Windows - найти процесс")
            return
    
    # Запуск сервера
    server = ChatServer(args.host, args.port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\n🛑 Остановка по команде пользователя")
        server.stop_server()

if __name__ == "__main__":
    main()