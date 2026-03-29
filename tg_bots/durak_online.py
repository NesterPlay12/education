import random
import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SUITS = ['♥', '♦', '♣', '♠']
VALUES = ['6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
SUIT_EMOJI = {'♥': '♥', '♦': '♦', '♣': '♣', '♠': '♠'}
VALUE_NAMES = {'6': '6', '7': '7', '8': '8', '9': '9', '10': '10', 'J': 'В', 'Q': 'Д', 'K': 'К', 'A': 'Т'}

games = {}
players = {}


class Game:
    def __init__(self, game_id, vs_bot=False):
        self.id = game_id
        self.players = []
        self.deck = []
        self.hands = {}
        self.table = []
        self.trump = None
        self.turn = 0
        self.attacker = 0
        self.defender = 1
        self.status = "waiting"
        self.vs_bot = vs_bot
        self.taking_cards = False
        self.create_deck()

    def create_deck(self):
        self.deck = [f"{suit}{value}" for suit in SUITS for value in VALUES]
        random.shuffle(self.deck)
        self.trump = self.deck[-1][0] if self.deck else '♦'

    def add_player(self, user_id, username):
        max_players = 2 if self.vs_bot else 6
        player_ids = [p['id'] for p in self.players]

        if user_id in player_ids:
            return False

        if len(self.players) < max_players:
            self.players.append({
                'id': user_id,
                'name': username,
                'type': 'human'
            })
            self.hands[user_id] = []

            if len(self.players) == 2:
                self.defender = 1
            return True
        return False

    def add_bot(self):
        bot_id = -1
        self.players.append({
            'id': bot_id,
            'name': '🤖 Бот',
            'type': 'bot'
        })
        self.hands[bot_id] = []

        if len(self.players) == 2:
            self.defender = 1

    def deal_cards(self):
        for player in self.players:
            player_id = player['id']
            if player_id not in self.hands:
                self.hands[player_id] = []
            while len(self.hands[player_id]) < 6 and self.deck:
                card = self.deck.pop()
                self.hands[player_id].append(card)

        self.attacker = random.randint(0, len(self.players) - 1)
        self.turn = self.attacker
        self.defender = (self.attacker + 1) % len(self.players)
        self.status = "playing"

    def get_card_rank_value(self, card):
        rank = card[1:] if len(card) == 3 else card[1]
        try:
            return VALUES.index(rank)
        except ValueError:
            return 0

    def can_beat(self, attack_card, defend_card):
        attack_suit = attack_card[0]
        attack_value = self.get_card_rank_value(attack_card)
        defend_suit = defend_card[0]
        defend_value = self.get_card_rank_value(defend_card)

        if defend_suit == attack_suit:
            return defend_value > attack_value
        if defend_suit == self.trump and attack_suit != self.trump:
            return True
        return False

    def play_card(self, player_id, card_index):
        if (player_id not in self.hands or
                not self.hands[player_id] or
                card_index < 0 or
                card_index >= len(self.hands[player_id])):
            return False, "Неверная карта"

        card = self.hands[player_id][card_index]

        if player_id == self.players[self.attacker]['id']:
            if len(self.table) > 0 and len(self.table) % 2 == 1:
                return False, "Сейчас нужно защищаться или брать карты"

            if len(self.table) > 0:
                allowed_values = []
                for card_data in self.table:
                    if card_data['position'] == 'attack':
                        allowed_values.append(
                            card_data['card'][1:] if len(card_data['card']) == 3 else card_data['card'][1])

                card_value = card[1:] if len(card) == 3 else card[1]
                if card_value not in allowed_values:
                    return False, "Можно подкидывать только карты с такими же значениями"

            self.hands[player_id].pop(card_index)
            self.table.append({
                'card': card,
                'player': player_id,
                'position': 'attack'
            })
            self.turn = self.defender
            return True, f"Атака: {card}"

        elif player_id == self.players[self.defender]['id']:
            if len(self.table) == 0 or len(self.table) % 2 == 0:
                return False, "Сейчас нужно атаковать"

            last_attack = None
            for card_data in reversed(self.table):
                if card_data['position'] == 'attack':
                    last_attack = card_data
                    break

            if not last_attack:
                return False, "Нет атакующей карты"

            if self.can_beat(last_attack['card'], card):
                self.hands[player_id].pop(card_index)
                self.table.append({
                    'card': card,
                    'player': player_id,
                    'position': 'defend'
                })

                attack_count = sum(1 for c in self.table if c['position'] == 'attack')
                defend_count = sum(1 for c in self.table if c['position'] == 'defend')

                if attack_count == defend_count:
                    winner = self.end_round()
                    if winner:
                        return True, f"Защита: {card}\n\n🏆 Игра окончена!"
                    return True, f"Защита: {card}\n\n✅ Раунд завершен! Теперь атакует {self.players[self.attacker]['name']}"
                else:
                    self.turn = self.attacker
                    return True, f"Защита: {card}"
            else:
                return False, "Этой картой нельзя побить"

        return False, "Не ваш ход"

    def take_cards(self, player_id):
        if player_id != self.players[self.defender]['id']:
            return False, "Не вы защищаетесь"

        for card_data in self.table:
            self.hands[player_id].append(card_data['card'])

        self.table = []
        self.attacker, self.defender = self.defender, self.attacker
        self.turn = self.attacker
        self.taking_cards = True
        return True, "Вы взяли карты"

    def end_round(self):
        self.table = []

        for player in self.players:
            player_id = player['id']
            while len(self.hands[player_id]) < 6 and self.deck:
                card = self.deck.pop()
                self.hands[player_id].append(card)

        self.attacker, self.defender = self.defender, self.attacker
        self.turn = self.attacker
        self.taking_cards = False
        return self.check_game_over()

    def bot_move(self):
        bot_id = -1

        if bot_id not in self.hands or not self.hands[bot_id]:
            return None, "Нет карт"

        hand = self.hands[bot_id]

        if self.turn >= len(self.players) or self.players[self.turn]['id'] != bot_id:
            return None, "Сейчас не ход бота"

        if bot_id == self.players[self.defender]['id'] and len(self.table) > 0 and len(self.table) % 2 == 1:
            last_attack = None
            for card_data in reversed(self.table):
                if card_data['position'] == 'attack':
                    last_attack = card_data
                    break

            if last_attack:
                for i, card in enumerate(hand):
                    if self.can_beat(last_attack['card'], card):
                        self.hands[bot_id].pop(i)
                        self.table.append({
                            'card': card,
                            'player': bot_id,
                            'position': 'defend'
                        })

                        attack_count = sum(1 for c in self.table if c['position'] == 'attack')
                        defend_count = sum(1 for c in self.table if c['position'] == 'defend')

                        if attack_count == defend_count:
                            winner = self.end_round()
                            if winner:
                                return True, f"🤖 Бот бьет картой {card}\n\n🏆 Игра окончена!"
                            return True, f"🤖 Бот бьет картой {card}\n\n✅ Раунд завершен!"
                        else:
                            self.turn = self.attacker
                            return True, f"🤖 Бот бьет картой {card}"

                for card_data in self.table:
                    self.hands[bot_id].append(card_data['card'])
                self.table = []
                self.attacker, self.defender = self.defender, self.attacker
                self.turn = self.attacker
                self.taking_cards = True
                return True, "🤖 Бот берет карты"

        elif bot_id == self.players[self.attacker]['id'] and (len(self.table) == 0 or len(self.table) % 2 == 0):
            if len(self.table) == 0:
                non_trump = [(i, card) for i, card in enumerate(hand) if card[0] != self.trump]
                if non_trump:
                    non_trump.sort(key=lambda x: self.get_card_rank_value(x[1]))
                    i, card = non_trump[0]
                else:
                    cards = [(i, card) for i, card in enumerate(hand)]
                    cards.sort(key=lambda x: self.get_card_rank_value(x[1]))
                    i, card = cards[0]

                self.hands[bot_id].pop(i)
                self.table.append({
                    'card': card,
                    'player': bot_id,
                    'position': 'attack'
                })
                self.turn = self.defender
                return True, f"🤖 Бот атакует картой {card}"

            else:
                attack_values = set()
                for card_data in self.table:
                    if card_data['position'] == 'attack':
                        val = card_data['card'][1:] if len(card_data['card']) == 3 else card_data['card'][1]
                        attack_values.add(val)

                for i, card in enumerate(hand):
                    card_val = card[1:] if len(card) == 3 else card[1]
                    if card_val in attack_values:
                        self.hands[bot_id].pop(i)
                        self.table.append({
                            'card': card,
                            'player': bot_id,
                            'position': 'attack'
                        })
                        self.turn = self.defender
                        return True, f"🤖 Бот подкидывает {card}"

                winner = self.end_round()
                if winner:
                    return True, f"🏆 Игра окончена! Победитель: {winner if winner != -1 else 'Бот'}"
                else:
                    return True, f"🤖 Бот завершил раунд"

        return None, "Бот пропускает ход"

    def check_game_over(self):
        for player in self.players:
            player_id = player['id']
            if player_id in self.hands and len(self.hands[player_id]) == 0 and len(self.deck) == 0:
                return player_id
        return None

    def get_state(self):
        if not self.players:
            return {
                'players': [],
                'trump': f"{self.trump} (козырь)" if self.trump else "Нет",
                'table': [],
                'deck_count': len(self.deck),
                'attacker': None,
                'defender': None,
                'turn': None,
                'vs_bot': self.vs_bot,
                'taking_cards': self.taking_cards
            }

        player_names = [p['name'] for p in self.players]

        table_view = []
        for i, card_data in enumerate(self.table):
            if card_data['position'] == 'attack':
                if i % 2 == 0:
                    table_view.append(f"⚔️ {card_data['card']}")
                else:
                    table_view.append(f"🛡️ {card_data['card']}")

        return {
            'players': player_names,
            'trump': f"{self.trump} (козырь)" if self.trump else "Нет",
            'table': table_view,
            'deck_count': len(self.deck),
            'attacker': self.players[self.attacker]['name'] if self.players and self.attacker < len(
                self.players) else None,
            'defender': self.players[self.defender]['name'] if self.players and self.defender < len(
                self.players) else None,
            'turn': self.players[self.turn]['name'] if self.players and self.turn < len(self.players) else None,
            'vs_bot': self.vs_bot,
            'taking_cards': self.taking_cards
        }


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 Добро пожаловать в игру 'Дурак'!\n\n"
        "📋 Доступные команды:\n"
        "/new - Создать игру с людьми\n"
        "/bot - Создать игру с ботом\n"
        "/join <ID> - Присоединиться к игре\n"
        "/hand - Показать мои карты\n"
        "/status - Статус текущей игры\n"
        "/take - Взять карты (если нечем бить)\n"
        "/end - Завершить раунд (если отбились)\n"
        "/leave - Выйти из игры"
    )


async def new_game_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Игрок"

    if user_id in players:
        await update.message.reply_text("❌ Вы уже участвуете в игре!")
        return

    game_id = random.randint(1000, 9999)
    while game_id in games:
        game_id = random.randint(1000, 9999)

    game = Game(game_id, vs_bot=False)
    game.add_player(user_id, username)
    games[game_id] = game
    players[user_id] = game_id

    keyboard = [
        [
            InlineKeyboardButton("🎴 Раздать карты", callback_data=f"deal_{game_id}"),
            InlineKeyboardButton("👥 Пригласить", callback_data=f"invite_{game_id}")
        ]
    ]

    await update.message.reply_text(
        f"✅ Игра #{game_id} создана!\n"
        f"👤 Игрок: {username}\n\n"
        f"📢 Другие игроки могут присоединиться командой:\n"
        f"<code>/join {game_id}</code>\n\n"
        f"Когда все игроки присоединятся, нажмите 'Раздать карты'.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def new_game_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Игрок"

    if user_id in players:
        await update.message.reply_text("❌ Вы уже участвуете в игре!")
        return

    game_id = random.randint(1000, 9999)
    while game_id in games:
        game_id = random.randint(1000, 9999)

    game = Game(game_id, vs_bot=True)
    game.add_player(user_id, username)
    game.add_bot()
    games[game_id] = game
    players[user_id] = game_id

    keyboard = [
        [InlineKeyboardButton("🎴 Раздать карты", callback_data=f"deal_{game_id}")]
    ]

    await update.message.reply_text(
        f"✅ Игра #{game_id} с ботом создана!\n"
        f"👤 Вы vs 🤖 Бот\n\n"
        f"Нажмите 'Раздать карты' чтобы начать!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Игрок"

    if user_id in players:
        await update.message.reply_text("❌ Вы уже участвуете в игре!")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID игры!\n"
            "Пример: <code>/join 1234</code>",
            parse_mode='HTML'
        )
        return

    try:
        game_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Неверный формат ID игры!")
        return

    if game_id not in games:
        await update.message.reply_text("❌ Игра не найдена!")
        return

    game = games[game_id]

    if game.vs_bot:
        await update.message.reply_text("❌ Это игра с ботом. Присоединиться нельзя!")
        return

    if game.add_player(user_id, username):
        players[user_id] = game_id
        await update.message.reply_text(f"✅ {username} присоединился к игре #{game_id}")
    else:
        await update.message.reply_text("❌ Не удалось присоединиться (игра заполнена)")


async def take_cards_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in players:
        await update.message.reply_text("❌ Вы не участвуете в игре!")
        return

    game_id = players[user_id]
    game = games[game_id]

    if game.status != "playing":
        await update.message.reply_text("❌ Игра еще не началась!")
        return

    success, message = game.take_cards(user_id)
    if success:
        await update.message.reply_text(f"✅ {message}")
        await show_hand(update, context)
    else:
        await update.message.reply_text(f"❌ {message}")


async def end_round_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in players:
        await update.message.reply_text("❌ Вы не участвуете в игре!")
        return

    game_id = players[user_id]
    game = games[game_id]

    if game.status != "playing":
        await update.message.reply_text("❌ Игра еще не началась!")
        return

    if user_id != game.players[game.attacker]['id']:
        await update.message.reply_text("❌ Только атакующий может завершить раунд!")
        return

    winner = game.end_round()
    if winner:
        if winner == -1:
            await update.message.reply_text("🏆 Бот победил!")
        else:
            await update.message.reply_text(f"🏆 Игрок {game.players[winner]['name']} победил!")
        del games[game_id]
        del players[user_id]
    else:
        await update.message.reply_text("✅ Раунд завершен! Новый раунд начинается.")
        await game_status(update, context)


async def show_hand(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in players:
        await update.message.reply_text("❌ Вы не участвуете в игре!")
        return

    game_id = players[user_id]
    game = games[game_id]

    if user_id not in game.hands:
        await update.message.reply_text("🎴 У вас пока нет карт")
        return

    hand = game.hands[user_id]

    if not hand:
        await update.message.reply_text("🎴 У вас нет карт")
        return

    hand.sort(key=lambda c: (SUITS.index(c[0]), VALUES.index(c[1:] if len(c) == 3 else c[1])))

    keyboard = []
    row = []

    for i, card in enumerate(hand):
        suit = card[0]
        value = card[1:] if len(card) == 3 else card[1]
        display_card = f"{SUIT_EMOJI[suit]}{VALUE_NAMES[value]}"

        row.append(InlineKeyboardButton(display_card, callback_data=f"play_{game_id}_{i}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    action_row = []
    if game.taking_cards:
        action_row.append(InlineKeyboardButton("✅ Продолжить", callback_data=f"continue_{game_id}"))
    else:
        if user_id == game.players[game.defender]['id'] and len(game.table) % 2 == 1:
            action_row.append(InlineKeyboardButton("📥 Взять карты", callback_data=f"take_{game_id}"))
        if user_id == game.players[game.attacker]['id'] and len(game.table) % 2 == 0 and len(game.table) > 0:
            action_row.append(InlineKeyboardButton("⏹️ Завершить", callback_data=f"end_{game_id}"))

    if action_row:
        keyboard.append(action_row)

    if game.turn < len(game.players):
        current_player = game.players[game.turn]
        if current_player['id'] == user_id:
            if user_id == game.players[game.defender]['id'] and len(game.table) % 2 == 1:
                turn_message = "\n\n🛡️ <b>Ваша защита! Выберите карту или нажмите 'Взять карты'</b>"
            elif user_id == game.players[game.attacker]['id']:
                if len(game.table) == 0:
                    turn_message = "\n\n⚔️ <b>Ваша атака! Выберите карту для хода</b>"
                else:
                    turn_message = "\n\n⚔️ <b>Можете подкинуть карту или завершить</b>"
            else:
                turn_message = "\n\n✅ <b>Сейчас ваш ход!</b>"
        else:
            turn_message = f"\n\n⏳ Сейчас ходит: {current_player['name']}"
    else:
        turn_message = ""

    table_message = ""
    if game.table:
        table_message = "\n\n📌 На столе:\n"
        for i, card_data in enumerate(game.table):
            if card_data['position'] == 'attack':
                table_message += f"⚔️ {card_data['card']} "
            else:
                table_message += f"🛡️ {card_data['card']} "
            if (i + 1) % 2 == 0:
                table_message += "\n"

    await update.message.reply_text(
        f"🎴 Ваши карты ({len(hand)} шт.):\n"
        f"{' '.join([f'{SUIT_EMOJI[c[0]]}{VALUE_NAMES[c[1:] if len(c) == 3 else c[1]]}' for c in hand])}"
        f"{table_message}"
        f"{turn_message}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def game_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in players:
        await update.message.reply_text("❌ Вы не участвуете в игре!")
        return

    game_id = players[user_id]
    game = games[game_id]
    state = game.get_state()

    game_type = "🤖 С ботом" if state['vs_bot'] else "👥 С людьми"

    status_text = (
        f"🃏 Игра #{game_id} ({game_type})\n"
        f"👥 Игроки: {', '.join(state['players'])}\n"
        f"🎯 {state['trump']}\n"
        f"📊 Карт в колоде: {state['deck_count']}\n"
        f"⚔️ Атакует: {state['attacker']}\n"
        f"🛡️ Защищается: {state['defender']}\n"
        f"▶️ Сейчас ходит: {state['turn']}"
    )

    if state['table']:
        status_text += "\n\n📌 На столе:\n" + '\n'.join(state['table'])

    await update.message.reply_text(status_text)


async def leave_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name or "Игрок"

    if user_id not in players:
        await update.message.reply_text("❌ Вы не участвуете в игре!")
        return

    game_id = players[user_id]
    game = games[game_id]

    game.players = [p for p in game.players if p['id'] != user_id]

    if user_id in game.hands:
        del game.hands[user_id]

    del players[user_id]

    if not game.players:
        del games[game_id]
        await update.message.reply_text("✅ Вы вышли из игры. Игра удалена.")
    else:
        await update.message.reply_text(f"✅ {username} вышел из игры")

        for player in game.players:
            if player['type'] == 'human' and player['id'] != user_id:
                try:
                    await context.bot.send_message(
                        player['id'],
                        f"⚠️ {username} вышел из игры"
                    )
                except Exception as e:
                    logger.error(f"Не удалось уведомить игрока {player['id']}: {e}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data.startswith("deal_"):
        try:
            game_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка: неверный формат данных")
            return

        if game_id not in games:
            await query.edit_message_text("❌ Игра не найдена!")
            return

        game = games[game_id]

        if user_id not in players or players[user_id] != game_id:
            await query.edit_message_text("❌ Вы не участвуете в этой игре!")
            return

        if not game.vs_bot:
            if not game.players or game.players[0]['id'] != user_id:
                await query.edit_message_text("❌ Только создатель игры может раздать карты!")
                return

        if game.vs_bot and len(game.players) != 2:
            await query.edit_message_text("❌ В игре с ботом должно быть 2 игрока (вы и бот)!")
            return

        if not game.vs_bot and len(game.players) < 2:
            await query.edit_message_text("❌ Нужно минимум 2 игрока для начала игры!")
            return

        game.deal_cards()
        game.status = "playing"

        deal_info = "✅ Карты розданы!\n\n"
        for player in game.players:
            card_count = len(game.hands.get(player['id'], []))
            cards = game.hands.get(player['id'], [])
            deal_info += f"{player['name']}: {card_count} карт"
            if player['type'] == 'human' and cards:
                deal_info += f" ({' '.join(cards[:3])}...)"
            deal_info += "\n"

        deal_info += f"\n🎯 Козырь: {game.trump}\n"
        deal_info += f"⚔️ Первым атакует: {game.players[game.attacker]['name']}\n"
        deal_info += f"🛡️ Защищается: {game.players[game.defender]['name']}"

        await query.edit_message_text(deal_info)

        if game.vs_bot and game.players[game.turn]['type'] == 'bot':
            await asyncio.sleep(1)
            success, message = game.bot_move()
            if success:
                await query.message.reply_text(message)
                for player in game.players:
                    if player['type'] == 'human':
                        fake_update = type('obj', (object,), {
                            'effective_user': type('obj', (object,), {'id': player['id']}),
                            'message': query.message
                        })
                        await show_hand(fake_update, context)
                        break

    elif data.startswith("invite_"):
        try:
            game_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка: неверный формат данных")
            return

        await query.edit_message_text(
            f"📢 Приглашение в игру #{game_id}\n\n"
            f"Чтобы присоединиться, отправьте команду:\n"
            f"<code>/join {game_id}</code>",
            parse_mode='HTML'
        )

    elif data.startswith("play_"):
        try:
            _, game_id_str, card_index_str = data.split("_")
            game_id = int(game_id_str)
            card_index = int(card_index_str)
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка: неверный формат данных")
            return

        if user_id not in players or players[user_id] != game_id:
            await query.edit_message_text("❌ Вы не участвуете в этой игре!")
            return

        if game_id not in games:
            await query.edit_message_text("❌ Игра не найдена!")
            return

        game = games[game_id]

        if game.status != "playing":
            await query.edit_message_text("❌ Игра еще не началась!")
            return

        if game.turn >= len(game.players) or game.players[game.turn]['id'] != user_id:
            await query.edit_message_text("❌ Сейчас не ваш ход!")
            return

        success, message = game.play_card(user_id, card_index)

        if success:
            await query.edit_message_text(f"✅ {message}")
            winner = game.check_game_over()

            if winner:
                if winner == -1:
                    await query.message.reply_text("🏆 Бот победил!")
                else:
                    winner_name = next((p['name'] for p in game.players if p['id'] == winner), "Игрок")
                    await query.message.reply_text(f"🏆 {winner_name} победил!")
                del games[game_id]
                if user_id in players:
                    del players[user_id]
                return

            if game.turn < len(game.players) and game.players[game.turn]['type'] == 'bot':
                await asyncio.sleep(1)
                success2, message2 = game.bot_move()
                if success2:
                    await query.message.reply_text(message2)
                    winner = game.check_game_over()
                    if winner:
                        if winner == -1:
                            await query.message.reply_text("🏆 Бот победил!")
                        else:
                            winner_name = next((p['name'] for p in game.players if p['id'] == winner), "Игрок")
                            await query.message.reply_text(f"🏆 {winner_name} победил!")
                        del games[game_id]
                        if user_id in players:
                            del players[user_id]
                        return

            await show_hand(update, context)
        else:
            await query.edit_message_text(f"❌ {message}")

    elif data.startswith("take_"):
        try:
            game_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка: неверный формат данных")
            return

        if user_id not in players or players[user_id] != game_id:
            await query.edit_message_text("❌ Вы не участвуете в этой игре!")
            return

        game = games[game_id]
        success, message = game.take_cards(user_id)

        if success:
            await query.edit_message_text(f"✅ {message}")

            winner = game.check_game_over()
            if winner:
                if winner == -1:
                    await query.message.reply_text("🏆 Бот победил!")
                else:
                    winner_name = next((p['name'] for p in game.players if p['id'] == winner), "Игрок")
                    await query.message.reply_text(f"🏆 {winner_name} победил!")
                del games[game_id]
                if user_id in players:
                    del players[user_id]
                return

            if game.players[game.turn]['type'] == 'bot':
                await asyncio.sleep(1)
                success2, message2 = game.bot_move()
                if success2:
                    await query.message.reply_text(message2)
                    winner = game.check_game_over()
                    if winner:
                        if winner == -1:
                            await query.message.reply_text("🏆 Бот победил!")
                        else:
                            winner_name = next((p['name'] for p in game.players if p['id'] == winner), "Игрок")
                            await query.message.reply_text(f"🏆 {winner_name} победил!")
                        del games[game_id]
                        if user_id in players:
                            del players[user_id]
                        return

            await show_hand(update, context)
        else:
            await query.edit_message_text(f"❌ {message}")

    elif data.startswith("end_"):
        try:
            game_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка: неверный формат данных")
            return

        if user_id not in players or players[user_id] != game_id:
            await query.edit_message_text("❌ Вы не участвуете в этой игре!")
            return

        game = games[game_id]

        if user_id != game.players[game.attacker]['id']:
            await query.edit_message_text("❌ Только атакующий может завершить раунд!")
            return

        winner = game.end_round()
        if winner:
            if winner == -1:
                await query.edit_message_text("🏆 Бот победил!")
            else:
                winner_name = next((p['name'] for p in game.players if p['id'] == winner), "Игрок")
                await query.edit_message_text(f"🏆 {winner_name} победил!")
            del games[game_id]
            if user_id in players:
                del players[user_id]
        else:
            await query.edit_message_text("✅ Раунд завершен! Начинается новый раунд.")

            if game.players[game.turn]['type'] == 'bot':
                await asyncio.sleep(1)
                success2, message2 = game.bot_move()
                if success2:
                    await query.message.reply_text(message2)

            await game_status(update, context)

    elif data.startswith("continue_"):
        try:
            game_id = int(data.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("❌ Ошибка: неверный формат данных")
            return

        if user_id not in players or players[user_id] != game_id:
            await query.edit_message_text("❌ Вы не участвуете в этой игре!")
            return

        game = games[game_id]
        game.taking_cards = False
        await query.edit_message_text("✅ Продолжаем игру!")

        if game.players[game.turn]['type'] == 'bot':
            await asyncio.sleep(1)
            success2, message2 = game.bot_move()
            if success2:
                await query.message.reply_text(message2)

        await show_hand(update, context)


def main():
    TOKEN = "7631600375:AAFIqfg5HgkIHsjnxZ4cDxXTUyNYwZS7uk8"

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_game_human))
    app.add_handler(CommandHandler("bot", new_game_bot))
    app.add_handler(CommandHandler("join", join_game))
    app.add_handler(CommandHandler("hand", show_hand))
    app.add_handler(CommandHandler("status", game_status))
    app.add_handler(CommandHandler("take", take_cards_command))
    app.add_handler(CommandHandler("end", end_round_command))
    app.add_handler(CommandHandler("leave", leave_game))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("=" * 50)
    print("🤖 Бот 'Дурак' запущен!")
    print("=" * 50)

    app.run_polling()


if __name__ == '__main__':
    main()
