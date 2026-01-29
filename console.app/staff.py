print("---КАДРОВЫЙ УЧЕТ---")
company = []
POSITIONS = ["Менеджер", "Разработчик", "Дизайнер", "Аналитик", "Тестировщик", "Администратор"]


def add_staff(name, position=None):
    if not name:
        return False

    if position is None:
        print("Доступные должности:")
        for i, p in enumerate(POSITIONS, 1):
            print(f"{i}. {p}")

        try:
            choice1 = int(input("\nВыберите номер: "))
            position = POSITIONS[choice1 - 1]
        except (ValueError, IndexError):
            return False
    elif position not in POSITIONS:
        return False

    company.append({"name": name, "position": position})
    return True


def delete_staff():
    for i, people in enumerate(company):
        if people["name"] == name:
            removed = company.pop(i)
            print(f"Удален сотрудник - {removed['name']}")
            return
    print("Сотрудник не найден")


def edit_positions():
    print("\n".join(f"{i + 1}. {p}" for i, p in enumerate(POSITIONS)))

    try:
        idx = int(input("Номер для изменения: ")) - 1
        if 0 <= idx < len(POSITIONS):
            new_name = input("Новое название: ").strip()
            if new_name:
                POSITIONS[idx] = new_name
                print(f"Изменено!")
    except:
        pass


def assign_salary():
    print("\nСотрудники:")
    for i, emp in enumerate(company, 1):
        salary = emp.get("salary", "не назначен")
        print(f"{i}. {emp['name']} ({emp['position']}): {salary}")

    try:
        idx = int(input("\nНомер сотрудника: ")) - 1
        if 0 <= idx < len(company):
            emp = company[idx]

            # Если оклада нет - назначаем, если есть - спрашиваем действие
            if "salary" not in emp:
                salary = int(input("Оклад: "))
                emp["salary"] = salary
                print(f"Назначено: {salary} руб.")
            else:
                percent = float(input("Процент (+/-): "))
                old = emp["salary"]
                emp["salary"] = int(old * (1 + percent / 100))
                print(f"{old} → {emp['salary']} руб.")
            return company
    except:
        print("Ошибка")


def show_staff():
    if not company:
        print("В штате нет сотрудников")
    else:
        for i, people in enumerate(company, 1):
            print(f"{i}. {people['name']} ({people['position']}): {people['salary']} руб.")


if __name__ == "__main__":
    while True:
        print("\n1. Добавить сотрудника")
        print("\n2. Удалить сотрудника")
        print("\n3. Назначить оклад")
        print("\n4. Показать штат")
        print("\n5. Редактировать должности")
        print("\n6. Выйти\n")

        choice = int(input("Выберите действие: "))

        if choice == 1:
            name = input("Введите имя сотрудника: ")
            if add_staff(name):
                print("Сотрудник добавлен")
            else:
                print("Ошибка: пустые поля")

        elif choice == 2:
            name = input("Введите имя сотрудника: ")
            delete_staff()

        elif choice == 3:
            assign_salary()

        elif choice == 4:
            show_staff()

        elif choice == 5:
            edit_positions()
            print(f"Должности: {POSITIONS}")

        elif choice == 6:
            break

        else:
            print("Неверный выбор")
