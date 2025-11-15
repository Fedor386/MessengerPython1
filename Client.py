# client.py
import socket
import threading
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, ttk
import sys

class ChatClient:
    def __init__(self):
        self.client_socket = None
        self.nickname = ""
        self.connected = False
        self.host = "localhost"
        self.port = 5555
        
        self.setup_gui()
        
    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Мессенджер v2.0")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Стиль
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TEntry", padding=6)
        
        self.create_connection_frame()
        self.create_chat_frame()
        self.create_status_bar()
        
        # Настройка тегов для цветного текста
        self.setup_text_tags()
        
    def create_connection_frame(self):
        connection_frame = ttk.LabelFrame(self.root, text="Подключение", padding=10)
        connection_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Хост
        ttk.Label(connection_frame, text="Хост:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.host_entry = ttk.Entry(connection_frame, width=20)
        self.host_entry.insert(0, "localhost")
        self.host_entry.grid(row=0, column=1, padx=5)
        
        # Порт
        ttk.Label(connection_frame, text="Порт:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.port_entry = ttk.Entry(connection_frame, width=10)
        self.port_entry.insert(0, "5555")
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # Кнопки подключения
        self.connect_button = ttk.Button(connection_frame, text="Подключиться", 
                                       command=self.connect_to_server)
        self.connect_button.grid(row=0, column=4, padx=10)
        
        self.disconnect_button = ttk.Button(connection_frame, text="Отключиться", 
                                          command=self.disconnect, state=tk.DISABLED)
        self.disconnect_button.grid(row=0, column=5, padx=5)
        
        # Никнейм
        ttk.Label(connection_frame, text="Никнейм:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.nickname_entry = ttk.Entry(connection_frame, width=20)
        self.nickname_entry.insert(0, f"User_{id(self) % 1000}")
        self.nickname_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W+tk.E)
        
    def create_chat_frame(self):
        chat_frame = ttk.LabelFrame(self.root, text="Чат", padding=10)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Область чата
        self.chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                 state=tk.DISABLED, height=20)
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        # Панель ввода
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.message_entry = ttk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = ttk.Button(input_frame, text="Отправить", 
                                    command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Кнопки команд
        command_frame = ttk.Frame(chat_frame)
        command_frame.pack(fill=tk.X)
        
        ttk.Button(command_frame, text="Список пользователей", 
                  command=self.request_users).pack(side=tk.LEFT, padx=2)
        ttk.Button(command_frame, text="Очистить чат", 
                  command=self.clear_chat).pack(side=tk.LEFT, padx=2)
        
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Не подключено")
        
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def setup_text_tags(self):
        # Настройка цветов для разных типов сообщений
        self.chat_area.tag_config("server", foreground="blue", font=('Arial', 9, 'italic'))
        self.chat_area.tag_config("welcome", foreground="green", font=('Arial', 9, 'bold'))
        self.chat_area.tag_config("error", foreground="red", font=('Arial', 9, 'bold'))
        self.chat_area.tag_config("info", foreground="purple", font=('Arial', 9, 'italic'))
        self.chat_area.tag_config("my_message", foreground="darkgreen", font=('Arial', 9))
        self.chat_area.tag_config("user_message", foreground="black", font=('Arial', 9))
        
    def connect_to_server(self):
        try:
            self.host = self.host_entry.get().strip()
            self.port = int(self.port_entry.get().strip())
            self.nickname = self.nickname_entry.get().strip()
            
            if not self.nickname:
                messagebox.showwarning("Предупреждение", "Введите никнейм!")
                return
            
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(5)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.settimeout(None)
            
            # Обработка запроса ника
            message = self.client_socket.recv(1024).decode('utf-8')
            if message == "NICK":
                self.client_socket.send(self.nickname.encode('utf-8'))
            
            self.connected = True
            self.update_connection_status(True)
            
            # Запуск потока для получения сообщений
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.add_message_to_chat("⚡ Подключение установлено!", "server")
            
        except socket.timeout:
            messagebox.showerror("Ошибка", "Таймаут подключения к серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться: {e}")
    
    def update_connection_status(self, connected):
        if connected:
            self.connect_button.config(state=tk.DISABLED)
            self.disconnect_button.config(state=tk.NORMAL)
            self.host_entry.config(state=tk.DISABLED)
            self.port_entry.config(state=tk.DISABLED)
            self.nickname_entry.config(state=tk.DISABLED)
            self.status_var.set(f"Подключено к {self.host}:{self.port} как {self.nickname}")
        else:
            self.connect_button.config(state=tk.NORMAL)
            self.disconnect_button.config(state=tk.DISABLED)
            self.host_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)
            self.nickname_entry.config(state=tk.NORMAL)
            self.status_var.set("Не подключено")
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                    
                message_data = json.loads(message)
                self.handle_received_message(message_data)
                
            except Exception as e:
                if self.connected:
                    self.add_message_to_chat(f"❌ Ошибка соединения: {e}", "error")
                break
        
        if self.connected:
            self.disconnect()
    
    def handle_received_message(self, message_data):
        msg_type = message_data.get('type', 'message')
        sender = message_data.get('sender', 'UNKNOWN')
        message = message_data.get('message', '')
        timestamp = message_data.get('timestamp', '')
        
        if msg_type == 'shutdown':
            self.add_message_to_chat("⚡ Сервер остановлен", "error")
            self.disconnect()
        elif msg_type == 'welcome':
            self.add_message_to_chat(f"⭐ {message}", "welcome")
        elif msg_type == 'info':
            self.add_message_to_chat(f"ℹ️  {message}", "info")
        else:
            if sender == "SERVER":
                self.add_message_to_chat(f"[{timestamp}] ⚡ {message}", "server")
            elif sender == self.nickname:
                self.add_message_to_chat(f"[{timestamp}] Вы: {message}", "my_message")
            else:
                self.add_message_to_chat(f"[{timestamp}] {sender}: {message}", "user_message")
    
    def add_message_to_chat(self, message, tag="user_message"):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n", tag)
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
    
    def send_message(self, event=None):
        if not self.connected:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь к серверу!")
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        if message.startswith('/'):
            self.handle_command(message)
        else:
            message_data = {
                "type": "message",
                "content": message,
                "color": "black"
            }
            
            try:
                self.client_socket.send(json.dumps(message_data).encode('utf-8'))
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                self.add_message_to_chat(f"❌ Ошибка отправки: {e}", "error")
                self.disconnect()
    
    def handle_command(self, command):
        if command == '/users':
            message_data = {
                "type": "command",
                "command": "users"
            }
            try:
                self.client_socket.send(json.dumps(message_data).encode('utf-8'))
            except:
                self.disconnect()
        elif command == '/clear':
            self.clear_chat()
        else:
            self.add_message_to_chat(f"❌ Неизвестная команда: {command}", "error")
    
    def request_users(self):
        if self.connected:
            self.handle_command('/users')
    
    def clear_chat(self):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete(1.0, tk.END)
        self.chat_area.config(state=tk.DISABLED)
    
    def disconnect(self):
        if self.connected:
            self.connected = False
            try:
                self.client_socket.close()
            except:
                pass
            
            self.update_connection_status(False)
            self.add_message_to_chat("⚡ Отключено от сервера", "server")
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.connected:
            self.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    client = ChatClient()
    client.run()