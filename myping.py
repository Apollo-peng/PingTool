import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import locale
import platform
import re
from datetime import datetime

class PingToolApp:
    def __init__(self, root):
        self.root = root
        self.is_pinging = False
        self.process = None
        
        # 统计数据变量
        self.sent_count = 0
        self.timeout_count = 0
        self.ping_times = []
        self.start_datetime = None
        
        self.load_language()
        self.root.title(self.lang['title'])
        self.root.geometry("680x600")
        
        self.create_widgets()

    def load_language(self):
        sys_lang = locale.getdefaultlocale()[0]
        if sys_lang and sys_lang.startswith('zh'):
            self.lang = {
                'title': '高级 Ping 工具 - 完整版',
                'target': '目标主机(H):',
                'start': '开始',
                'stop': '停止',
                'count': 'Ping 次数(N):',
                'infinite': '永远 Ping(V)',
                'clear': '清空日志',
                'stat_title': 'Ping 统计信息',
                'sent': '发送包',
                'timeout': '超时',
                'loss': '包丢失',
                'min': 'Ping 最小值',
                'max': 'Ping 最大值',
                'avg': 'Ping 平均值',
                'start_time': '开始时间',
                'elapsed': '经过时间',
                'stop_time': '停止时间',
                'ms': '毫秒',
                'status_ready': '准备就绪',
                'status_pinging': '正在测试中...'
            }
        else:
            self.lang = {
                'title': 'Advanced Ping Tool - Full',
                'target': 'Target Host:',
                'start': 'Start',
                'stop': 'Stop',
                'count': 'Count:',
                'infinite': 'Ping Forever',
                'clear': 'Clear Log',
                'stat_title': 'Ping Statistics',
                'sent': 'Sent',
                'timeout': 'Timeout',
                'loss': 'Loss %',
                'min': 'Minimum',
                'max': 'Maximum',
                'avg': 'Average',
                'start_time': 'Start Time',
                'elapsed': 'Elapsed',
                'stop_time': 'Stop Time',
                'ms': 'ms',
                'status_ready': 'Ready',
                'status_pinging': 'Pinging...'
            }

    def create_widgets(self):
        # --- 顶部配置区域 ---
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text=self.lang['target']).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_entry = ttk.Entry(top_frame, width=25)
        self.target_entry.insert(0, "192.168.10.1")
        self.target_entry.grid(row=0, column=1, padx=5, pady=5)

        self.start_btn = ttk.Button(top_frame, text=self.lang['start'], command=self.start_ping)
        self.start_btn.grid(row=0, column=2, padx=5, pady=5)

        self.stop_btn = ttk.Button(top_frame, text=self.lang['stop'], command=self.stop_ping, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(top_frame, text=self.lang['count']).grid(row=1, column=0, sticky=tk.W, padx=5)
        self.count_entry = ttk.Entry(top_frame, width=10)
        self.count_entry.insert(0, "4")
        self.count_entry.grid(row=1, column=1, sticky=tk.W, padx=5)

        self.infinite_var = tk.BooleanVar(value=True) # 默认勾选永远 Ping
        self.infinite_check = ttk.Checkbutton(top_frame, text=self.lang['infinite'], variable=self.infinite_var)
        self.infinite_check.grid(row=1, column=1, sticky=tk.E, padx=5)
        
        self.clear_btn = ttk.Button(top_frame, text=self.lang['clear'], command=self.clear_log)
        self.clear_btn.grid(row=1, column=2, padx=5)

        # --- 灵魂功能：统计信息面板 ---
        stat_frame = ttk.LabelFrame(self.root, text=self.lang['stat_title'], padding="10")
        stat_frame.pack(fill=tk.X, padx=10, pady=5)

        # 定义用于实时更新的变量
        self.var_sent = tk.StringVar(value="0")
        self.var_timeout = tk.StringVar(value="0")
        self.var_loss = tk.StringVar(value="0.00 %")
        
        self.var_min = tk.StringVar(value="—")
        self.var_max = tk.StringVar(value="—")
        self.var_avg = tk.StringVar(value="—")
        
        self.var_start_t = tk.StringVar(value="—")
        self.var_elapsed = tk.StringVar(value="—")
        self.var_stop_t = tk.StringVar(value="—")

        # 布局：三列数据
        # 第一列：发送包、超时、丢包率
        ttk.Label(stat_frame, text=self.lang['sent']).grid(row=0, column=0, sticky=tk.E, padx=5, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_sent, width=8, relief="sunken", anchor="e", background="white").grid(row=0, column=1, padx=5)
        ttk.Label(stat_frame, text=self.lang['timeout']).grid(row=1, column=0, sticky=tk.E, padx=5, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_timeout, width=8, relief="sunken", anchor="e", background="white").grid(row=1, column=1, padx=5)
        ttk.Label(stat_frame, text=self.lang['loss']).grid(row=2, column=0, sticky=tk.E, padx=5, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_loss, width=8, relief="sunken", anchor="e", background="white").grid(row=2, column=1, padx=5)

        # 第二列：最小值、最大值、平均值
        ttk.Label(stat_frame, text=self.lang['min']).grid(row=0, column=2, sticky=tk.E, padx=15, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_min, width=12, relief="sunken", anchor="e", background="white").grid(row=0, column=3, padx=5)
        ttk.Label(stat_frame, text=self.lang['max']).grid(row=1, column=2, sticky=tk.E, padx=15, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_max, width=12, relief="sunken", anchor="e", background="white").grid(row=1, column=3, padx=5)
        ttk.Label(stat_frame, text=self.lang['avg']).grid(row=2, column=2, sticky=tk.E, padx=15, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_avg, width=12, relief="sunken", anchor="e", background="white").grid(row=2, column=3, padx=5)

        # 第三列：时间记录
        ttk.Label(stat_frame, text=self.lang['start_time']).grid(row=0, column=4, sticky=tk.E, padx=15, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_start_t, width=10, relief="sunken", anchor="center", background="white").grid(row=0, column=5, padx=5)
        ttk.Label(stat_frame, text=self.lang['elapsed']).grid(row=1, column=4, sticky=tk.E, padx=15, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_elapsed, width=10, relief="sunken", anchor="center", background="white").grid(row=1, column=5, padx=5)
        ttk.Label(stat_frame, text=self.lang['stop_time']).grid(row=2, column=4, sticky=tk.E, padx=15, pady=2)
        ttk.Label(stat_frame, textvariable=self.var_stop_t, width=10, relief="sunken", anchor="center", background="white").grid(row=2, column=5, padx=5)

        # --- 日志输出区域 ---
        log_frame = ttk.Frame(self.root, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg="white", fg="black", font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- 底部状态栏 ---
        self.status_var = tk.StringVar(value=self.lang['status_ready'])
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def log_message(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def reset_stats(self):
        self.sent_count = 0
        self.timeout_count = 0
        self.ping_times.clear()
        
        self.var_sent.set("0")
        self.var_timeout.set("0")
        self.var_loss.set("0.00 %")
        self.var_min.set("—")
        self.var_max.set("—")
        self.var_avg.set("—")
        
        now = datetime.now()
        self.start_datetime = now
        self.var_start_t.set(now.strftime("%H:%M:%S"))
        self.var_elapsed.set("00:00:00")
        self.var_stop_t.set("—")

    def update_clock(self):
        if self.is_pinging and self.start_datetime:
            elapsed = datetime.now() - self.start_datetime
            # 将时差格式化为 HH:MM:SS
            elapsed_str = str(elapsed).split('.')[0]
            if len(elapsed_str) == 7: # 处理 H:MM:SS 变为 HH:MM:SS
                elapsed_str = "0" + elapsed_str
            self.var_elapsed.set(elapsed_str)
            self.root.after(1000, self.update_clock)

    def start_ping(self):
        target = self.target_entry.get().strip()
        if not target: return

        self.is_pinging = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set(self.lang['status_pinging'])
        
        self.reset_stats()
        self.update_clock() # 启动计时器
        
        threading.Thread(target=self.run_ping_command, args=(target,), daemon=True).start()

    def stop_ping(self):
        self.is_pinging = False
        if self.process:
            self.process.terminate()
        
        self.var_stop_t.set(datetime.now().strftime("%H:%M:%S"))
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set(self.lang['status_ready'])

    def run_ping_command(self, target):
        count_val = self.count_entry.get().strip()
        is_infinite = self.infinite_var.get()
        
        os_name = platform.system().lower()
        command = ["ping"]
        
        if os_name == "windows":
            if not is_infinite and count_val.isdigit():
                command.extend(["-n", count_val])
            elif is_infinite:
                command.append("-t")
        else:
            if not is_infinite and count_val.isdigit():
                command.extend(["-c", count_val])
        
        command.append(target)

        try:
            self.process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                text=True, creationflags=subprocess.CREATE_NO_WINDOW if os_name == "windows" else 0
            )

            for line in iter(self.process.stdout.readline, ''):
                if not self.is_pinging: break
                self.log_message(line)
                self.parse_ping_output(line)
            
            self.process.stdout.close()
            self.process.wait()

        except Exception as e:
            self.log_message(f"\nError: {str(e)}\n")
        finally:
            if self.is_pinging:
                self.root.after(0, self.stop_ping)

    def parse_ping_output(self, line):
        line = line.strip()
        if not line: return

        # 核心正则分析引擎
        is_success = False
        is_timeout = False

        # 如果包含 TTL，通常说明收到了有效回复
        if 'TTL=' in line.upper():
            self.sent_count += 1
            is_success = True
            # 提取延迟时间，例如 time=5ms 或 time<1ms
            time_match = re.search(r'(?:time|时间)[=<]\s*([\d\.]+)', line, re.IGNORECASE)
            if time_match:
                ms = float(time_match.group(1))
                self.ping_times.append(ms)
        # 如果包含超时或无法访问的字眼
        elif "超时" in line or "timed out" in line.lower() or "unreachable" in line.lower() or "无法访问" in line:
            self.sent_count += 1
            self.timeout_count += 1
            is_timeout = True

        if is_success or is_timeout:
            self.root.after(0, self.update_stats_ui)

    def update_stats_ui(self):
        self.var_sent.set(str(self.sent_count))
        self.var_timeout.set(str(self.timeout_count))
        
        # 计算丢包率
        if self.sent_count > 0:
            loss_rate = (self.timeout_count / self.sent_count) * 100
            self.var_loss.set(f"{loss_rate:.2f} %")
            
        # 计算最大/最小/平均延迟
        if self.ping_times:
            p_min = min(self.ping_times)
            p_max = max(self.ping_times)
            p_avg = sum(self.ping_times) / len(self.ping_times)
            
            unit = f" {self.lang['ms']}"
            self.var_min.set(f"{p_min:.0f}{unit}")
            self.var_max.set(f"{p_max:.0f}{unit}")
            self.var_avg.set(f"{p_avg:.0f}{unit}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PingToolApp(root)
    root.mainloop()
