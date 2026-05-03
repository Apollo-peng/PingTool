import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import locale
import platform
import time

class PingToolApp:
    def __init__(self, root):
        self.root = root
        self.is_pinging = False
        self.process = None
        
        # 1. 检测系统语言并加载对应语言包
        self.load_language()
        
        self.root.title(self.lang['title'])
        self.root.geometry("650x500")
        
        # 2. 构建 UI
        self.create_widgets()

    def load_language(self):
        # 获取系统默认语言，例如 'zh_CN' 或 'en_US'
        sys_lang = locale.getdefaultlocale()[0]
        
        if sys_lang and sys_lang.startswith('zh'):
            self.lang = {
                'title': '高级 Ping 工具 (自动检测语言)',
                'target': '目标主机 (IP/域名):',
                'start': '开始',
                'stop': '停止',
                'count': 'Ping 次数:',
                'infinite': '永远 Ping (不停止)',
                'clear': '清空日志',
                'status_ready': '准备就绪',
                'status_pinging': '正在 Ping...',
                'error_empty': '请输入目标主机地址！'
            }
        else:
            self.lang = {
                'title': 'Advanced Ping Tool (Auto Language)',
                'target': 'Target Host (IP/Domain):',
                'start': 'Start',
                'stop': 'Stop',
                'count': 'Ping Count:',
                'infinite': 'Ping forever',
                'clear': 'Clear Log',
                'status_ready': 'Ready',
                'status_pinging': 'Pinging...',
                'error_empty': 'Please enter a target host!'
            }

    def create_widgets(self):
        # 顶部配置区域
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text=self.lang['target']).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.target_entry = ttk.Entry(top_frame, width=30)
        self.target_entry.insert(0, "192.168.10.1")
        self.target_entry.grid(row=0, column=1, padx=5, pady=5)

        self.start_btn = ttk.Button(top_frame, text=self.lang['start'], command=self.start_ping)
        self.start_btn.grid(row=0, column=2, padx=5, pady=5)

        self.stop_btn = ttk.Button(top_frame, text=self.lang['stop'], command=self.stop_ping, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=3, padx=5, pady=5)

        # 参数设置区域
        param_frame = ttk.Frame(self.root, padding="10")
        param_frame.pack(fill=tk.X)

        ttk.Label(param_frame, text=self.lang['count']).grid(row=0, column=0, sticky=tk.W)
        self.count_entry = ttk.Entry(param_frame, width=10)
        self.count_entry.insert(0, "4")
        self.count_entry.grid(row=0, column=1, padx=5)

        self.infinite_var = tk.BooleanVar(value=False)
        self.infinite_check = ttk.Checkbutton(param_frame, text=self.lang['infinite'], variable=self.infinite_var)
        self.infinite_check.grid(row=0, column=2, padx=15)
        
        self.clear_btn = ttk.Button(param_frame, text=self.lang['clear'], command=self.clear_log)
        self.clear_btn.grid(row=0, column=3, padx=5)

        # 日志输出区域
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg="black", fg="white", font=("Consolas", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 底部状态栏
        self.status_var = tk.StringVar(value=self.lang['status_ready'])
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log_message(self, message):
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)  # 自动滚动到底部

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def start_ping(self):
        target = self.target_entry.get().strip()
        if not target:
            self.log_message(self.lang['error_empty'] + "\n")
            return

        self.is_pinging = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set(self.lang['status_pinging'])
        
        # 使用新线程运行 ping，防止阻塞主 GUI 界面
        threading.Thread(target=self.run_ping_command, args=(target,), daemon=True).start()

    def stop_ping(self):
        self.is_pinging = False
        if self.process:
            self.process.terminate() # 尝试终止子进程
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set(self.lang['status_ready'])
        self.log_message("\n--- Ping Stopped by User ---\n\n")

    def run_ping_command(self, target):
        count_val = self.count_entry.get().strip()
        is_infinite = self.infinite_var.get()
        
        # 判断操作系统以使用正确的 Ping 参数
        os_name = platform.system().lower()
        command = ["ping"]
        
        if os_name == "windows":
            if not is_infinite and count_val.isdigit():
                command.extend(["-n", count_val])
            elif is_infinite:
                command.append("-t")
        else:
            # Linux / macOS
            if not is_infinite and count_val.isdigit():
                command.extend(["-c", count_val])
        
        command.append(target)
        self.log_message(f"Executing: {' '.join(command)}\n")

        try:
            # 启动子进程捕获输出
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os_name == "windows" else 0
            )

            # 实时读取输出
            for line in iter(self.process.stdout.readline, ''):
                if not self.is_pinging:
                    break
                self.log_message(line)
            
            self.process.stdout.close()
            self.process.wait()

        except Exception as e:
            self.log_message(f"\nError: {str(e)}\n")
        finally:
            self.root.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        if self.is_pinging: # 如果是自然结束而非手动停止
            self.is_pinging = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_var.set(self.lang['status_ready'])
            self.log_message("\n--- Ping Finished ---\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = PingToolApp(root)
    root.mainloop()