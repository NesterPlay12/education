import tkinter as tk
from tkinter import messagebox, filedialog
import json
import os


class NotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Простой блокнот")
        self.root.geometry("600x400")

        # Список для хранения заметок
        self.notes = []
        self.current_note_index = -1

        # Создание интерфейса
        self.create_widgets()

    def create_widgets(self):
        # Фрейм для кнопок
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        # Кнопки управления
        tk.Button(button_frame, text="Новая заметка", command=self.new_note, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Сохранить", command=self.save_note, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Удалить", command=self.delete_note, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Сохранить в файл", command=self.save_to_file, width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Загрузить из файла", command=self.load_from_file, width=15).pack(side=tk.LEFT,
                                                                                                       padx=5)

        # Фрейм для списка заметок и текстового поля
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Список заметок
        self.notes_listbox = tk.Listbox(main_frame, width=25)
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.notes_listbox.bind('<<ListboxSelect>>', self.on_note_select)

        # Полоса прокрутки для списка
        scrollbar = tk.Scrollbar(main_frame)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.notes_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.notes_listbox.yview)

        # Фрейм для текстового поля
        text_frame = tk.Frame(main_frame)
        text_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Заголовок заметки
        tk.Label(text_frame, text="Заголовок:").pack(anchor=tk.W)
        self.title_entry = tk.Entry(text_frame)
        self.title_entry.pack(fill=tk.X, pady=(0, 10))

        # Текстовое поле для заметки
        tk.Label(text_frame, text="Текст заметки:").pack(anchor=tk.W)

        text_scrollbar = tk.Scrollbar(text_frame)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area = tk.Text(text_frame, height=15, yscrollcommand=text_scrollbar.set)
        self.text_area.pack(fill=tk.BOTH, expand=True)

        text_scrollbar.config(command=self.text_area.yview)

    def new_note(self):
        """Создание новой заметки"""
        self.current_note_index = -1
        self.title_entry.delete(0, tk.END)
        self.text_area.delete(1.0, tk.END)
        self.title_entry.insert(0, "Новая заметка")

    def save_note(self):
        """Сохранение текущей заметки"""
        title = self.title_entry.get()
        content = self.text_area.get(1.0, tk.END)

        if not title.strip():
            messagebox.showwarning("Внимание", "Введите заголовок заметки")
            return

        if self.current_note_index == -1:
            # Новая заметка
            self.notes.append({"title": title, "content": content})
            self.notes_listbox.insert(tk.END, title)
        else:
            # Обновление существующей заметки
            self.notes[self.current_note_index] = {"title": title, "content": content}
            self.notes_listbox.delete(self.current_note_index)
            self.notes_listbox.insert(self.current_note_index, title)
            self.notes_listbox.selection_set(self.current_note_index)

        messagebox.showinfo("Успех", "Заметка сохранена")

    def delete_note(self):
        """Удаление выбранной заметки"""
        if self.current_note_index == -1:
            messagebox.showwarning("Внимание", "Выберите заметку для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную заметку?"):
            self.notes.pop(self.current_note_index)
            self.notes_listbox.delete(self.current_note_index)
            self.new_note()

    def on_note_select(self, event):
        """Обработка выбора заметки из списка"""
        if not self.notes_listbox.curselection():
            return

        index = self.notes_listbox.curselection()[0]
        self.current_note_index = index

        note = self.notes[index]
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, note["title"])

        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, note["content"])

    def save_to_file(self):
        """Сохранение всех заметок в файл"""
        if not self.notes:
            messagebox.showwarning("Внимание", "Нет заметок для сохранения")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(self.notes, file, ensure_ascii=False, indent=2)
                messagebox.showinfo("Успех", f"Заметки сохранены в файл:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def load_from_file(self):
        """Загрузка заметок из файла"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    self.notes = json.load(file)

                # Обновление списка
                self.notes_listbox.delete(0, tk.END)
                for note in self.notes:
                    self.notes_listbox.insert(tk.END, note["title"])

                self.new_note()
                messagebox.showinfo("Успех", f"Заметки загружены из файла:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")


def main():
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

if file_path and os.path.exists(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            self.notes = json.load(file)

        # Обновление списка
        self.notes_listbox.delete(0, tk.END)
        for note in self.notes:
            self.notes_listbox.insert(tk.END, note["title"])

        self.new_note()
        messagebox.showinfo("Успех", f"Заметки загружены из файла:\n{file_path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{str(e)}")


def main():
    root = tk.Tk()
    app = NotesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
