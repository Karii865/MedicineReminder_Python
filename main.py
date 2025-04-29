import tkinter as tk
from tkinter import messagebox, simpledialog
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
                if row:
                    medicines.append((row[0], row[1]))
    except FileNotFoundError:
        pass
    return medicines

def save_medicines(medicines):
    with open('medicines.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(medicines)

def log_medicine(medicine_name, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open('logs.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([medicine_name, now, status])

# --------------------- Reminder Function ---------------------
current_reminders = {}

def check_medicines():
    now = datetime.now().strftime("%H:%M")
    medicines = load_medicines()
    for med_name, med_time in medicines:
        if now == med_time and med_name not in current_reminders:
            current_reminders[med_name] = True
            speak(f"Time to take your medicine: {med_name}")
            show_reminder(med_name)

def reset_reminders():
    global current_reminders
    current_reminders.clear()
    print("Daily reminders reset.")

def run_schedule():
    schedule.every().day.at("00:00").do(reset_reminders)  # Reset at midnight
    schedule.every(1).minutes.do(check_medicines)         # Check every minute
    while True:
        schedule.run_pending()
        time.sleep(1)

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
        time.sleep(120)  # Wait 5 minutes
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

# --------------------- Background Scheduler ---------------------
def run_schedule():
    schedule.every(1).minutes.do(check_medicines)
    while True:
        schedule.run_pending()
        time.sleep(1)

# --------------------- View, Edit, Delete Medicines ---------------------
def view_medicines_only():
    medicines = load_medicines()
    if not medicines:
        messagebox.showinfo("No Reminders", "No scheduled medicines found.")
        return

    view_win = tk.Toplevel(root)
    view_win.title("View Medicines")
    view_win.geometry("350x250")

    lbl = tk.Label(view_win, text="Scheduled Medicines", font=("Arial", 12))
    lbl.pack(pady=5)

    listbox = tk.Listbox(view_win, font=("Arial", 12))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for name, time_str in medicines:
        listbox.insert(tk.END, f"{name} at {time_str}")

def edit_medicines_only():
    medicines = load_medicines()
    if not medicines:
        messagebox.showinfo("No Reminders", "No scheduled medicines found.")
        return

    edit_win = tk.Toplevel(root)
    edit_win.title("Edit Medicines")
    edit_win.geometry("350x300")

    lbl = tk.Label(edit_win, text="Select medicine to edit", font=("Arial", 12))
    lbl.pack(pady=5)

    listbox = tk.Listbox(edit_win, font=("Arial", 12))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for idx, (name, time_str) in enumerate(medicines):
        listbox.insert(idx, f"{name} at {time_str}")

    def on_edit(event):
        selection = listbox.curselection()
        if not selection:
            return
        index = selection[0]
        name, time_str = medicines[index]

        new_name = simpledialog.askstring("Edit Name", "Enter new medicine name:", initialvalue=name)
        new_time = simpledialog.askstring("Edit Time", "Enter new time (HH:MM):", initialvalue=time_str)

        if new_name and new_time:
            medicines[index] = (new_name, new_time)
            save_medicines(medicines)
            messagebox.showinfo("Updated", "Reminder updated successfully.")
            edit_win.destroy()
            edit_medicines_only()

    listbox.bind("<<ListboxSelect>>", on_edit)

def delete_medicines_only():
    medicines = load_medicines()
    if not medicines:
        messagebox.showinfo("No Reminders", "No scheduled medicines found.")
        return

    del_win = tk.Toplevel(root)
    del_win.title("Delete Medicines")
    del_win.geometry("350x300")

    lbl = tk.Label(del_win, text="Select medicine to delete", font=("Arial", 12))
    lbl.pack(pady=5)

    listbox = tk.Listbox(del_win, font=("Arial", 12))
    listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    for idx, (name, time_str) in enumerate(medicines):
        listbox.insert(idx, f"{name} at {time_str}")

    def on_delete(event):
        selection = listbox.curselection()
        if not selection:
            return
        index = selection[0]
        name, time_str = medicines[index]

        confirm = messagebox.askyesno("Confirm Delete", f"Delete reminder for {name} at {time_str}?")
        if confirm:
            medicines.pop(index)
            save_medicines(medicines)
            messagebox.showinfo("Deleted", "Reminder deleted successfully.")
            del_win.destroy()
            delete_medicines_only()

    listbox.bind("<<ListboxSelect>>", on_delete)

# --------------------- GUI ---------------------
root = tk.Tk()
root.title("Medicine Reminder App")
root.geometry("400x500")

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

# New Feature Buttons
view_button = tk.Button(root, text="View Medicines", command=view_medicines_only, font=("Arial", 12), bg="lightblue")
view_button.pack(pady=5)

edit_button = tk.Button(root, text="Edit Medicines", command=edit_medicines_only, font=("Arial", 12), bg="khaki")
edit_button.pack(pady=5)

delete_button = tk.Button(root, text="Delete Medicines", command=delete_medicines_only, font=("Arial", 12), bg="salmon")
delete_button.pack(pady=5)

note = tk.Label(root, text="(Keep the app running for reminders!)", font=("Arial", 10), fg="red")
note.pack(pady=10)

# Start background scheduler thread
t = threading.Thread(target=run_schedule)
t.daemon = True
t.start()

root.mainloop()