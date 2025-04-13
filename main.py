import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import os

class Task:
    def __init__(self, description, priority="Medium", due_date=None, completed=False):
        self.description = description
        self.priority = priority
        self.due_date = due_date
        self.completed = completed
        self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return {
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "completed": self.completed,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        task = cls(data["description"], data["priority"], data["due_date"], data["completed"])
        task.created_at = data["created_at"]
        return task

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.tasks = []
        self.selected_task_index = None
        self.current_filter = "All"
        
        # Set up the main window
        self.root.title("Professional Task Manager")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Set theme
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure styles
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0", font=("Arial", 11))
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 16, "bold"))
        self.style.configure("Sidebar.TFrame", background="#e0e0e0")
        
        # Create menu
        self.create_menu()
        
        # Create main layout frames
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        self.sidebar_frame = ttk.Frame(self.main_frame, style="Sidebar.TFrame", width=150)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # Create content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create UI components
        self.create_sidebar()
        self.create_task_list()
        self.create_task_form()
        self.create_status_bar()
        
        # Set up event bindings
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)
        root.bind("<F5>", lambda event: self.refresh_task_list())
        
        # Initialize
        self.load_tasks()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_tasks)
        file_menu.add_command(label="Open", command=self.load_tasks_from_file)
        file_menu.add_command(label="Save", command=self.save_tasks)
        file_menu.add_command(label="Save As", command=self.save_tasks_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add Task", command=self.show_add_task)
        edit_menu.add_command(label="Edit Task", command=self.edit_task)
        edit_menu.add_command(label="Delete Task", command=self.delete_task)
        edit_menu.add_separator()
        edit_menu.add_command(label="Mark as Completed", command=lambda: self.toggle_task_status(True))
        edit_menu.add_command(label="Mark as Incomplete", command=lambda: self.toggle_task_status(False))
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Refresh", command=self.refresh_task_list)
        view_menu.add_separator()
        view_menu.add_command(label="Filter by Priority", command=self.show_priority_filter)
        view_menu.add_command(label="Filter by Status", command=self.show_status_filter)
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)

    def create_sidebar(self):
        # Header
        header_label = ttk.Label(self.sidebar_frame, text="Filters", style="Header.TLabel")
        header_label.pack(pady=10)
        
        # Filters
        ttk.Button(self.sidebar_frame, text="All Tasks", width=18, 
                  command=lambda: self.filter_tasks("All")).pack(pady=5)
        ttk.Button(self.sidebar_frame, text="High Priority", width=18,
                  command=lambda: self.filter_tasks("High")).pack(pady=5)
        ttk.Button(self.sidebar_frame, text="Medium Priority", width=18,
                  command=lambda: self.filter_tasks("Medium")).pack(pady=5)
        ttk.Button(self.sidebar_frame, text="Low Priority", width=18,
                  command=lambda: self.filter_tasks("Low")).pack(pady=5)
        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Button(self.sidebar_frame, text="Completed", width=18,
                  command=lambda: self.filter_tasks("Completed")).pack(pady=5)
        ttk.Button(self.sidebar_frame, text="Incomplete", width=18,
                  command=lambda: self.filter_tasks("Incomplete")).pack(pady=5)
        ttk.Separator(self.sidebar_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Actions
        ttk.Button(self.sidebar_frame, text="Add Task", width=18,
                  command=self.show_add_task).pack(pady=5)
        ttk.Button(self.sidebar_frame, text="Delete Task", width=18,
                  command=self.delete_task).pack(pady=5)

    def create_task_list(self):
        list_frame = ttk.Frame(self.content_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(list_frame)
        header_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(header_frame, text="Task List", style="Header.TLabel").pack(side=tk.LEFT)
        
        search_frame = ttk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode: self.filter_tasks(self.current_filter))
        ttk.Entry(search_frame, textvariable=self.search_var, width=20).pack(side=tk.LEFT, padx=5)
        
        # Task treeview
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.task_tree = ttk.Treeview(tree_frame, columns=("Description", "Priority", "Due Date", "Status"))
        self.task_tree.heading("#0", text="ID")
        self.task_tree.heading("Description", text="Description")
        self.task_tree.heading("Priority", text="Priority")
        self.task_tree.heading("Due Date", text="Due Date")
        self.task_tree.heading("Status", text="Status")
        
        self.task_tree.column("#0", width=50, stretch=tk.NO)
        self.task_tree.column("Description", width=300, stretch=tk.YES)
        self.task_tree.column("Priority", width=100, stretch=tk.NO)
        self.task_tree.column("Due Date", width=100, stretch=tk.NO)
        self.task_tree.column("Status", width=100, stretch=tk.NO)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        
        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_task_form(self):
        self.form_frame = ttk.Frame(self.content_frame)
        self.form_frame.pack(fill=tk.X, pady=10)
        
        # Form fields
        form_left = ttk.Frame(self.form_frame)
        form_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        form_right = ttk.Frame(self.form_frame)
        form_right.pack(side=tk.RIGHT, padx=10)
        
        # Description field
        ttk.Label(form_left, text="Task Description:").pack(anchor=tk.W, pady=(0, 5))
        self.description_var = tk.StringVar()
        ttk.Entry(form_left, textvariable=self.description_var, width=50).pack(fill=tk.X, pady=(0, 10))
        
        # Priority and due date
        subform = ttk.Frame(form_left)
        subform.pack(fill=tk.X)
        
        # Priority dropdown
        priority_frame = ttk.Frame(subform)
        priority_frame.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(priority_frame, text="Priority:").pack(anchor=tk.W)
        self.priority_var = tk.StringVar(value="Medium")
        priority_dropdown = ttk.Combobox(priority_frame, textvariable=self.priority_var, 
                                     values=["High", "Medium", "Low"], width=15)
        priority_dropdown.pack(pady=5)
        
        # Due date field
        due_date_frame = ttk.Frame(subform)
        due_date_frame.pack(side=tk.LEFT)
        ttk.Label(due_date_frame, text="Due Date (YYYY-MM-DD):").pack(anchor=tk.W)
        self.due_date_var = tk.StringVar()
        ttk.Entry(due_date_frame, textvariable=self.due_date_var, width=15).pack(pady=5)
        
        # Form buttons
        ttk.Button(form_right, text="Add Task", command=self.add_task).pack(pady=5)
        ttk.Button(form_right, text="Update Task", command=self.update_task).pack(pady=5)
        ttk.Button(form_right, text="Clear Form", command=self.clear_form).pack(pady=5)

    def create_status_bar(self):
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Separator(status_frame, orient=tk.HORIZONTAL).pack(fill=tk.X)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.task_count_var = tk.StringVar()
        self.task_count_var.set("Tasks: 0")
        count_label = ttk.Label(status_frame, textvariable=self.task_count_var)
        count_label.pack(side=tk.RIGHT, padx=5, pady=2)

    def add_task(self):
        description = self.description_var.get().strip()
        if not description:
            messagebox.showerror("Error", "Please enter a task description")
            return
        
        priority = self.priority_var.get()
        due_date = self.due_date_var.get() if self.due_date_var.get().strip() else None
        
        # Validate due date format if provided
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
        
        # Create and add the task
        task = Task(description, priority, due_date)
        self.tasks.append(task)
        
        # Update UI
        self.clear_form()
        self.refresh_task_list()
        self.set_status(f"Task '{description}' added successfully")

    def show_add_task(self):
        self.clear_form()
        self.description_var.set("")
        self.priority_var.set("Medium")
        self.due_date_var.set("")
        self.selected_task_index = None

    def on_task_select(self, event):
        selection = self.task_tree.selection()
        if selection:
            item_id = selection[0]
            task_index = int(self.task_tree.item(item_id)["text"]) - 1
            
            if 0 <= task_index < len(self.tasks):
                self.selected_task_index = task_index
                task = self.tasks[task_index]
                
                # Update form with selected task
                self.description_var.set(task.description)
                self.priority_var.set(task.priority)
                self.due_date_var.set(task.due_date if task.due_date else "")

    def edit_task(self):
        if self.selected_task_index is None:
            messagebox.showinfo("Info", "Please select a task to edit")
            return
        
        # Just populate the form for editing
        task = self.tasks[self.selected_task_index]
        self.description_var.set(task.description)
        self.priority_var.set(task.priority)
        self.due_date_var.set(task.due_date if task.due_date else "")

    def update_task(self):
        if self.selected_task_index is None:
            messagebox.showinfo("Info", "Please select a task to update")
            return
        
        description = self.description_var.get().strip()
        if not description:
            messagebox.showerror("Error", "Please enter a task description")
            return
        
        priority = self.priority_var.get()
        due_date = self.due_date_var.get() if self.due_date_var.get().strip() else None
        
        # Validate due date format if provided
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
        
        # Update the task
        task = self.tasks[self.selected_task_index]
        task.description = description
        task.priority = priority
        task.due_date = due_date
        
        # Update UI
        self.clear_form()
        self.refresh_task_list()
        self.set_status(f"Task '{description}' updated successfully")

    def delete_task(self):
        if self.selected_task_index is None:
            messagebox.showinfo("Info", "Please select a task to delete")
            return
        
        task = self.tasks[self.selected_task_index]
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete the task '{task.description}'?")
        
        if confirm:
            del self.tasks[self.selected_task_index]
            self.clear_form()
            self.selected_task_index = None
            self.refresh_task_list()
            self.set_status("Task deleted successfully")

    def toggle_task_status(self, completed):
        if self.selected_task_index is None:
            messagebox.showinfo("Info", "Please select a task to update")
            return
        
        task = self.tasks[self.selected_task_index]
        task.completed = completed
        
        self.refresh_task_list()
        status_text = "completed" if completed else "marked as incomplete"
        self.set_status(f"Task '{task.description}' {status_text}")

    def filter_tasks(self, filter_type):
        self.current_filter = filter_type
        self.refresh_task_list()

    def show_priority_filter(self):
        filter_window = tk.Toplevel(self.root)
        filter_window.title("Filter by Priority")
        filter_window.geometry("300x200")
        filter_window.resizable(False, False)
        filter_window.transient(self.root)
        
        ttk.Label(filter_window, text="Select Priority Filter:").pack(pady=10)
        
        selected_filter = tk.StringVar(value=self.current_filter)
        
        ttk.Radiobutton(filter_window, text="All Tasks", variable=selected_filter, 
                       value="All").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(filter_window, text="High Priority", variable=selected_filter, 
                       value="High").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(filter_window, text="Medium Priority", variable=selected_filter, 
                       value="Medium").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(filter_window, text="Low Priority", variable=selected_filter, 
                       value="Low").pack(anchor=tk.W, padx=20, pady=5)
        
        ttk.Button(filter_window, text="Apply", 
                  command=lambda: [self.filter_tasks(selected_filter.get()), filter_window.destroy()]).pack(pady=10)

    def show_status_filter(self):
        filter_window = tk.Toplevel(self.root)
        filter_window.title("Filter by Status")
        filter_window.geometry("300x150")
        filter_window.resizable(False, False)
        filter_window.transient(self.root)
        
        ttk.Label(filter_window, text="Select Status Filter:").pack(pady=10)
        
        selected_filter = tk.StringVar(value=self.current_filter)
        
        ttk.Radiobutton(filter_window, text="All Tasks", variable=selected_filter, 
                       value="All").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(filter_window, text="Completed", variable=selected_filter, 
                       value="Completed").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(filter_window, text="Incomplete", variable=selected_filter, 
                       value="Incomplete").pack(anchor=tk.W, padx=20, pady=5)
        
        ttk.Button(filter_window, text="Apply", 
                  command=lambda: [self.filter_tasks(selected_filter.get()), filter_window.destroy()]).pack(pady=10)

    def clear_form(self):
        self.description_var.set("")
        self.priority_var.set("Medium")
        self.due_date_var.set("")
        self.selected_task_index = None

    def refresh_task_list(self):
        # Clear current items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Filter tasks based on current filter
        filtered_tasks = self.tasks
        search_term = self.search_var.get().lower()
        
        if self.current_filter == "High":
            filtered_tasks = [t for t in filtered_tasks if t.priority == "High"]
        elif self.current_filter == "Medium":
            filtered_tasks = [t for t in filtered_tasks if t.priority == "Medium"]
        elif self.current_filter == "Low":
            filtered_tasks = [t for t in filtered_tasks if t.priority == "Low"]
        elif self.current_filter == "Completed":
            filtered_tasks = [t for t in filtered_tasks if t.completed]
        elif self.current_filter == "Incomplete":
            filtered_tasks = [t for t in filtered_tasks if not t.completed]
        
        # Apply search filter if search term exists
        if search_term:
            filtered_tasks = [t for t in filtered_tasks if search_term in t.description.lower()]
        
        # Populate tree
        for i, task in enumerate(filtered_tasks):
            item_id = self.task_tree.insert("", tk.END, text=str(self.tasks.index(task) + 1),
                                          values=(task.description, 
                                                 task.priority,
                                                 task.due_date if task.due_date else "Not set",
                                                 "Completed" if task.completed else "Pending"))
            
            # Apply color based on priority
            if task.priority == "High":
                self.task_tree.item(item_id, tags=("high",))
            elif task.priority == "Low":
                self.task_tree.item(item_id, tags=("low",))
                
            # Apply style for completed tasks
            if task.completed:
                self.task_tree.item(item_id, tags=("completed",))
        
        # Configure tags
        self.task_tree.tag_configure("high", background="#ffe6e6")
        self.task_tree.tag_configure("low", background="#e6ffe6")
        self.task_tree.tag_configure("completed", foreground="gray")
        
        # Update status bar
        self.task_count_var.set(f"Tasks: {len(self.tasks)} (Showing: {len(filtered_tasks)})")

    def save_tasks(self):
        if not hasattr(self, 'current_file'):
            self.save_tasks_as()
            return
        
        try:
            self.save_to_file(self.current_file)
            self.set_status(f"Tasks saved to {self.current_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving tasks: {e}")

    def save_tasks_as(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.save_to_file(filename)
                self.current_file = filename
                self.set_status(f"Tasks saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving tasks: {e}")

    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            data = [task.to_dict() for task in self.tasks]
            json.dump(data, file, indent=2)

    def load_tasks(self):
        # Check for default save file
        default_file = "tasks.json"
        if os.path.exists(default_file):
            self.load_from_file(default_file)
            self.current_file = default_file

    def load_tasks_from_file(self):
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.load_from_file(filename)
                self.current_file = filename
                self.set_status(f"Tasks loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading tasks: {e}")

    def load_from_file(self, filename):
        with open(filename, 'r') as file:
            data = json.load(file)
            self.tasks = [Task.from_dict(item) for item in data]
            self.refresh_task_list()

    def new_tasks(self):
        if self.tasks:
            confirm = messagebox.askyesno("Confirm New", 
                                        "This will clear all current tasks. Continue?")
            if not confirm:
                return
        
        self.tasks = []
        self.clear_form()
        self.refresh_task_list()
        self.set_status("New task list created")

    def set_status(self, message):
        self.status_var.set(message)

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Task Manager")
        about_window.geometry("400x250")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        
        ttk.Label(about_window, text="Professional Task Manager", 
                 font=("Arial", 16, "bold")).pack(pady=10)
        ttk.Label(about_window, text="Version 1.0").pack()
        ttk.Label(about_window, text="A professional task management application").pack(pady=5)
        ttk.Label(about_window, text="© 2023 Harsh Rokade ").pack(pady=10)
        ttk.Button(about_window, text="OK", command=about_window.destroy).pack(pady=10)


def main():
    root = tk.Tk()
    root.title("Professional Task Manager")
    
    # Set icon if available
    try:
        root.iconbitmap("taskicon.ico")
    except:
        pass
    
    app = TaskManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()