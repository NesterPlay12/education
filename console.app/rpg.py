# Импортируем модуль random для случайных чисел
import random
import time


# === БАЗОВЫЙ КЛАСС (РОДИТЕЛЬ) ===
class Character:
    """
    Базовый класс для всех персонажей в игре
    Содержит общие свойства и методы
    """

    def __init__(self, name, health, power):
        """
        Конструктор класса - вызывается при создании персонажа
        self - ссылка на сам объект (обязательный параметр)
        name - имя персонажа
        health - здоровье
        power - сила удара
        """
        self.name = name  # Атрибут: имя
        self.health = health  # Атрибут: здоровье
        self.power = power  # Атрибут: сила
        self.max_health = health  # Запоминаем максимальное здоровье

    def attack(self, enemy):
        """
        Метод атаки - один персонаж атакует другого
        enemy - противник (объект класса Character)
        """
        # Наносим урон от 50% до 100% от силы
        damage = random.randint(int(self.power * 0.5), self.power)

        # Уменьшаем здоровье противника
        enemy.health -= damage

        # Выводим информацию об атаке
        print(f"⚔️ {self.name} атакует {enemy.name} и наносит {damage} урона!")
        print(f"💚 У {enemy.name} осталось {enemy.health} здоровья")

        # Проверяем, не умер ли противник
        if enemy.health <= 0:
            print(f"💀 {enemy.name} погиб!")
            return True  # Возвращаем True, если противник мертв
        return False  # Противник жив

    def is_alive(self):
        """
        Проверяет, жив ли персонаж
        Возвращает True если здоровье > 0
        """
        return self.health > 0

    def show_stats(self):
        """
        Показывает характеристики персонажа
        """
        print(f"\n=== {self.name} ===")
        print(f"❤️ Здоровье: {self.health}/{self.max_health}")
        print(f"⚔️ Сила: {self.power}")


# === КЛАСС ДЛЯ ПРЕДМЕТОВ ===
class Item:
    """
    Класс для предметов в игре
    """

    def __init__(self, name, type, value, price):
        """
        Создание предмета
        name - название предмета
        type - тип (heal, power, defense)
        value - сила эффекта
        price - цена в магазине
        """
        self.name = name
        self.type = type
        self.value = value
        self.price = price

    def use(self, player):
        """
        Использовать предмет на игроке
        """
        if self.type == "heal":
            if self.value == "full":
                player.health = player.max_health
                print(f"💚 {self.name}: здоровье полностью восстановлено!")
            else:
                player.health = min(player.health + self.value, player.max_health)
                print(f"💚 {self.name}: восстановлено {self.value} здоровья!")

        elif self.type == "power":
            # Временное усиление будет обрабатываться в битве
            player.temp_power = self.value
            player.power_boost_turns = 3
            print(f"⚔️ {self.name}: сила увеличена на {self.value} на 3 боя!")

        elif self.type == "defense":
            player.temp_defense = self.value
            player.defense_boost_turns = 3
            print(f"🛡️ {self.name}: защита увеличена на {self.value} на 3 хода!")

    def __str__(self):
        return f"{self.name} (💰 {self.price})"


# === КЛАСС ДЛЯ ДОСТИЖЕНИЙ ===
class Achievement:
    """
    Класс для системы достижений
    """

    def __init__(self, name, description, condition_func):
        self.name = name
        self.description = description
        self.condition_func = condition_func  # Функция проверки
        self.unlocked = False

    def check(self, player):
        """
        Проверить, выполнено ли условие
        """
        if not self.unlocked and self.condition_func(player):
            self.unlocked = True
            return True
        return False

    def __str__(self):
        status = "✅" if self.unlocked else "❌"
        return f"{status} {self.name}: {self.description}"


# === КЛАСС ДЛЯ КВЕСТОВ ===
class Quest:
    """
    Класс для системы квестов
    """

    def __init__(self, name, description, goal_type, goal_amount, reward_gold, reward_exp, reward_item=None):
        self.name = name
        self.description = description
        self.goal_type = goal_type  # "kill", "collect", "level", "explore"
        self.goal_amount = goal_amount
        self.current_amount = 0
        self.reward_gold = reward_gold
        self.reward_exp = reward_exp
        self.reward_item = reward_item
        self.completed = False

    def update(self, event_type, amount=1):
        """
        Обновить прогресс квеста
        """
        if not self.completed and event_type == self.goal_type:
            self.current_amount = min(self.current_amount + amount, self.goal_amount)
            if self.current_amount >= self.goal_amount:
                self.completed = True
            return True
        return False

    def show_progress(self):
        """
        Показать прогресс квеста
        """
        status = "✅" if self.completed else f"{self.current_amount}/{self.goal_amount}"
        return f"{self.name}: {self.description} [{status}]"

    def get_reward(self, player):
        """
        Выдать награду за квест
        """
        if self.completed:
            player.gold += self.reward_gold
            player.gain_exp(self.reward_exp)

            if self.reward_item:
                player.inventory.append(self.reward_item)
                player.collected_items.add(self.reward_item.name)

            print(f"💰 Награда: {self.reward_gold} золота, {self.reward_exp} опыта")
            if self.reward_item:
                print(f"📦 Предмет: {self.reward_item.name}")

            return True
        return False


# === КЛАСС ДЛЯ ЗАКЛИНАНИЙ ===
class Spell:
    """
    Класс для системы магии
    """

    def __init__(self, name, mana_cost, effect_type, power, description):
        self.name = name
        self.mana_cost = mana_cost
        self.effect_type = effect_type  # "damage", "heal", "shield", "stun"
        self.power = power
        self.description = description

    def cast(self, caster, target):
        """
        Применить заклинание
        """
        if caster.mana < self.mana_cost:
            print(f"❌ Недостаточно маны! Нужно {self.mana_cost}")
            return False

        caster.mana -= self.mana_cost

        if self.effect_type == "damage":
            # Урон с учетом магической силы
            damage = self.power + caster.magic_power
            target.health -= damage
            print(f"🔥 {self.name}! Нанесено {damage} урона!")

        elif self.effect_type == "heal":
            heal_amount = self.power + caster.magic_power
            caster.health = min(caster.health + heal_amount, caster.max_health)
            print(f"💚 {self.name}! Восстановлено {heal_amount} здоровья!")

        elif self.effect_type == "shield":
            caster.shield_turns = self.power
            print(f"🛡️ {self.name}! Защита на {self.power} ходов!")

        elif self.effect_type == "stun":
            damage = self.power
            target.health -= damage
            target.stunned = True
            print(f"⚡ {self.name}! Нанесено {damage} урона и оглушение!")

        return True

    def __str__(self):
        return f"{self.name} (мана: {self.mana_cost}) - {self.description}"


# === КЛАСС ДЛЯ СПУТНИКОВ ===
class Companion:
    """
    Класс для спутников, помогающих в бою
    """

    def __init__(self, name, type, level):
        """
        Создание спутника
        """
        self.name = name
        self.type = type
        self.level = level
        self.exp = 0

        # Характеристики зависят от типа
        if type == "warrior":
            self.power = 10 + level * 3
            self.health = 50 + level * 10
        elif type == "healer":
            self.power = 5 + level * 2
            self.health = 40 + level * 8
        elif type == "thief":
            self.power = 8 + level * 2
            self.health = 30 + level * 5

    def action(self, player, enemy):
        """
        Действие спутника в бою
        """
        if self.type == "warrior":
            # Воин атакует врага
            damage = random.randint(int(self.power * 0.5), self.power)
            enemy.health -= damage
            print(f"⚔️ Спутник {self.name} атакует и наносит {damage} урона!")

        elif self.type == "healer":
            # Целитель лечит игрока
            heal_amount = random.randint(5, 15) * self.level
            player.health = min(player.health + heal_amount, player.max_health)
            print(f"💚 Спутник {self.name} лечит вас на {heal_amount} здоровья!")

        elif self.type == "thief":
            # Вор пытается украсть золото
            if random.random() > 0.5:
                stolen = random.randint(5, 20) * self.level
                player.gold += stolen
                print(f"💰 Спутник {self.name} нашел {stolen} золота!")

    def gain_exp(self, amount):
        """
        Получение опыта спутником
        """
        self.exp += amount
        if self.exp >= 50 * self.level:
            self.level_up()

    def level_up(self):
        """
        Повышение уровня спутника
        """
        self.level += 1
        self.exp = 0

        if self.type == "warrior":
            self.power += 5
            self.health += 20
        elif self.type == "healer":
            self.power += 3
            self.health += 15
        elif self.type == "thief":
            self.power += 4
            self.health += 10

        print(f"✨ Спутник {self.name} повысил уровень до {self.level}!")


# === КЛАСС ДЛЯ СУНДУКОВ ===
class Chest:
    """
    Класс для сундуков с сокровищами
    """

    def __init__(self, player_level):
        """
        Создание сундука в зависимости от уровня игрока
        """
        # Типы сундуков
        chest_types = [
            {"name": "📦 Маленький сундук", "gold": random.randint(10, 30), "items": ["small_potion"]},
            {"name": "💰 Средний сундук", "gold": random.randint(30, 70), "items": ["potion", "small_potion"]},
            {"name": "💎 Большой сундук", "gold": random.randint(70, 150),
             "items": ["potion", "power_potion", "defense_potion"]}
        ]

        # Выбираем тип сундука с разной вероятностью
        rand = random.random()
        if rand < 0.5:  # 50% маленький
            chest_data = chest_types[0]
        elif rand < 0.8:  # 30% средний
            chest_data = chest_types[1]
        else:  # 20% большой
            chest_data = chest_types[2]

        self.name = chest_data["name"]
        self.gold = int(chest_data["gold"] * (1 + (player_level - 1) * 0.2))

        # Создаем предметы в сундуке
        self.items = []
        for item_type in chest_data["items"]:
            if item_type == "small_potion":
                self.items.append(Item("Малое зелье лечения", "heal", 30, 25))
            elif item_type == "potion":
                self.items.append(Item("Большое зелье лечения", "heal", "full", 100))
            elif item_type == "power_potion":
                self.items.append(Item("Зелье силы", "power", 5, 50))
            elif item_type == "defense_potion":
                self.items.append(Item("Зелье защиты", "defense", 3, 40))

    def open(self, player):
        """
        Игрок открывает сундук
        """
        print(f"\n✨ Вы открываете {self.name}!")
        print(f"💰 Найдено золота: {self.gold}")
        player.gold += self.gold

        if self.items:
            print("📦 Найдены предметы:")
            for item in self.items:
                print(f"  - {item.name}")
                player.inventory.append(item)
                player.collected_items.add(item.name)
        else:
            print("📦 В сундуке больше ничего нет")


# === КЛАСС ДЛЯ ПОГОДЫ ===
class Weather:
    """
    Класс для системы погоды и времени суток
    """

    def __init__(self):
        """
        Создание случайной погоды
        """
        self.types = ["☀️ Ясно", "🌧️ Дождь", "🌫️ Туман", "🌙 Ночь"]
        self.current = random.choice(self.types)
        self.effect_multiplier = 1.0

    def apply_effects(self, attacker, defender):
        """
        Применить эффекты погоды к атаке
        Возвращает модификаторы для атаки и защиты
        """
        attack_mod = 1.0
        crit_mod = 1.0
        dodge_mod = 1.0

        if self.current == "🌧️ Дождь":
            crit_mod = 0.5  # Меньше шанс критического удара
            print("🌧️ Из-за дождя сложнее нанести критический удар!")

        elif self.current == "🌫️ Туман":
            attack_mod = 0.8  # Меньше точность
            print("🌫️ Туман снижает точность атак!")

        elif self.current == "🌙 Ночь":
            dodge_mod = 1.5  # Легче убежать
            print("🌙 В темноте легче скрыться...")

        return attack_mod, crit_mod, dodge_mod

    def change_weather(self):
        """
        Случайно меняем погоду
        """
        if random.random() < 0.3:  # 30% шанс смены погоды
            old_weather = self.current
            self.current = random.choice(self.types)
            print(f"🌤️ Погода изменилась: {old_weather} -> {self.current}")


# === КЛАСС-НАСЛЕДНИК (ИГРОК) ===
class Player(Character):
    """
    Класс игрока - наследует всё от Character
    Добавляет свои методы: лечение, прокачку, инвентарь
    """

    def __init__(self, name):
        """
        Создание игрока с начальными параметрами
        """
        # Вызываем конструктор родителя
        super().__init__(name, health=100, power=20)
        self.level = 1
        self.exp = 0
        self.gold = 50
        self.inventory = []
        self.energy = 100
        self.max_energy = 100
        self.companions = []
        self.achievements = []
        self.monsters_killed = 0
        self.battles_without_healing = 0
        self.max_battles_without_healing = 0
        self.collected_items = set()
        self.mana = 50
        self.max_mana = 50
        self.magic_power = 10
        self.spells = []
        self.shield_turns = 0
        self.stunned = False
        self.temp_power = 0
        self.power_boost_turns = 0
        self.temp_defense = 0
        self.defense_boost_turns = 0

    def heal(self):
        """
        Лечение игрока
        """
        if self.gold >= 30:
            self.health = self.max_health
            self.gold -= 30
            self.battles_without_healing = 0
            print(f"💚 Вы полечились! Здоровье восстановлено! Осталось золота: {self.gold}")
        else:
            print("❌ Недостаточно золота! Нужно 30")

    def gain_exp(self, amount):
        """
        Получение опыта и повышение уровня
        """
        self.exp += amount
        print(f"✨ Получено {amount} опыта!")

        if self.exp >= 100:
            self.level += 1
            self.exp = 0
            self.max_health += 30
            self.health = self.max_health
            self.power += 10
            self.max_energy += 20
            self.energy = self.max_energy
            self.max_mana += 15
            self.mana = self.max_mana
            self.magic_power += 5
            print(f"🎉 УРОВЕНЬ ПОВЫШЕН! Теперь {self.level} уровень!")
            print(f"❤️ Здоровье +30, ⚔️ Сила +10, ⚡ Энергия +20, 📚 Мана +15")

            for companion in self.companions:
                companion.gain_exp(20)

    def show_inventory(self):
        """
        Показывает инвентарь игрока
        """
        print(f"\n🎒 ИНВЕНТАРЬ")
        print(f"💰 Золото: {self.gold}")
        print(f"⚡ Энергия: {self.energy}/{self.max_energy}")
        print(f"📚 Мана: {self.mana}/{self.max_mana}")
        print(f"📊 Уровень: {self.level}")
        print(f"✨ Опыт: {self.exp}/100")

        if self.inventory:
            print("\n📦 Предметы:")
            for i, item in enumerate(self.inventory, 1):
                print(f"  {i}. {item}")
        else:
            print("\n📦 Предметов нет")

        if self.spells:
            print("\n📚 Заклинания:")
            for spell in self.spells:
                print(f"  {spell}")

        if self.companions:
            print("\n👥 Спутники:")
            for comp in self.companions:
                print(f"  {comp.name} ({comp.type}) - уровень {comp.level}")

    def use_item(self, item_index):
        """
        Использовать предмет из инвентаря
        """
        if 0 <= item_index < len(self.inventory):
            item = self.inventory[item_index]
            item.use(self)
            self.collected_items.add(item.name)
            self.inventory.pop(item_index)
            return True
        return False

    def show_battle_menu(self):
        """
        Показывает меню битвы с разными типами атак
        """
        print("\n⚔️ ВЫБЕРИТЕ ДЕЙСТВИЕ:")
        print("1. Обычная атака (100% урона, -10 энергии)")
        print("2. Сильная атака (150% урона, 70% точность, -25 энергии)")
        print("3. Защита (-50% получаемого урона, +10 энергии)")
        print("4. 🎒 Использовать предмет")
        print("5. 🏃 Убежать")

        if self.companions:
            print("6. 👥 Действие спутника")

    def attack_strong(self, enemy):
        """
        Сильная атака
        """
        if self.energy < 25:
            print("❌ Недостаточно энергии!")
            return False

        self.energy -= 25

        if random.random() > 0.7:
            print("❌ Сильная атака промахнулась!")
            return False

        power = self.power + self.temp_power
        damage = random.randint(int(power * 1.2), int(power * 1.5))
        enemy.health -= damage

        print(f"💥 СИЛЬНАЯ АТАКА! Нанесено {damage} урона!")

        if enemy.health <= 0:
            print(f"💀 {enemy.name} погиб!")
            return True
        return False

    def defend(self):
        """
        Защитная стойка
        """
        self.energy = min(self.energy + 10, self.max_energy)
        self.defense_boost_turns = 1
        print("🛡️ Вы встали в защитную стойку!")

    def learn_spell(self, spell):
        """
        Выучить новое заклинание
        """
        if spell not in self.spells:
            self.spells.append(spell)
            print(f"📚 Вы выучили заклинание: {spell.name}!")


# === КЛАСС-НАСЛЕДНИК (МОНСТР) ===
class Monster(Character):
    """
    Класс монстра - наследует от Character
    Монстры создаются случайными
    """

    def __init__(self, player_level):
        """
        Создание случайного монстра
        Сложность зависит от уровня игрока
        """
        monsters = [
            {"name": "👿 Гоблин", "health": 40, "power": 10},
            {"name": "🐺 Волк", "health": 60, "power": 15},
            {"name": "🧟 Скелет", "health": 80, "power": 20},
            {"name": "🐉 Орк", "health": 120, "power": 25},
            {"name": "👹 Огр", "health": 150, "power": 30}
        ]

        monster_data = random.choice(monsters)

        health_multiplier = 1 + (player_level - 1) * 0.5
        power_multiplier = 1 + (player_level - 1) * 0.3

        super().__init__(
            monster_data["name"],
            int(monster_data["health"] * health_multiplier),
            int(monster_data["power"] * power_multiplier)
        )

        self.reward_gold = int(20 * player_level)
        self.reward_exp = int(30 * player_level)
        self.stunned = False

    def show_reward(self):
        """
        Показывает награду за убийство монстра
        """
        print(f"💰 Награда: {self.reward_gold} золота, {self.reward_exp} опыта")


# === ОСНОВНАЯ ИГРА ===
class Game:
    """
    Класс управляющий игрой
    """

    def __init__(self):
        """
        Запуск новой игры
        """
        print("🎮 ДОБРО ПОЖАЛОВАТЬ В ИГРУ!")
        print("=" * 40)

        name = input("Введите имя вашего героя: ")
        self.player = Player(name)

        self.weather = Weather()

        self.shop_items = [
            Item("Малое зелье лечения", "heal", 30, 25),
            Item("Большое зелье лечения", "heal", "full", 100),
            Item("Зелье силы", "power", 5, 50),
            Item("Зелье защиты", "defense", 3, 40)
        ]

        self.setup_achievements()
        self.setup_quests()
        self.setup_spells()

        self.running = True
        self.enemy = None

    def setup_achievements(self):
        """
        Создание всех достижений
        """
        achievements = [
            Achievement(
                "Первый уровень",
                "Достигнуть 2 уровня",
                lambda p: p.level >= 2
            ),
            Achievement(
                "Охотник",
                "Убить 10 монстров",
                lambda p: p.monsters_killed >= 10
            ),
            Achievement(
                "Богач",
                "Накопить 500 золота",
                lambda p: p.gold >= 500
            ),
            Achievement(
                "Бессмертный",
                "Победить 5 врагов без лечения",
                lambda p: p.max_battles_without_healing >= 5
            ),
            Achievement(
                "Коллекционер",
                "Собрать все виды предметов",
                lambda p: len(p.collected_items) >= 8
            ),
            Achievement(
                "Мастер магии",
                "Выучить все заклинания",
                lambda p: len(p.spells) >= 4
            ),
            Achievement(
                "Герой",
                "Достигнуть 5 уровня",
                lambda p: p.level >= 5
            ),
            Achievement(
                "Миллионер",
                "Накопить 1000 золота",
                lambda p: p.gold >= 1000
            )
        ]

        for achievement in achievements:
            self.player.achievements.append(achievement)

    def setup_quests(self):
        """
        Создание всех доступных квестов
        """
        self.available_quests = [
            Quest(
                "Истребитель гоблинов",
                "Убить 5 гоблинов",
                "kill_goblin",
                5,
                100,
                50
            ),
            Quest(
                "Охотник на волков",
                "Убить 3 волков",
                "kill_wolf",
                3,
                150,
                80
            ),
            Quest(
                "Коллекционер зелий",
                "Собрать 3 малых зелья лечения",
                "collect_small_potion",
                3,
                80,
                40,
                Item("Малое зелье лечения", "heal", 30, 25)
            ),
            Quest(
                "Путь героя",
                "Достичь 3 уровня",
                "level",
                3,
                200,
                150
            ),
            Quest(
                "Богатство",
                "Накопить 300 золота",
                "gold",
                300,
                100,
                100
            )
        ]

        self.active_quests = []
        self.completed_quests = []

    def setup_spells(self):
        """
        Создание всех заклинаний
        """
        self.available_spells = [
            Spell("Огненный шар", 20, "damage", 25, "Наносит сильный урон одному врагу"),
            Spell("Лечение", 15, "heal", 30, "Восстанавливает здоровье"),
            Spell("Магический щит", 25, "shield", 3, "Уменьшает получаемый урон на 3 хода"),
            Spell("Молния", 30, "stun", 20, "Наносит урон и оглушает врага")
        ]

    def show_menu(self):
        """
        Показывает главное меню
        """
        print(f"\n🌤️ Текущая погода: {self.weather.current}")
        print("=" * 40)
        print("ГЛАВНОЕ МЕНЮ:")
        print("1. ⚔️ Найти врага")
        print("2. 💚 Полечиться")
        print("3. 📊 Мои характеристики")
        print("4. 🎒 Инвентарь")
        print("5. 🏪 Магазин предметов")
        print("6. 📚 Магазин заклинаний")
        print("7. 👥 Нанять спутника")
        print("8. 📋 Квесты")
        print("9. 🏆 Достижения")
        print("10. 🚪 Выйти из игры")
        print("=" * 40)

        return input("Выберите действие: ")

    def find_enemy(self):
        """
        Поиск случайного врага или сундука
        """
        print("\n🔍 Вы ищете врага...")
        time.sleep(1)

        if random.random() < 0.3:
            self.find_chest()
            return

        self.enemy = Monster(self.player.level)
        print(f"\n👾 Вы встретили {self.enemy.name}!")
        self.enemy.show_stats()
        self.enemy.show_reward()

        self.battle()

    def find_chest(self):
        """
        Найти сундук с сокровищами
        """
        chest = Chest(self.player.level)
        print(f"\n💎 Вы нашли {chest.name}!")

        print("\n1. 📦 Открыть сундук")
        print("2. 🚶 Пройти мимо")

        choice = input("Выберите действие: ")

        if choice == "1":
            chest.open(self.player)
            self.check_achievements()
        else:
            print("Вы решили не открывать сундук и пошли дальше...")

    def battle(self):
        """
        Боевая система с разными атаками, магией и погодой
        """
        print("\n⚔️ БИТВА НАЧАЛАСЬ!")
        print(f"🌤️ Погода: {self.weather.current}")

        while self.player.is_alive() and self.enemy.is_alive():
            if hasattr(self.enemy, 'stunned') and self.enemy.stunned:
                print("⚡ Враг оглушен и пропускает ход!")
                self.enemy.stunned = False

            print("\n" + "-" * 30)
            print(f"Ваше здоровье: {self.player.health}/{self.player.max_health}")
            print(f"Ваша энергия: {self.player.energy}/{self.player.max_energy}")
            print(f"Ваша мана: {self.player.mana}/{self.player.max_mana}")
            print(f"Здоровье врага: {self.enemy.health}")

            self.player.show_battle_menu()

            if self.player.spells:
                print("7. 📚 Магия")

            choice = input("Выберите действие: ")

            attack_mod, crit_mod, dodge_mod = self.weather.apply_effects(self.player, self.enemy)

            if choice == "1":
                if self.player.energy < 10:
                    print("❌ Недостаточно энергии!")
                    continue

                self.player.energy -= 10

                power = self.player.power + self.player.temp_power
                damage = random.randint(int(power * 0.5), power)
                damage = int(damage * attack_mod)

                self.enemy.health -= damage
                print(f"⚔️ Обычная атака! Нанесено {damage} урона!")

                if self.enemy.health <= 0:
                    self.win_battle()
                    return

            elif choice == "2":
                if self.player.attack_strong(self.enemy):
                    self.win_battle()
                    return

            elif choice == "3":
                self.player.defend()

            elif choice == "4":
                self.show_inventory_in_battle()

            elif choice == "5":
                escape_chance = 0.3
                if self.weather.current == "🌙 Ночь":
                    escape_chance = 0.5

                if random.random() > escape_chance:
                    print("🏃 Вы успешно убежали!")
                    self.enemy = None
                    self.weather.change_weather()
                    return
                else:
                    print("❌ Не удалось убежать!")

            elif choice == "6" and self.player.companions:
                for companion in self.player.companions:
                    companion.action(self.player, self.enemy)

            elif choice == "7" and self.player.spells:
                spell = self.show_spells_in_battle()
                if spell:
                    if spell.cast(self.player, self.enemy):
                        if self.enemy.health <= 0:
                            self.win_battle()
                            return

            if self.enemy.is_alive():
                print("\n🤖 Ход монстра!")
                time.sleep(1)

                damage_multiplier = 1.0
                if self.player.defense_boost_turns > 0:
                    damage_multiplier *= 0.5
                if self.player.shield_turns > 0:
                    damage_multiplier *= 0.7
                    self.player.shield_turns -= 1

                old_power = self.enemy.power
                self.enemy.power = int(self.enemy.power * damage_multiplier)

                if self.enemy.attack(self.player):
                    self.game_over()
                    return

                self.enemy.power = old_power

            if self.player.power_boost_turns > 0:
                self.player.power_boost_turns -= 1
                if self.player.power_boost_turns == 0:
                    self.player.temp_power = 0
                    print("⚔️ Эффект усиления силы закончился")

            if self.player.defense_boost_turns > 0:
                self.player.defense_boost_turns -= 1
                if self.player.defense_boost_turns == 0:
                    self.player.temp_defense = 0
                    print("🛡️ Эффект защиты закончился")

            self.player.mana = min(self.player.mana + 2, self.player.max_mana)

            self.weather.change_weather()

    def show_inventory_in_battle(self):
        """
        Показать инвентарь во время битвы
        """
        if not self.player.inventory:
            print("🎒 В инвентаре нет предметов!")
            return

        print("\n🎒 Ваши предметы:")
        for i, item in enumerate(self.player.inventory):
            print(f"{i + 1}. {item.name}")
        print("0. Отмена")

        try:
            choice = int(input("Выберите предмет: ")) - 1
            if choice >= 0:
                if self.player.use_item(choice):
                    print("✅ Предмет использован!")
        except ValueError:
            pass

    def show_spells_in_battle(self):
        """
        Показать доступные заклинания в бою
        """
        if not self.player.spells:
            print("❌ У вас нет заклинаний!")
            return None

        print("\n📚 ЗАКЛИНАНИЯ:")
        for i, spell in enumerate(self.player.spells, 1):
            mana_color = "✅" if self.player.mana >= spell.mana_cost else "❌"
            print(f"{i}. {mana_color} {spell}")
        print("0. Отмена")

        try:
            choice = int(input("Выберите заклинание: ")) - 1
            if 0 <= choice < len(self.player.spells):
                return self.player.spells[choice]
        except ValueError:
            pass
        return None

    def win_battle(self):
        """
        Победа в битве
        """
        print(f"\n🎉 ПОБЕДА! Вы победили {self.enemy.name}!")

        self.player.monsters_killed += 1

        enemy_name = self.enemy.name.lower()
        if "гоблин" in enemy_name:
            self.update_quests("kill_goblin", 1)
        elif "волк" in enemy_name:
            self.update_quests("kill_wolf", 1)

        self.player.battles_without_healing += 1
        if self.player.battles_without_healing > self.player.max_battles_without_healing:
            self.player.max_battles_without_healing = self.player.battles_without_healing

        self.player.gold += self.enemy.reward_gold
        self.player.gain_exp(self.enemy.reward_exp)

        self.update_quests("gold", self.player.gold)
        self.update_quests("level", self.player.level)

        self.player.energy = min(self.player.energy + 30, self.player.max_energy)

        print(f"💰 Получено {self.enemy.reward_gold} золота!")
        print(f"⚡ Восстановлено 30 энергии!")

        self.check_achievements()

        self.enemy = None
        self.weather.change_weather()

    def game_over(self):
        """
        Игрок проиграл
        """
        print("\n💀 ВЫ ПОГИБЛИ...")
        print("🎮 GAME OVER")
        self.running = False

    def show_shop(self):
        """
        Магазин предметов
        """
        print("\n🏪 МАГАЗИН ПРЕДМЕТОВ")
        print(f"💰 Ваше золото: {self.player.gold}")
        print("\nТовары:")

        for i, item in enumerate(self.shop_items, 1):
            print(f"{i}. {item.name} - {item.price} золота")
        print("0. Выйти")

        try:
            choice = int(input("Что хотите купить? "))
            if 1 <= choice <= len(self.shop_items):
                item = self.shop_items[choice - 1]

                if self.player.gold >= item.price:
                    self.player.gold -= item.price
                    new_item = Item(item.name, item.type, item.value, item.price)
                    self.player.inventory.append(new_item)
                    self.player.collected_items.add(item.name)
                    print(f"✅ Вы купили {item.name}!")
                    self.check_achievements()
                else:
                    print("❌ Недостаточно золота!")
        except ValueError:
            pass

    def show_spell_shop(self):
        """
        Магазин заклинаний
        """
        print("\n📚 МАГАЗИН ЗАКЛИНАНИЙ")
        print(f"💰 Ваше золото: {self.player.gold}")
        print(f"📚 Ваши заклинания: {len(self.player.spells)}")

        print("\nДоступные заклинания:")
        for i, spell in enumerate(self.available_spells, 1):
            if spell not in self.player.spells:
                price = spell.mana_cost * 5
                print(f"{i}. {spell.name} - {price}💰")
                print(f"   {spell.description}")

        print("0. Назад")

        try:
            choice = int(input("Выберите заклинание для изучения: ")) - 1
            if 0 <= choice < len(self.available_spells):
                spell = self.available_spells[choice]
                price = spell.mana_cost * 5

                if spell not in self.player.spells:
                    if self.player.gold >= price:
                        self.player.gold -= price
                        self.player.learn_spell(spell)
                        self.player.collected_items.add(spell.name)
                        self.check_achievements()
                    else:
                        print("❌ Недостаточно золота!")
                else:
                    print("❌ Вы уже знаете это заклинание!")
        except ValueError:
            pass

    def hire_companion(self):
        """
        Нанять спутника
        """
        print("\n👥 НАЕМ СПУТНИКА")
        print(f"💰 Ваше золото: {self.player.gold}")

        companions = [
            {"name": "Воин Брут", "type": "warrior", "price": 100},
            {"name": "Целительница Элис", "type": "healer", "price": 150},
            {"name": "Вор Рыжик", "type": "thief", "price": 120}
        ]

        print("\nДоступные спутники:")
        for i, comp in enumerate(companions, 1):
            print(f"{i}. {comp['name']} ({comp['type']}) - {comp['price']} золота")
        print("0. Отмена")

        try:
            choice = int(input("Кого хотите нанять? ")) - 1
            if 0 <= choice < len(companions):
                comp_data = companions[choice]

                if self.player.gold >= comp_data["price"]:
                    self.player.gold -= comp_data["price"]
                    new_companion = Companion(comp_data["name"], comp_data["type"], 1)
                    self.player.companions.append(new_companion)
                    print(f"✅ {comp_data['name']} присоединился к вам!")
                else:
                    print("❌ Недостаточно золота!")
        except ValueError:
            pass

    def show_quest_board(self):
        """
        Показать доску квестов
        """
        print("\n📋 ДОСКА КВЕСТОВ")
        print("=" * 40)

        print("\n📌 Активные квесты:")
        if self.active_quests:
            for i, quest in enumerate(self.active_quests, 1):
                print(f"{i}. {quest.show_progress()}")
        else:
            print("  Нет активных квестов")

        print("\n📋 Доступные квесты:")
        available = [q for q in self.available_quests if q not in self.active_quests and q not in self.completed_quests]
        if available:
            for i, quest in enumerate(available, 1):
                print(f"{i}. {quest.name} - {quest.description}")
                print(f"   Награда: {quest.reward_gold}💰, {quest.reward_exp}✨")
        else:
            print("  Нет доступных квестов")

        print("\n✅ Выполненные квесты:")
        if self.completed_quests:
            for quest in self.completed_quests:
                print(f"  ✓ {quest.name}")
        else:
            print("  Нет выполненных квестов")

        print("\nДействия:")
        print("1. Взять квест")
        print("2. Сдать квест")
        print("0. Назад")

        return input("Выберите действие: ")

    def take_quest(self):
        """
        Взять новый квест
        """
        available = [q for q in self.available_quests if q not in self.active_quests and q not in self.completed_quests]

        if not available:
            print("❌ Нет доступных квестов!")
            return

        print("\nДоступные квесты:")
        for i, quest in enumerate(available, 1):
            print(f"{i}. {quest.name} - {quest.description}")
            print(f"   Награда: {quest.reward_gold}💰, {quest.reward_exp}✨")

        try:
            choice = int(input("Выберите номер квеста (0 - отмена): ")) - 1
            if 0 <= choice < len(available):
                quest = available[choice]
                self.active_quests.append(quest)
                print(f"✅ Вы взяли квест: {quest.name}")
        except ValueError:
            pass

    def complete_quests(self):
        """
        Сдать выполненные квесты
        """
        completed = [q for q in self.active_quests if q.completed]

        if not completed:
            print("❌ Нет выполненных квестов!")
            return

        print("\n✅ Выполненные квесты:")
        for i, quest in enumerate(completed, 1):
            print(f"{i}. {quest.name}")

        try:
            choice = int(input("Выберите квест для сдачи (0 - отмена): ")) - 1
            if 0 <= choice < len(completed):
                quest = completed[choice]
                print(f"\n🎉 Квест выполнен: {quest.name}")
                quest.get_reward(self.player)

                self.active_quests.remove(quest)
                self.completed_quests.append(quest)

                self.check_achievements()
        except ValueError:
            pass

    def update_quests(self, event_type, amount=1):
        """
        Обновить прогресс всех активных квестов
        """
        for quest in self.active_quests:
            if not quest.completed:
                quest.update(event_type, amount)

    def check_achievements(self):
        """
        Проверить все достижения
        """
        for achievement in self.player.achievements:
            if achievement.check(self.player):
                print(f"\n🏆 ПОЛУЧЕНО ДОСТИЖЕНИЕ: {achievement.name}!")
                print(f"   {achievement.description}")

    def show_achievements(self):
        """
        Показать все достижения
        """
        print("\n🏆 ДОСТИЖЕНИЯ")
        print("=" * 40)

        unlocked = [a for a in self.player.achievements if a.unlocked]
        locked = [a for a in self.player.achievements if not a.unlocked]

        print(f"\n✅ Получены ({len(unlocked)}):")
        for a in unlocked:
            print(f"  {a}")

        print(f"\n❌ Не получены ({len(locked)}):")
        for a in locked:
            print(f"  {a}")

    def start(self):
        """
        Главный игровой цикл
        """
        while self.running:
            choice = self.show_menu()

            if choice == "1":
                self.find_enemy()

            elif choice == "2":
                self.player.heal()

            elif choice == "3":
                self.player.show_stats()

            elif choice == "4":
                self.player.show_inventory()

            elif choice == "5":
                self.show_shop()

            elif choice == "6":
                self.show_spell_shop()

            elif choice == "7":
                self.hire_companion()

            elif choice == "8":
                while True:
                    quest_choice = self.show_quest_board()
                    if quest_choice == "1":
                        self.take_quest()
                    elif quest_choice == "2":
                        self.complete_quests()
                    elif quest_choice == "0":
                        break

            elif choice == "9":
                self.show_achievements()

            elif choice == "10":
                print("\n👋 До свидания! Спасибо за игру!")
                self.running = False

            else:
                print("\n❌ Неправильный выбор! Попробуйте снова.")


# === ЗАПУСК ИГРЫ ===
if __name__ == "__main__":
    game = Game()
    game.start()