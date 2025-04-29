import tkinter as tk
from tkinter import messagebox
import schedule
import time
import threading
import pyttsx3
import csv
from datetime import datetime

# --------------------- Speech Engine ---------------------
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# --------------------- File Operations ---------------------
def add_medicine():
    name = entry_name.get()
    time_str = entry_time.get()

    if name == "" or time_str == "":
        messagebox.showwarning("Input Error", "Please enter both medicine name and time!")
        return
    
    with open('medicines.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([name, time_str])

    messagebox.showinfo("Success", f"Medicine '{name}' added for {time_str}!")
    entry_name.delete(0, tk.END)
    entry_time.delete(0, tk.END)

def load_medicines():
    medicines = []
    try:
        with open('medicines.csv', 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:  # Avoid empty rows
                    medicines.append((row[0], row[1]))
    except FileNotFoundError:
        pass
    return medicines

def log_medicine(medicine_name, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open('logs.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([medicine_name, now, status])

# --------------------- Reminder Function ---------------------
current_reminders = {}  # To track pending reminders

def check_medicines():
    now = datetime.now().strftime("%H:%M")
    medicines = load_medicines()
    for med_name, med_time in medicines:
        if now == med_time and med_name not in current_reminders:
            # New reminder triggered
            current_reminders[med_name] = True
            speak(f"Time to take your medicine: {med_name}")
            show_reminder(med_name)

def show_reminder(medicine_name):
    reminder_window = tk.Toplevel(root)
    reminder_window.title("Medicine Reminder")

    lbl = tk.Label(reminder_window, text=f"Did you take your medicine: {medicine_name}?", font=("Arial", 14))
    lbl.pack(pady=10)

    btn_taken = tk.Button(reminder_window, text="Taken ✅", command=lambda: taken_action(medicine_name, reminder_window))
    btn_taken.pack(side="left", padx=20, pady=20)

    btn_missed = tk.Button(reminder_window, text="Missed ❌", command=lambda: missed_action(medicine_name, reminder_window))
    btn_missed.pack(side="right", padx=20, pady=20)

    # ------------------ Timeout Logic ------------------
    def auto_miss():
        time.sleep(300)  # Wait 5 minutes
        if reminder_window.winfo_exists():
            speak(f"You missed your medicine: {medicine_name}. Please take it now.")
            time.sleep(60)  # Wait 1 more minute
            if reminder_window.winfo_exists():
                log_medicine(medicine_name, "Missed (Auto)")
                if medicine_name in current_reminders:
                    del current_reminders[medicine_name]
                try:
                    reminder_window.destroy()
                except:
                    pass

    timeout_thread = threading.Thread(target=auto_miss)
    timeout_thread.daemon = True
    timeout_thread.start()

def taken_action(medicine_name, window):
    log_medicine(medicine_name, "Taken")
    if medicine_name in current_reminders:
        del current_reminders[medicine_name]
    window.destroy()

def missed_action(medicine_name, window):
    log_medicine(medicine_name, "Missed")
    if medicine_name in current_reminders:
        del current_reminders[medicine_name]
    window.destroy()

def reset_reminders():
    current_reminders.clear()

# --------------------- Background Scheduler ---------------------
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# --------------------- GUI ---------------------
root = tk.Tk()
root.title("Medicine Reminder App")
root.geometry("400x300")

title = tk.Label(root, text="Add Medicine Reminder", font=("Arial", 16))
title.pack(pady=10)

label_name = tk.Label(root, text="Medicine Name:")
label_name.pack()
entry_name = tk.Entry(root, font=("Arial", 12))
entry_name.pack(pady=5)

label_time = tk.Label(root, text="Time (24Hr Format HH:MM):")
label_time.pack()
entry_time = tk.Entry(root, font=("Arial", 12))
entry_time.pack(pady=5)

add_button = tk.Button(root, text="Add Medicine", command=add_medicine, font=("Arial", 12), bg="lightgreen")
add_button.pack(pady=10)

note = tk.Label(root, text="(Keep the app running for reminders!)", font=("Arial", 10), fg="red")
note.pack(pady=10)

schedule.every().day.at("00:00").do(reset_reminders)

# Schedule medicine check every 1 minute
schedule.every(1).minutes.do(check_medicines)

# Start background thread for schedule
t = threading.Thread(target=run_schedule)
t.daemon = True
t.start()

root.mainloop()
