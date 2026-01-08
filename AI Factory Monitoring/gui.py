import tkinter as tk
from tkinter import ttk
import serial, threading, time, pickle
from collections import deque
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =======================
# 설정
# =======================
PORT = "COM10"
BAUD = 115200
MODEL_PATH = "decision_tree_sensor.pkl"
MAX_POINTS = 30
BLINK_INTERVAL = 500  # ms

# =======================
# 모델 로드
# =======================
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# =======================
# 시리얼 연결
# =======================
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# =======================
# 데이터 버퍼
# =======================
temps = deque(maxlen=MAX_POINTS)
humis = deque(maxlen=MAX_POINTS)
times = deque(maxlen=MAX_POINTS)
count = 0

# =======================
# GUI 기본
# =======================
root = tk.Tk()
root.title("AI Factory Monitoring")
root.geometry("1200x700")
root.configure(bg="#2f2f2f")

# =======================
# 프레임 구성
# =======================
left = tk.Frame(root, bg="#3a3a3a", width=300)
left.pack(side="left", fill="y")

right = tk.Frame(root, bg="#e0e0e0")
right.pack(side="right", expand=True, fill="both")

# =======================
# 상태 원형 표시
# =======================
canvas = tk.Canvas(left, width=220, height=220, bg="#3a3a3a", highlightthickness=0)
canvas.pack(pady=30)

circle = canvas.create_oval(20, 20, 200, 200, outline="black", width=4)
result_text = canvas.create_text(
    110, 110, text="WAIT", font=("Arial", 20, "bold")
)

def set_circle(color):
    canvas.itemconfig(circle, fill=color)

# =======================
# GUI 깜빡임 제어 변수
# =======================
blink_enable = False
blink_state = False
is_reset_mode = False  # RESET 모드 플래그 추가

def blink_loop():
    global blink_state
    if blink_enable and not is_reset_mode:  # RESET 모드가 아닐 때만 깜빡임
        blink_state = not blink_state
        set_circle("red" if blink_state else "")
        root.after(BLINK_INTERVAL, blink_loop)

# =======================
# Reset 버튼
# =======================
def reset_action():
    global blink_enable, is_reset_mode

    blink_enable = False
    is_reset_mode = True  # RESET 모드 활성화
    canvas.itemconfig(result_text, text="RESET")
    set_circle("red")  # 빨간색 고정

    # 데이터와 테이블은 유지 (clear 하지 않음)
    # temps.clear()
    # humis.clear()
    # times.clear()
    # count = 0
    
    # for item in tree.get_children():
    #     tree.delete(item)

    # 그래프도 유지 (clear 하지 않음)
    # ax1.clear()
    # ax2.clear()
    
    # ax1.set_xlabel('Sample Number', fontsize=13, fontweight='bold', color='#333')
    # ax1.set_ylabel('Temperature (°C)', fontsize=13, fontweight='bold', color='#FF6B35')
    # ax2.set_ylabel('Humidity (%)', fontsize=13, fontweight='bold', color='#004E89')
    
    # ax1.tick_params(axis='y', labelcolor='#FF6B35', labelsize=11, width=2)
    # ax2.tick_params(axis='y', labelcolor='#004E89', labelsize=11, width=2)
    # ax1.tick_params(axis='x', labelsize=11, width=2)
    
    # ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    # ax1.set_axisbelow(True)
    # ax1.set_facecolor('#f8f9fa')
    
    # fig.tight_layout(pad=2)
    # canvas_plot.draw()

    ser.write(b"RESET\n")

tk.Button(
    left,
    text="RESET",
    font=("Arial", 16, "bold"),
    bg="#e74c3c",
    fg="white",
    width=10,
    command=reset_action
).pack(pady=20)

# =======================
# 상태 설명
# =======================
tk.Label(
    left,
    text="OK   : Green ON\nNOK  : Red BLINK\nRESET: Red ON",
    fg="white",
    bg="#3a3a3a",
    font=("Arial", 13, "bold"),
    justify="left"
).pack(pady=10)

# =======================
# 그래프 영역 (개선됨)
# =======================
graph_frame = tk.Frame(right, bg="white")
graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

# 스타일 설정
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax1 = plt.subplots(figsize=(8, 4.5), facecolor='white')
fig.patch.set_facecolor('white')
ax2 = ax1.twinx()

canvas_plot = FigureCanvasTkAgg(fig, master=graph_frame)
canvas_plot.get_tk_widget().pack(fill="both", expand=True)

# =======================
# 테이블 영역
# =======================
table_frame = tk.Frame(right)
table_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("Time", "Temp", "Humi", "Result")
tree = ttk.Treeview(
    table_frame, columns=columns, show="headings", height=8
)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scroll.set)

tree.pack(side="left", fill="both", expand=True)
scroll.pack(side="right", fill="y")

# =======================
# 판정 처리
# =======================
def process(temp, humi):
    global blink_enable, is_reset_mode

    pred = model.predict([[temp, humi]])[0]

    if pred == 1:
        # RESET 모드일 때는 NOK로 바뀌지 않고 RESET 상태 유지
        if not is_reset_mode:
            canvas.itemconfig(result_text, text="NOK")
            blink_enable = True
            blink_loop()
        ser.write(b"NOK\n")
        return "NOK"
    else:
        # OK일 때만 RESET 모드 해제
        blink_enable = False
        is_reset_mode = False  # RESET 모드 해제
        canvas.itemconfig(result_text, text="OK")
        set_circle("green")
        ser.write(b"OK\n")
        return "OK"

# =======================
# 시리얼 수신
# =======================
def serial_loop():
    global count

    while True:
        try:
            line = ser.readline().decode().strip()
            if not line:
                continue

            temp, humi = map(float, line.split(","))
            result = process(temp, humi)

            temps.append(temp)
            humis.append(humi)
            times.append(count)
            count += 1

            tree.insert(
                "", 0,
                values=(time.strftime("%H:%M:%S"), temp, humi, result)
            )

            # ===== 그래프 업데이트 (개선됨) =====
            ax1.clear()
            ax2.clear()

            # 데이터 플롯 (마커와 선 스타일 개선)
            if len(times) > 0:
                ax1.plot(times, temps, color='#FF6B35', linewidth=2.5, 
                        marker='o', markersize=5, label='Temperature',
                        markerfacecolor='#FF6B35', markeredgecolor='white', 
                        markeredgewidth=1.5, alpha=0.9)
                ax2.plot(times, humis, color='#004E89', linewidth=2.5,
                        marker='s', markersize=5, label='Humidity',
                        markerfacecolor='#004E89', markeredgecolor='white',
                        markeredgewidth=1.5, alpha=0.9)

            # 축 레이블 및 제목
            ax1.set_xlabel('Sample Number', fontsize=13, fontweight='bold', color='#333')
            ax1.set_ylabel('Temperature (°C)', fontsize=13, fontweight='bold', color='#FF6B35')
            ax2.set_ylabel('Humidity (%)', fontsize=13, fontweight='bold', color='#004E89')
            
            # 축 색상 매칭
            ax1.tick_params(axis='y', labelcolor='#FF6B35', labelsize=11, width=2)
            ax2.tick_params(axis='y', labelcolor='#004E89', labelsize=11, width=2)
            ax1.tick_params(axis='x', labelsize=11, width=2)
            
            # 그리드 추가
            ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
            ax1.set_axisbelow(True)
            
            # 배경색
            ax1.set_facecolor('#f8f9fa')
            
            # 범례 추가
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, 
                      loc='upper left', fontsize=11, framealpha=0.95,
                      edgecolor='#ddd', fancybox=True, shadow=True)
            
            # Y축 범위 여유 추가
            if len(temps) > 0:
                temp_margin = (max(temps) - min(temps)) * 0.15
                ax1.set_ylim(min(temps) - temp_margin, max(temps) + temp_margin)
            
            if len(humis) > 0:
                humi_margin = (max(humis) - min(humis)) * 0.15
                ax2.set_ylim(min(humis) - humi_margin, max(humis) + humi_margin)

            fig.tight_layout(pad=2)
            canvas_plot.draw()

        except:
            pass

# =======================
# 실행
# =======================
threading.Thread(target=serial_loop, daemon=True).start()
root.mainloop()
ser.close()