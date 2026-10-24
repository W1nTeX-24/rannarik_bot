import asyncio
import random
import string
import datetime
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

from config import BOT_TOKEN, DB_NAME, SUPERADMINS, DONATION_ALERTS_URL, EXAM_FEES

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- КАТАЛОГ ТРАНСПОРТА (CAR CRASH SIMULATOR) ---
CAR_CATALOG = {
    # Категория B (Легковые / Внедорожники)
    "bike": {"name": "Велосипед (Bike)", "price": 0, "tax": 0, "cat": "Без прав"},
    "vaz_oka": {"name": "ВАЗ Ока", "price": 10000, "tax": 50, "cat": "B"},
    "lada_2106": {"name": "LADA 2106 (Жигули)", "price": 5000, "tax": 40, "cat": "B"},
    "lada_2107": {"name": "LADA 2107", "price": 5000, "tax": 40, "cat": "B"},
    "lada_samara": {"name": "Lada Samara", "price": 7000, "tax": 60, "cat": "B"},
    "twingo": {"name": "Renault Twingo", "price": 15000, "tax": 100, "cat": "B"},
    "golf": {"name": "VW Golf", "price": 20000, "tax": 120, "cat": "B"},
    "civic": {"name": "Honda Civic", "price": 21000, "tax": 130, "cat": "B"},
    "sierra": {"name": "Ford Sierra", "price": 20000, "tax": 120, "cat": "B"},
    "peugeot_406": {"name": "Peugeot 406", "price": 25000, "tax": 160, "cat": "B"},
    "audi_a4": {"name": "Audi A4", "price": 28000, "tax": 200, "cat": "B"},
    "mercedes_w124": {"name": "Mercedes-Benz W124", "price": 30000, "tax": 220, "cat": "B"},
    "passat": {"name": "VW Passat", "price": 30000, "tax": 220, "cat": "B"},
    "bmw_e36": {"name": "BMW E36", "price": 45000, "tax": 320, "cat": "B"},
    "mitsubishi_evo6": {"name": "Mitsubishi Evo 6", "price": 35000, "tax": 260, "cat": "B"},
    "toyota_mr2": {"name": "Toyota MR2", "price": 45000, "tax": 320, "cat": "B"},
    "hilux": {"name": "Toyota Hilux", "price": 25000, "tax": 180, "cat": "B"},
    "pajero": {"name": "Mitsubishi Pajero", "price": 30000, "tax": 220, "cat": "B"},
    "ranger": {"name": "Ford Ranger", "price": 35000, "tax": 250, "cat": "B"},
    "range_rover": {"name": "Range Rover", "price": 40000, "tax": 300, "cat": "B"},
    "gelik": {"name": "Mercedes G250 Gelik", "price": 50000, "tax": 400, "cat": "B"},
    "porsche_996": {"name": "Porsche 996", "price": 115000, "tax": 800, "cat": "B"},
    "ranger_modded": {"name": "Ford Ranger Modded", "price": 500000, "tax": 2500, "cat": "B"},

    # Категория A (Мототехника)
    "atv": {"name": "Квадроцикл ATV", "price": 13000, "tax": 90, "cat": "A"},
    "suzuki_pv": {"name": "Мопед Suzuki PV 50", "price": 9000, "tax": 60, "cat": "A"},
    "ninja_bike": {"name": "Мотоцикл Ninja GPZ900R", "price": 150000, "tax": 600, "cat": "A"},

    # Категория C (Грузовики)
    "scania_r500": {"name": "Тягач Scania R500", "price": 80000, "tax": 950, "cat": "C"},
    "iveco_stralis": {"name": "Грузовик Iveco Stralis", "price": 75000, "tax": 850, "cat": "C"},

    # Категория D (Автобусы)
    "ikarus_260": {"name": "Автобус Ikarus 260", "price": 45000, "tax": 500, "cat": "D"},
}

# --- НЕДВИЖИМОСТЬ В ГОРОДЕ ---
HOUSE_CATALOG = {
    "city_flat": {"name": "🏢 Квартира в городе", "price": 35000, "tax": 400},
    "city_regular": {"name": "🏡 Обычный дом в городе", "price": 75000, "tax": 900},
    "city_lux": {"name": "🏰 Люкс дом в городе", "price": 180000, "tax": 2200},
}

# --- БИЗНЕСЫ ОКРУГА ---
BUSINESS_CATALOG = {
    "sto": {"name": "🔧 СТО (Автомастерская)", "price": 70000, "income": 4800, "tax": 1000},
    "bus_depot": {"name": "🚌 Автобусное Депо", "price": 85000, "income": 6000, "tax": 1300},
    "gas_station": {"name": "⛽ АЗС Circle K", "price": 95000, "income": 7000, "tax": 1500},
    "truck_base": {"name": "🚛 База дальнобойщиков", "price": 130000, "income": 9500, "tax": 2100},
}

# --- ПРЕМИУМ-ПРЕДМЕТЫ С БОНУСОМ К ЗАРАБОТКЕ (ПРОДАЮТСЯ НА 5VITO) ---
BONUS_ITEMS = {
    "investor_case": {
        "name": "💼 Чемодан инвестора",
        "price": 15000,
        "bonus_pct": 10,
        "desc": "+10% к общему заработку за сессию"
    },
    "crypto_laptop": {
        "name": "💻 Ноутбук криптотрейдера",
        "price": 35000,
        "bonus_pct": 20,
        "desc": "+20% к общему заработку за сессию"
    },
    "rolex_watch": {
        "name": "💎 Золотые часы Rolex",
        "price": 75000,
        "bonus_pct": 35,
        "desc": "+35% к общему заработку за сессию"
    },
    "magnate_ring": {
        "name": "👑 Платиновый перстень магната",
        "price": 150000,
        "bonus_pct": 50,
        "desc": "+50% к общему заработку за сессию"
    },
}

# --- ТЁМНЫЙ РЫНОК (DARKNET) ---
DARK_ITEMS = {
    "coke": {"name": "❄️ Кокаин (Кокс)", "price": 2500, "desc": "Нелегал! Разовый допинг +35% к выплате за сессию", "is_coke": True},
    "lockpick": {"name": "🪛 Отмычка", "price": 800, "desc": "Инструмент для взлома замков и дверей", "is_coke": False},
    "fake_id": {"name": "🪪 Поддельный паспорт", "price": 5000, "desc": "Скрывает судимости при поверхностном досмотре", "is_coke": False},
    "hacker_usb": {"name": "💾 Взломщик базы МВД", "price": 8000, "desc": "Флешка для стирания судимостей", "is_coke": False},
}

# --- ДОНАТ ПРИВИЛЕГИИ ---
DONATE_PERKS = {
    "vip_status": {"name": "👑 VIP Гражданин (+50% к ЗП навсегда)", "coins": 150},
    "cash_50k": {"name": "💶 Пакет 50,000 €", "coins": 100},
    "cash_150k": {"name": "💶 Пакет 150,000 €", "coins": 250},
    "clear_criminal": {"name": "⚖️ Очистить судимости в базе МВД", "coins": 200},
    "gold_number": {"name": "📱 Блатной номер (+372 5777 7777)", "coins": 80},
}

# --- ЗАРПЛАТЫ ЗА РП СЕССИЮ (€) ---
SALARIES = {
    "Гражданин": 0,
    "Младший Констебль": 1200,
    "Констебль": 1800,
    "Главный Констебль": 2600,
    "Работник Скорой": 1500,
    "Пожарный": 1400,
    "Дорожный рабочий": 900,
    "Водитель Автобуса": 1100,
    "Таксист": 850,
    "Дальнобойщик": 1700,
    "Механик": 1100,
    "Журналист": 1150,
    "Заправщик Азс": 800,
    "Адвокат": 2200,
    "Бандит": 0,
    "Наркоторговец": 0,
    "Модератор": 2000,
}

POLICE_ROLES = ["Младший Констебль", "Констебль", "Главный Констебль"]

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                roblox_nick TEXT,
                rp_name TEXT,
                birth_date TEXT,
                phone_number TEXT,
                iban TEXT,
                faction TEXT DEFAULT 'Гражданин',
                balance INTEGER DEFAULT 1000,
                bank_balance INTEGER DEFAULT 4000,
                donate_coins INTEGER DEFAULT 0,
                license_a INTEGER DEFAULT 0,
                license_b INTEGER DEFAULT 0,
                license_c INTEGER DEFAULT 0,
                license_d INTEGER DEFAULT 0,
                sessions_count INTEGER DEFAULT 0,
                record_criminal INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_vip INTEGER DEFAULT 0,
                has_coke_boost INTEGER DEFAULT 0,
                is_cuffed INTEGER DEFAULT 0,
                passport_status TEXT DEFAULT 'pending'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                model_name TEXT,
                plate_number TEXT,
                tax INTEGER DEFAULT 100
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS houses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                house_key TEXT,
                house_name TEXT,
                tax INTEGER DEFAULT 500
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                biz_key TEXT,
                biz_name TEXT,
                income INTEGER,
                tax INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS market (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                seller_name TEXT,
                seller_username TEXT,
                title TEXT,
                price INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS active_session (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_active INTEGER DEFAULT 0
            )
        """)
        await db.execute("INSERT OR IGNORE INTO active_session (id, is_active) VALUES (1, 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS session_members (user_id INTEGER PRIMARY KEY)")
        await db.commit()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def generate_plate():
    digits = "".join(random.choices(string.digits, k=3))
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
    return f"{digits} {letters}"

def generate_phone():
    p1 = "".join(random.choices(string.digits, k=3))
    p2 = "".join(random.choices(string.digits, k=4))
    return f"+372 5{p1} {p2}"

def generate_iban():
    nums = "".join(random.choices(string.digits, k=16))
    return f"EE{nums[:2]} {nums[2:6]} {nums[6:10]} {nums[10:14]} {nums[14:16]}"

async def is_admin(user_id: int, username: str = None) -> bool:
    if username and username.lower() in [u.lower() for u in SUPERADMINS]:
        return True
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_admin FROM players WHERE user_id = ?", (user_id,)) as cur:
            res = await cur.fetchone()
            if res and res[0] == 1:
                return True
    return False

async def get_inventory_multiplier(user_id: int) -> float:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_name FROM inventory WHERE user_id = ?", (user_id,)) as cur:
            items = await cur.fetchall()
    
    total_bonus_pct = 0
    owned_names = [it[0] for it in items]
    for k, v in BONUS_ITEMS.items():
        if v["name"] in owned_names:
            total_bonus_pct += v["bonus_pct"]
    
    return 1.0 + (total_bonus_pct / 100.0)

# FSM Состояния
class RegState(StatesGroup):
    roblox = State()
    rp_name = State()
    birth_date = State()

class SellSelectState(StatesGroup):
    choosing_item = State()
    price = State()

class BankTransferState(StatesGroup):
    target = State()
    amount = State()

class BankDepositState(StatesGroup):
    amount = State()

class BankWithdrawState(StatesGroup):
    amount = State()

class BroadcastState(StatesGroup):
    text = State()

# --- КЛАВИАТУРЫ ---
async def get_main_menu(user_id: int, username: str = None):
    adm = await is_admin(user_id, username)
    kb = [
        [InlineKeyboardButton(text="🪪 Паспорт & Статус", callback_data="menu:profile"),
         InlineKeyboardButton(text="🏦 Банк Swedbank", callback_data="menu:bank")],
        [InlineKeyboardButton(text="💼 Биржа Труда (Вакансии)", callback_data="menu:jobs"),
         InlineKeyboardButton(text="📱 Мой Телефон", callback_data="menu:phone")],
        [InlineKeyboardButton(text="🚗 Мой Гараж", callback_data="menu:garage"),
         InlineKeyboardButton(text="🏠 Недвижимость в городе", callback_data="menu:my_houses")],
        [InlineKeyboardButton(text="🏢 Автосалон (30+ Авто)", callback_data="menu:dealership"),
         InlineKeyboardButton(text="🏡 Риелторское агентство", callback_data="menu:estate_agency")],
        [InlineKeyboardButton(text="🏭 Бизнесы города", callback_data="menu:businesses"),
         InlineKeyboardButton(text="💎 Магазин Оборудования", callback_data="menu:bonus_shop")],
        [InlineKeyboardButton(text="🛒 Маркет 5vito", callback_data="menu:5vito"),
         InlineKeyboardButton(text="🕵️ DarkNet Рынок", callback_data="menu:darkshop")],
        [InlineKeyboardButton(text="🚦 Автошкола (Категории A,B,C,D)", callback_data="menu:driving_school")],
        [InlineKeyboardButton(text="💎 Донат Магазин", callback_data="menu:donate"),
         InlineKeyboardButton(text="📜 Правила сервера", callback_data="menu:rules")],
    ]
    if adm:
        kb.append([InlineKeyboardButton(text="👑 АДМИН ПАНЕЛЬ 👑", callback_data="admin:panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_bank_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Перевести средства гражданину", callback_data="bank:transfer_start")],
        [InlineKeyboardButton(text="📥 Положить наличные на счёт", callback_data="bank:deposit_start"),
         InlineKeyboardButton(text="📤 Снять наличные в банкомате", callback_data="bank:withdraw_start")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="menu:home")]
    ])

async def get_admin_menu():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM players WHERE passport_status = 'pending'") as cur:
            count = (await cur.fetchone())[0]

    count_str = f" ({count})" if count > 0 else ""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🪪 Заявки на Паспорта{count_str}", callback_data="admin:pending_passports")],
        [InlineKeyboardButton(text="📢 Рассылка игрокам", callback_data="admin:broadcast_start"),
         InlineKeyboardButton(text="🔍 Досье на игрока", callback_data="admin:checkuser_help")],
        [InlineKeyboardButton(text="💶 Начислить/Списать Евро", callback_data="admin:give_money_help"),
         InlineKeyboardButton(text="💎 Выдать Coins", callback_data="admin:give_coins_help")],
        [InlineKeyboardButton(text="🚨 Запуск/Конец Сессии", callback_data="admin:session_help"),
         InlineKeyboardButton(text="📖 Список всех команд", callback_data="admin:all_commands")],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")]
    ])

def get_rules_text():
    return (
        "╭──────⎝乡⎞──────╮\n"
        " 📎 РП ПРАВИЛА RANNARIK RP\n"
        "╰━─━─━─≪✦≫─━─━─━╯\n\n"
        "╰☆╮ 1. Запрещено иметь белую (и другие не человеческие цвета) кожу, хеадлесс, корблокс, волосы как у ёжика.\n"
        "──────────────────\n"
        "╰☆╮ 2. Рофл скины, скины не по тематике рп, скины связанные с политикой и нацисткими группировками запрещены.\n"
        "──────────────────\n"
        "╰☆╮ 3. Нельзя банить людей во время рп процесса из дома если это не рейдеры.\n"
        "──────────────────\n"
        "╰☆╮ 4. Нельзя оставлять машину посреди дороги и спавнить также если она мешает.\n"
        "──────────────────\n"
        "╰☆╮ 5. Запрещено ставить пропы которые могут помешать рп процессу.\n"
        "──────────────────\n"
        "╰☆╮ 6. Все что вне рп пишем в // (Пример: // Привет какая тематика рп?). Все другое считается за рп.\n"
        "──────────────────\n"
        "╰☆╮ 7. Общение по рации или телефону: добавляем т- (т-Ало привет) или р- (р-прием! как слышно).\n"
        "──────────────────\n"
        "╰☆╮ 8. Мысли персонажа пишем в скобках: (Как же надоела эта работа..).\n"
        "──────────────────\n"
        "╰☆╮ 9. РП действия пишем через ** : *пожал руку* *вытащил револьвер*.\n"
        "──────────────────\n"
        "╰☆╮ 10. Общение шепотом: ш-дай списать.\n"
        "──────────────────\n"
        "╰☆╮ 11. Любое нон-рп действие приведет к наказанию.\n"
        "──────────────────\n"
        "╰☆╮ 12. Водить машину разрешено строго с 16 лет и при наличии прав.\n"
        "──────────────────\n"
        "╰☆╮ 13. Действия происходят в штате Нью-Йорк / Эстония. Валюта — Евро (€).\n"
        "──────────────────\n"
        "╰☆╮ 14. При ДТП запрещено уезжать: обязательно заглушите мотор и отыграйте последствия!\n"
        "──────────────────\n"
        "╰☆╮ 15. Нельзя быть владельцем бизнеса если он не зарегистрирован в боте.\n"
        "──────────────────\n"
        "╰☆╮ 16. Запрещены конфликты и ООС-оскорбления участников и администрации.\n"
        "──────────────────\n"
        "╰☆╮ 17. Скины должны соответствовать требованиям вашей работы.\n"
        "──────────────────\n"
        "╰☆╮ 18. Запрещены любые оскорбления администрации и проводящих.\n"
        "──────────────────\n"
        "╰☆╮ 19. Криминал разрешён только если админ перед запуском круглосуточного рп подтвердил это.\n"
        "──────────────────\n"
        "╰☆╮ 20. Официально работать можно с 14 лет (с 14 до 16 без опасных смен и ночных дежурств).\n"
        "──────────────────\n"
        "╰☆╮ 21. Ограничение скорости: в городе 60 км/ч, за городом 120 км/ч.\n"
        "──────────────────\n"
        "╰☆╮ 22. Зеленые зоны (No DM): Детсад, Школа, Спавн.\n"
        "──────────────────\n"
        "╰☆╮ 23. Запрещены мульти-действия в одну строчку. Отыгрывайте каждый шаг отдельно!\n"
        "──────────────────\n"
        "╰☆╮ 24. Вызов экстренных служб: в чат отыгровкой *вызвал 112*.\n\n"
        "╭──────⎝乡⎞──────╮\n"
        " ✈️ ПРАВИЛА ЧАТА TELEGRAM\n"
        "╰━─━─━─≪✦≫─━─━─━╯\n"
        "╰☆╮ 1.1 Запрещён флуд и спам.\n"
        "╰☆╮ 1.2 Реклама в любом виде и распространение ссылок запрещены.\n"
        "╰☆╮ 1.3 Запрещена критика и осуждение участников или сервера.\n"
        "╰☆╮ 1.4 Оскорбление людей категорически запрещено.\n"
        "╰☆╮ 1.5 NSFW контент строго запрещён.\n"
        "╰☆╮ 1.6 Запрещено использовать твинки для накрутки валюты или обхода наказаний (БАН).\n"
        "╰☆╮ 1.7 Запрещены аватары и никнеймы с матами, оскорблениями и пропагандой.\n"
        "╰☆╮ 1.8 Запрещено частое упоминание людей и злоупотребление CAPS LOCK.\n"
        "╰☆╮ 1.9 Соблюдайте тематику чата.\n\n"
        "°˳˚｡ᅠ 彡 Наказания: Предупреждение / Мут / Бан 彡\n"
        "°˳˚｡ᅠ ≼∙Администрация выбирает меру наказания по тяжести нарушения∙≽"
    )

# --- РЕГИСТРАЦИЯ ПАСПОРТА (С СИСТЕМОЙ ЗАЯВОК И ОДОБРЕНИЯ) ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    uname = message.from_user.username or ""

    async with aiosqlite.connect(DB_NAME) as db:
        if uname.lower() in [u.lower() for u in SUPERADMINS]:
            await db.execute("UPDATE players SET is_admin = 1, passport_status = 'approved' WHERE user_id = ?", (user_id,))
            await db.commit()

        async with db.execute("SELECT rp_name, balance, bank_balance, faction, passport_status FROM players WHERE user_id = ?", (user_id,)) as cur:
            user = await cur.fetchone()

    if user:
        p_status = user[4]
        if p_status == "pending":
            await message.answer("⏳ **Ваша анкета на паспорт находится на проверке у Администрации сервера!**\nОжидайте уведомления об одобрении.", parse_mode="Markdown")
            return
        elif p_status == "rejected":
            await message.answer("❌ **Ваша анкета на паспорт была отклонена куратором!**\nПожалуйста, введите ваш игровой **Roblox ник** для повторной подачи заявки:", parse_mode="Markdown")
            await state.set_state(RegState.roblox)
            return

        menu = await get_main_menu(user_id, uname)
        welcome = (
            f"👋 С возвращением в округ, **{user[0]}**!\n"
            f"💵 Наличные: **{user[1]} €** | 💳 Банковский счёт: **{user[2]} €**\n"
            f"🏢 Текущая должность: **{user[3]}**\n\n"
            "Выберите раздел в меню гражданина:"
        )
        await message.answer(welcome, reply_markup=menu, parse_mode="Markdown")
    else:
        text = (
            "🇪🇪 **Добро пожаловать в Rannarik RP (Car RP Estonia)!**\n\n"
            "Для участия на сервере необходимо подать заявку на РП Паспорт гражданина.\n"
            "Введите ваш точный игровой **Roblox никнейм**:"
        )
        await message.answer(text, parse_mode="Markdown")
        await state.set_state(RegState.roblox)

@dp.message(RegState.roblox)
async def reg_roblox(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте ваш Roblox никнейм текстом:")
        return
    await state.update_data(roblox=message.text.strip())
    await message.answer("Отлично! Введите **РП Имя и Фамилию** вашего персонажа (Пример: Мартин Каллас):")
    await state.set_state(RegState.rp_name)

@dp.message(RegState.rp_name)
async def reg_rp_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, введите РП Имя и Фамилию текстом:")
        return
    await state.update_data(rp_name=message.text.strip())
    await message.answer(
        "Укажите **полную дату рождения** персонажа в формате `ДД.ММ.ГГГГ`:\n"
        "(Пример: `15.04.1998` или `01.01.2005`):",
        parse_mode="Markdown"
    )
    await state.set_state(RegState.birth_date)

@dp.message(RegState.birth_date)
async def reg_bdate(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("Пожалуйста, отправьте дату текстом в формате `ДД.ММ.ГГГГ`:")
        return
    text_in = message.text.strip()
    try:
        bdate = datetime.datetime.strptime(text_in, "%d.%m.%Y").date()
        today = datetime.date.today()
        age = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))
        if age < 14 or age > 90:
            await message.answer("❌ Возраст персонажа должен быть от 14 до 90 лет! Введите дату ещё раз:")
            return
    except ValueError:
        await message.answer("❌ Неверный формат! Введите дату строго вида `ДД.ММ.ГГГГ` (например: `01.01.2000`):", parse_mode="Markdown")
        return

    data = await state.get_data()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    is_adm = 1 if username.lower() in [u.lower() for u in SUPERADMINS] else 0
    phone = generate_phone()
    iban = generate_iban()
    status = "approved" if is_adm == 1 else "pending"

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO players 
            (user_id, username, roblox_nick, rp_name, birth_date, phone_number, iban, balance, bank_balance, is_admin, has_coke_boost, is_cuffed, passport_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1000, 4000, ?, 0, 0, ?)
        """, (user_id, username, data["roblox"], data["rp_name"], text_in, phone, iban, is_adm, status))
        await db.commit()

    await state.clear()

    if status == "approved":
        menu = await get_main_menu(user_id, username)
        msg = (
            f"🎉 **Паспорт гражданина Эстонии выдан!**\n\n"
            f"👤 ФИО: **{data['rp_name']}** ({age} лет)\n"
            f"🎮 Roblox: `{data['roblox']}`\n"
            f"📱 SIM-номер: `{phone}`\n"
            f"💳 Счёт Swedbank: `{iban}`\n\n"
            f"💰 Стартовый капитал: **1,000 €** на руках + **4,000 €** в банке."
        )
        await message.answer(msg, reply_markup=menu, parse_mode="Markdown")
    else:
        await message.answer(
            f"📑 **Заявка персонажа {data['rp_name']} успешно отправлена кураторам на проверку!**\n\n"
            "Администрация рассмотрит вашу анкету. Как только паспорт одобрят, бот сразу пришлёт вам уведомление с кнопкой входа в главное меню!",
            parse_mode="Markdown"
        )
        # Отправляем мгновенное уведомление супер-админам
        alert_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Одобрить", callback_data=f"adm_app:{user_id}"),
             InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_rej:{user_id}")]
        ])
        alert_text = (
            f"🚨 **НОВАЯ ЗАЯВКА НА ПАСПОРТ!**\n\n"
            f"👤 РП Имя: **{data['rp_name']}**\n"
            f"🎮 Roblox Ник: `{data['roblox']}`\n"
            f"🎂 Дата рождения: **{text_in}** ({age} лет)\n"
            f"📱 Telegram: @{username} (ID: `{user_id}`)"
        )
        for sa_uname in SUPERADMINS:
            try:
                async with aiosqlite.connect(DB_NAME) as db:
                    async with db.execute("SELECT user_id FROM players WHERE username = ? COLLATE NOCASE", (sa_uname,)) as cur:
                        admin_row = await cur.fetchone()
                if admin_row:
                    await bot.send_message(admin_row[0], alert_text, reply_markup=alert_kb, parse_mode="Markdown")
            except:
                pass

# --- РАБОТА С ЗАЯВКАМИ НА ПАСПОРТ В АДМИНКЕ ---
@dp.callback_query(F.data == "admin:pending_passports")
async def show_pending_passports(call: CallbackQuery):
    if not await is_admin(call.from_user.id, call.from_user.username): return
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, username, roblox_nick, rp_name, birth_date FROM players WHERE passport_status = 'pending'") as cur:
            pending = await cur.fetchall()

    if not pending:
        await call.message.edit_text(
            "✅ **В данный момент нет ожидающих заявок на паспорт!**\nВсе анкеты проверены.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")]]),
            parse_mode="Markdown"
        )
        return

    text = f"📑 **ЗАЯВКИ НА РАССМОТРЕНИИ ({len(pending)} шт.):**\n\n"
    buttons = []
    for p in pending[:8]:
        text += f"• **{p[3]}** | Roblox: `{p[2]}` | ДР: {p[4]} | TG: @{p[1] or 'без_юзера'}\n"
        buttons.append([
            InlineKeyboardButton(text=f"✅ Одобрить {p[3]}", callback_data=f"adm_app:{p[0]}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_rej:{p[0]}")
        ])
    buttons.append([InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("adm_app:"))
async def approve_passport(call: CallbackQuery):
    if not await is_admin(call.from_user.id, call.from_user.username): return
    target_id = int(call.data.split(":")[1])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE players SET passport_status = 'approved' WHERE user_id = ?", (target_id,))
        await db.commit()

    await call.answer("✅ Паспорт успешно одобрен!", show_alert=True)
    try:
        user_menu = await get_main_menu(target_id)
        await bot.send_message(
            target_id,
            "🎉 **ВАША АНКЕТА НА ПАСПОРТ ОДОБРЕНА АДМИНИСТРАЦИЕЙ!**\n\n"
            "Вам выдан паспорт гражданина Эстонии и стартовый капитал 5,000 €.\n"
            "Нажмите /start или кнопку ниже, чтобы начать игру:",
            reply_markup=user_menu,
            parse_mode="Markdown"
        )
    except:
        pass
    await show_pending_passports(call)

@dp.callback_query(F.data.startswith("adm_rej:"))
async def reject_passport(call: CallbackQuery):
    if not await is_admin(call.from_user.id, call.from_user.username): return
    target_id = int(call.data.split(":")[1])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE players SET passport_status = 'rejected' WHERE user_id = ?", (target_id,))
        await db.commit()

    await call.answer("❌ Заявка отклонена!", show_alert=True)
    try:
        await bot.send_message(
            target_id,
            "❌ **Ваша заявка на получение паспорта была отклонена куратором.**\n"
            "Возможно, указаны некорректные данные или ник. Напишите команду /start, чтобы подать анкету повторно.",
            parse_mode="Markdown"
        )
    except:
        pass
    await show_pending_passports(call)

# --- КОМАНДА /POLICE (ТОЛЬКО ДЛЯ ПОЛИЦИИ) ---
@dp.message(Command("police"))
async def cmd_police(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT faction FROM players WHERE user_id = ?", (message.from_user.id,)) as cur:
            caller = await cur.fetchone()

    if not caller or caller[0] not in POLICE_ROLES:
        await message.answer("❌ Доступ к полицейскому терминалу имеют только действующие сотрудники Полиции!")
        return

    police_guide = (
        "👮‍♂️ **СЛУЖЕБНЫЙ ТЕРМИНАЛ ДЕПАРТАМЕНТА ПОЛИЦИИ ЭСТОНИИ**\n\n"
        f"Ваше служебное звание: **{caller[0]}**\n\n"
        "📜 **Список доступных служебных команд:**\n"
        "• `/frisk @username` (или ответом на сообщение) — провести досмотр подозреваемого (проверка документов, категорий прав, инвентаря, транспорта и жилья).\n"
        "• `/cuff @username` (или ответом на сообщение) — надеть / снять наручники по РП.\n"
        "• `/fine @username сумма причина` (или ответом) — выписать официальный штраф со списанием с банковского счёта.\n"
        "• `/arrest @username статья` (или ответом) — арестовать преступника с доставкой в тюрьму (добавляет судимость и лишает права служить в полиции).\n"
        "• `/clearwanted @username` — снять судимости/розыск гражданину (для начальника полиции).\n\n"
        "⚖️ *Соблюдайте правила сервера и отыгрывайте все действия через /me и /do!*"
    )
    await message.answer(police_guide, parse_mode="Markdown")

# --- СЛУЖЕБНЫЕ КОМАНДЫ ПОЛИЦИИ ---
@dp.message(Command("cuff"))
async def cmd_cuff(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT faction FROM players WHERE user_id = ?", (message.from_user.id,)) as cur:
            caller = await cur.fetchone()
    
    if not caller or caller[0] not in POLICE_ROLES:
        await message.answer("❌ Надевать наручники могут только сотрудники Полиции!")
        return

    args = message.text.split()
    target = None
    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT user_id, rp_name, is_cuffed FROM players WHERE user_id = ?", (target_uid,)) as cur:
                target = await cur.fetchone()
    elif len(args) >= 2:
        target_name = args[1].replace("@", "")
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT user_id, rp_name, is_cuffed FROM players WHERE username = ? COLLATE NOCASE", (target_name,)) as cur:
                target = await cur.fetchone()

    if not target:
        await message.answer("📌 Использование: `/cuff @username` или ответом на сообщение `/cuff`", parse_mode="Markdown")
        return

    new_cuff = 0 if target[2] == 1 else 1
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE players SET is_cuffed = ? WHERE user_id = ?", (new_cuff, target[0]))
        await db.commit()

    if new_cuff == 1:
        await message.answer(f"🔒 **{caller[0]}** снял с пояса стальные наручники и заковал гражданина **{target[1]}**!")
    else:
        await message.answer(f"🔓 **{caller[0]}** достал ключ и снял наручники с гражданина **{target[1]}**.")

@dp.message(Command("frisk"))
async def cmd_frisk(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT faction FROM players WHERE user_id = ?", (message.from_user.id,)) as cur:
            caller = await cur.fetchone()

    if not caller or caller[0] not in POLICE_ROLES:
        await message.answer("❌ Проводить обыск могут только сотрудники Полиции!")
        return

    args = message.text.split()
    target = None
    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("""
                SELECT user_id, roblox_nick, rp_name, birth_date, faction, 
                       balance, bank_balance, record_criminal, phone_number,
                       license_a, license_b, license_c, license_d, username
                FROM players WHERE user_id = ?
            """, (target_uid,)) as cur:
                target = await cur.fetchone()
    elif len(args) >= 2:
        target_name = args[1].replace("@", "")
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("""
                SELECT user_id, roblox_nick, rp_name, birth_date, faction, 
                       balance, bank_balance, record_criminal, phone_number,
                       license_a, license_b, license_c, license_d, username
                FROM players WHERE username = ? COLLATE NOCASE
            """, (target_name,)) as cur:
                target = await cur.fetchone()

    if not target:
        await message.answer("📌 Использование: `/frisk @username` или ответом на сообщение `/frisk`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_name FROM inventory WHERE user_id = ?", (target[0],)) as cur:
            items = await cur.fetchall()
        async with db.execute("SELECT model_name, plate_number FROM cars WHERE owner_id = ?", (target[0],)) as cur:
            cars = await cur.fetchall()
        async with db.execute("SELECT house_name FROM houses WHERE owner_id = ?", (target[0],)) as cur:
            houses = await cur.fetchall()

    lic_list = []
    if target[9] == 1: lic_list.append("A (Мото)")
    if target[10] == 1: lic_list.append("B (Легковые)")
    if target[11] == 1: lic_list.append("C (Грузовые)")
    if target[12] == 1: lic_list.append("D (Автобусы)")
    lic_str = ", ".join(lic_list) if lic_list else "ОТСУТСТВУЮТ"

    inv_str = ", ".join([i[0] for i in items]) if items else "Карманы пусты"
    cars_str = ", ".join([f"{c[0]} ({c[1]})" for c in cars]) if cars else "Нет авто"
    houses_str = ", ".join([h[0] for h in houses]) if houses else "Нет жилья"

    report = (
        f"👮‍♂️ **ПРОТОКОЛ ДОСМОТРА И ПОЛИЦЕЙСКОЕ ДОСЬЕ**\n\n"
        f"👤 Личность: **{target[2]}** (@{target[13]})\n"
        f"🎮 Roblox Ник: `{target[1]}`\n"
        f"🎂 Дата рождения: **{target[3]}**\n"
        f"📱 Контактный номер: `{target[8]}`\n"
        f"🏢 Место работы: **{target[4]}**\n"
        f"🚗 Водительские категории: **{lic_str}**\n"
        f"⚖️ Судимостей в базе МВД: **{target[7]}**\n"
        f"💵 Наличные при себе: **{target[5]} €** (В банке: {target[6]} €)\n\n"
        f"🎒 **Обнаруженные предметы и вещи:**\n`{inv_str}`\n\n"
        f"🚘 **Транспортные средства:**\n`{cars_str}`\n\n"
        f"🏠 **Недвижимое имущество:**\n`{houses_str}`\n"
    )
    await message.answer(report, parse_mode="Markdown")

@dp.message(Command("fine"))
async def cmd_fine(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT faction FROM players WHERE user_id = ?", (message.from_user.id,)) as cur:
            caller = await cur.fetchone()
    if not caller or caller[0] not in POLICE_ROLES:
        await message.answer("❌ Выписывать штрафы могут только сотрудники Полиции!")
        return

    args = message.text.split()
    target_uid = None
    target_name = None
    amount = 0
    reason = "Нарушение ПДД"

    if message.reply_to_message and len(args) >= 2:
        target_uid = message.reply_to_message.from_user.id
        try:
            amount = int(args[1])
            reason = " ".join(args[2:]) if len(args) > 2 else "Нарушение ПДД"
        except ValueError:
            await message.answer("❌ Укажите сумму штрафа числом!")
            return
    elif len(args) >= 3:
        target_name = args[1].replace("@", "")
        try:
            amount = int(args[2])
            reason = " ".join(args[3:]) if len(args) > 3 else "Нарушение ПДД"
        except ValueError:
            await message.answer("❌ Укажите сумму штрафа числом!")
            return
    else:
        await message.answer("📌 Использование: `/fine @username сумма причина` или ответом `/fine сумма причина`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        if target_uid:
            async with db.execute("SELECT user_id, bank_balance, rp_name, username FROM players WHERE user_id = ?", (target_uid,)) as cur:
                target = await cur.fetchone()
        else:
            async with db.execute("SELECT user_id, bank_balance, rp_name, username FROM players WHERE username = ? COLLATE NOCASE", (target_name,)) as cur:
                target = await cur.fetchone()

        if not target:
            await message.answer("❌ Нарушитель не найден в базе!")
            return

        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (amount, target[0]))
        await db.commit()

    await message.answer(
        f"🚔 **ШТРАФНАЯ КВИТАНЦИЯ ВЫПИСАНА**\n\n"
        f"👮‍♂️ Офицер: **{caller[0]}**\n"
        f"👤 Нарушитель: **{target[2]}** (@{target[3]})\n"
        f"💶 Сумма штрафа: **{amount} €**\n"
        f"📑 Статья/Причина: *{reason}*\n"
        f"Сумма автоматически удержана с банковского счёта нарушителя.",
        parse_mode="Markdown"
    )

@dp.message(Command("arrest"))
async def cmd_arrest(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT faction FROM players WHERE user_id = ?", (message.from_user.id,)) as cur:
            caller = await cur.fetchone()
    if not caller or caller[0] not in POLICE_ROLES:
        await message.answer("❌ Проводить арест могут только полицейские!")
        return

    args = message.text.split()
    target_uid = None
    target_name = None
    reason = "Тяжкое уголовное преступление"

    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        reason = " ".join(args[1:]) if len(args) > 1 else "Уголовное преступление"
    elif len(args) >= 2:
        target_name = args[1].replace("@", "")
        reason = " ".join(args[2:]) if len(args) > 2 else "Уголовное преступление"
    else:
        await message.answer("📌 Использование: `/arrest @username статья` или ответом `/arrest статья`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        if target_uid:
            async with db.execute("SELECT user_id, rp_name, username FROM players WHERE user_id = ?", (target_uid,)) as cur:
                target = await cur.fetchone()
        else:
            async with db.execute("SELECT user_id, rp_name, username FROM players WHERE username = ? COLLATE NOCASE", (target_name,)) as cur:
                target = await cur.fetchone()

        if not target:
            await message.answer("❌ Гражданин не найден!")
            return

        await db.execute("""
            UPDATE players 
            SET record_criminal = record_criminal + 1, faction = 'Гражданин', is_cuffed = 1 
            WHERE user_id = ?
        """, (target[0],))
        await db.commit()

    await message.answer(
        f"🚨 **ГРАЖДАНИН ЗАДЕРЖАН И ДОСТАВЛЕН В ИВС / ТЮРЬМУ!**\n\n"
        f"👮‍♂️ Провёл задержание: **{caller[0]}**\n"
        f"👤 Осуждённый: **{target[1]}** (@{target[2]})\n"
        f"⚖️ Статья: *{reason}*\n"
        f"⚠️ Игроку добавлена судимость. Доступ к службе в Полиции аннулирован!",
        parse_mode="Markdown"
    )

@dp.message(Command("clearwanted"))
async def cmd_clearwanted(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username):
        await message.answer("❌ Только руководство полиции или администрация могут очищать базу судимостей!")
        return

    args = message.text.split()
    if len(args) < 2 and not message.reply_to_message:
        await message.answer("📌 `/clearwanted @username`", parse_mode="Markdown")
        return

    target_name = args[1].replace("@", "") if len(args) >= 2 else None
    async with aiosqlite.connect(DB_NAME) as db:
        if message.reply_to_message:
            await db.execute("UPDATE players SET record_criminal = 0 WHERE user_id = ?", (message.reply_to_message.from_user.id,))
        else:
            await db.execute("UPDATE players SET record_criminal = 0 WHERE username = ? COLLATE NOCASE", (target_name,))
        await db.commit()

    await message.answer(f"⚖️ Все судимости гражданина успешно удалены из базы данных МВД!")

# --- БИРЖА ТРУДА ---
@dp.callback_query(F.data == "menu:jobs")
async def menu_jobs(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT birth_date, record_criminal, faction, license_b, license_c, license_d 
            FROM players WHERE user_id = ?
        """, (call.from_user.id,)) as cur:
            u = await cur.fetchone()

    if not u: return
    buttons = []
    for role, sal in SALARIES.items():
        if role in ["Модератор", "Констебль", "Главный Констебль"]: continue
        buttons.append([InlineKeyboardButton(text=f"{role} — {sal} €/сессия", callback_data=f"setjob:{role}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])

    text = (
        f"💼 **ЦЕНТР ЗАНЯТОСТИ И БИРЖА ТРУДА**\n\n"
        f"Ваша текущая профессия: **{u[2]}**\n"
        f"⚖️ Судимостей в базе: **{u[1]}**\n\n"
        "⚠️ **Требования к трудоустройству:**\n"
        "• Младший Констебль, Дальнобойщик, Пожарный — строго с 16 лет!\n"
        "• **Дальнобойщик** требует водительские права категории **C**!\n"
        "• **Водитель Автобуса** требует права категории **D**!\n"
        "• **В полицию** можно устроиться только на должность **Младший Констебль** (требуются права B и отсутствие судимостей)!\n"
        "• 🎖 Повышение до Констебля и Главного Констебля происходит **строго через отчёты в чате** решением Администрации / Шефа!\n"
        "• Запрещено совмещать полицию с криминалом или скорой.\n\n"
        "Выберите желаемую профессию:"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("setjob:"))
async def callback_setjob(call: CallbackQuery):
    role = call.data.split(":")[1]
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT birth_date, record_criminal, faction, license_b, license_c, license_d 
            FROM players WHERE user_id = ?
        """, (user_id,)) as cur:
            u = await cur.fetchone()

        bdate = datetime.datetime.strptime(u[0], "%d.%m.%Y").date()
        age = datetime.date.today().year - bdate.year

        if age < 16 and role in ["Дальнобойщик", "Младший Констебль", "Пожарный"]:
            await call.answer("❌ Опасные и ночные работы доступны только с 16 лет по правилу №20!", show_alert=True)
            return

        if role == "Дальнобойщик" and u[4] == 0:
            await call.answer("❌ Для работы Дальнобойщиком нужны права категории C! Сдайте экзамен в Автошколе.", show_alert=True)
            return
        if role == "Водитель Автобуса" and u[5] == 0:
            await call.answer("❌ Для работы Водителем Автобуса нужны права категории D! Сдайте экзамен в Автошколе.", show_alert=True)
            return

        if role in POLICE_ROLES:
            if u[3] == 0:
                await call.answer("❌ Для службы в полиции необходимо иметь права категории B!", show_alert=True)
                return
            if u[1] > 0:
                await call.answer("❌ Доступ в Полицию закрыт навсегда из-за судимостей в базе МВД!", show_alert=True)
                return

        if role in ["Бандит", "Наркоторговец"] and u[2] in POLICE_ROLES:
            await call.answer("❌ Офицер полиции не может совмещать службу с криминалом!", show_alert=True)
            return

        await db.execute("UPDATE players SET faction = ? WHERE user_id = ?", (role, user_id))
        await db.commit()

    extra_msg = ""
    if role in POLICE_ROLES:
        extra_msg = "\n\n👮‍♂️ **Внимание:** Ознакомьтесь со служебными полномочиями и командами через команду `/police`."

    await call.answer(f"✅ Вы успешно трудоустроились: {role}!", show_alert=True)
    menu = await get_main_menu(call.from_user.id, call.from_user.username)
    await call.message.edit_text(f"Поздравляем! Ваша новая должность: **{role}**.{extra_msg}", reply_markup=menu, parse_mode="Markdown")

# --- ПОДТВЕРЖДЕНИЕ ПОКУПКИ АВТОМОБИЛЯ ---
@dp.callback_query(F.data.startswith("buycar:"))
async def ask_confirm_car(call: CallbackQuery):
    car_key = call.data.split(":")[1]
    car_info = CAR_CATALOG.get(car_key)
    if not car_info: return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, купить", callback_data=f"confirm_car:{car_key}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="menu:dealership")]
    ])
    text = (
        f"🚘 **ПОДТВЕРЖДЕНИЕ СДЕЛКИ (АВТОСАЛОН)**\n\n"
        f"Вы действительно хотите приобрести:\n"
        f"• Модель: **{car_info['name']}**\n"
        f"• Требуемая категория прав: **{car_info['cat']}**\n"
        f"• Стоимость покупки: **{car_info['price']} €**\n"
        f"• Налог за сессию: **{car_info['tax']} €**\n\n"
        "Сумма будет списана с вашего счёта в банке Swedbank."
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("confirm_car:"))
async def execute_buy_car(call: CallbackQuery):
    car_key = call.data.split(":")[1]
    car_info = CAR_CATALOG.get(car_key)
    user_id = call.from_user.id
    req_cat = car_info["cat"]

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT bank_balance, license_a, license_b, license_c, license_d 
            FROM players WHERE user_id = ?
        """, (user_id,)) as cur:
            u = await cur.fetchone()

        if req_cat != "Без прав":
            has_lic = False
            if req_cat == "A" and u[1] == 1: has_lic = True
            elif req_cat == "B" and u[2] == 1: has_lic = True
            elif req_cat == "C" and u[3] == 1: has_lic = True
            elif req_cat == "D" and u[4] == 1: has_lic = True

            if not has_lic:
                await call.answer(f"❌ Для покупки этой техники нужны права категории {req_cat}!", show_alert=True)
                return

        if u[0] < car_info["price"]:
            await call.answer("❌ Недостаточно средств на банковском счёте!", show_alert=True)
            return

        plate = generate_plate()
        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (car_info["price"], user_id))
        await db.execute("INSERT INTO cars (owner_id, model_name, plate_number, tax) VALUES (?, ?, ?, ?)",
                         (user_id, car_info["name"], plate, car_info["tax"]))
        await db.commit()

    text = (
        f"🎉 **ПОЗДРАВЛЯЕМ С ПРИОБРЕТЕНИЕМ ТРАНСПОРТА!**\n\n"
        f"🚘 Модель: **{car_info['name']}**\n"
        f"🔢 Присвоен госномер: `{plate}`\n"
        f"📑 Налог за сессию: **{car_info['tax']} €**\n\n"
        "Техника зарегистрирована в ГИБДД/Полиции и доставлена в Гараж!"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="menu:home")]]), parse_mode="Markdown")

# --- ПОДТВЕРЖДЕНИЕ ПОКУПКИ НЕДВИЖИМОСТИ ---
@dp.callback_query(F.data.startswith("buyhouse:"))
async def ask_confirm_house(call: CallbackQuery):
    h_key = call.data.split(":")[1]
    house = HOUSE_CATALOG.get(h_key)
    if not house: return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, купить жильё", callback_data=f"confirm_house:{h_key}"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="menu:estate_agency")]
    ])
    text = (
        f"🏡 **ПОДТВЕРЖДЕНИЕ ПОКУПКИ ЖИЛЬЯ**\n\n"
        f"Вы приобретаете: **{house['name']}**\n"
        f"• Стоимость оформления: **{house['price']} €**\n"
        f"• Налог на имущество: **{house['tax']} €** за сессию\n\n"
        "Подтвердить сделку?"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("confirm_house:"))
async def execute_buy_house(call: CallbackQuery):
    h_key = call.data.split(":")[1]
    house = HOUSE_CATALOG.get(h_key)
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            u = await cur.fetchone()
        if not u or u[0] < house["price"]:
            await call.answer("❌ Недостаточно средств на банковском счёте!", show_alert=True)
            return

        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (house["price"], user_id))
        await db.execute("INSERT INTO houses (owner_id, house_key, house_name, tax) VALUES (?, ?, ?, ?)",
                         (user_id, h_key, house["name"], house["tax"]))
        await db.commit()

    await call.message.edit_text(
        f"🎉 **ПОЗДРАВЛЯЕМ С ПОКУПКОЙ НЕДВИЖИМОСТИ!**\n\n"
        f"🏠 Объект: **{house['name']}**\n"
        f"📑 Налог на имущество: **{house['tax']} €** за сессию.\n"
        "Ключи внесены в реестр!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="menu:home")]])
    )

# --- АВТОШКОЛА ---
@dp.callback_query(F.data == "menu:driving_school")
async def show_driving_school(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT license_a, license_b, license_c, license_d, birth_date 
            FROM players WHERE user_id = ?
        """, (call.from_user.id,)) as cur:
            u = await cur.fetchone()

    if not u: return
    bdate = datetime.datetime.strptime(u[4], "%d.%m.%Y").date()
    age = datetime.date.today().year - bdate.year

    buttons = [
        [InlineKeyboardButton(
            text=f"🏍️ Категория A (Мото) — {EXAM_FEES['A']} €" + (" [СДАН]" if u[0]==1 else ""),
            callback_data="exam_start:A"
        )],
        [InlineKeyboardButton(
            text=f"🚗 Категория B (Легковые) — {EXAM_FEES['B']} €" + (" [СДАН]" if u[1]==1 else ""),
            callback_data="exam_start:B"
        )],
        [InlineKeyboardButton(
            text=f"🚛 Категория C (Грузовые) — {EXAM_FEES['C']} €" + (" [СДАН]" if u[2]==1 else ""),
            callback_data="exam_start:C"
        )],
        [InlineKeyboardButton(
            text=f"🚌 Категория D (Автобусы) — {EXAM_FEES['D']} €" + (" [СДАН]" if u[3]==1 else ""),
            callback_data="exam_start:D"
        )],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")]
    ]

    text = (
        "🚦 **ДЕПАРТАМЕНТ ТРАНСПОРТА / АВТОШКОЛА ЭСТОНИИ**\n\n"
        f"Ваш возраст: **{age} лет**\n\n"
        "📜 **Доступные категории водительских удостоверений:**\n"
        "• **Категория A** (Мотоциклы, квадроциклы) — с 16 лет\n"
        "• **Категория B** (Легковые авто, джипы) — с 16 лет\n"
        "• **Категория C** (Грузовики, Scania, Iveco) — с 18 лет\n"
        "• **Категория D** (Пассажирские автобусы Ikarus) — с 18 лет\n\n"
        "Выберите категорию для сдачи квалификационного экзамена:"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("exam_start:"))
async def exam_start(call: CallbackQuery):
    cat = call.data.split(":")[1]
    fee = EXAM_FEES[cat]
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT license_a, license_b, license_c, license_d, birth_date, balance, bank_balance 
            FROM players WHERE user_id = ?
        """, (user_id,)) as cur:
            u = await cur.fetchone()

    bdate = datetime.datetime.strptime(u[4], "%d.%m.%Y").date()
    age = datetime.date.today().year - bdate.year

    if cat in ["A", "B"] and age < 16:
        await call.answer("❌ Сдача на категории A и B разрешена только с 16 лет!", show_alert=True)
        return
    if cat in ["C", "D"] and age < 18:
        await call.answer("❌ Управление грузовиками и автобусами (C, D) разрешено строго с 18 лет!", show_alert=True)
        return

    cat_idx = {"A": 0, "B": 1, "C": 2, "D": 3}[cat]
    if u[cat_idx] == 1:
        await call.answer(f"✅ У вас уже открыта категория {cat}!", show_alert=True)
        return

    total_money = u[5] + u[6]
    if total_money < fee:
        await call.answer(f"❌ Экзамен стоит {fee} €! У вас недостаточно средств.", show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A) 60 км/ч в черте города, 120 км/ч на трассе", callback_data=f"exam_done:{cat}:correct")],
        [InlineKeyboardButton(text="B) 90 км/ч везде", callback_data=f"exam_done:{cat}:wrong")],
        [InlineKeyboardButton(text="C) Максимальная скорость без ограничений", callback_data=f"exam_done:{cat}:wrong")],
    ])
    text = (
        f"📝 **ТЕОРЕТИЧЕСКИЙ ЭКЗАМЕН НА КАТЕГОРИЮ {cat}**\n\n"
        f"💵 Стоимость гос. пошлины: **{fee} €**\n"
        "Вопрос: *Каковы установленные скоростные ограничения по правилу №21 сервера?*"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("exam_done:"))
async def exam_done(call: CallbackQuery):
    _, cat, res = call.data.split(":")
    fee = EXAM_FEES[cat]
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance, bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            u = await cur.fetchone()
        
        if u[0] >= fee:
            await db.execute("UPDATE players SET balance = balance - ? WHERE user_id = ?", (fee, user_id))
        else:
            await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (fee, user_id))

        if res == "correct":
            col = {"A": "license_a", "B": "license_b", "C": "license_c", "D": "license_d"}[cat]
            await db.execute(f"UPDATE players SET {col} = 1 WHERE user_id = ?", (user_id,))
            await db.commit()
            await call.message.edit_text(
                f"🎉 **ПОЗДРАВЛЯЕМ! ВЫ СДАЛИ ЭКЗАМЕН НА КАТЕГОРИЮ {cat}!**\n\n"
                f"Списана пошлина: **{fee} €**.\n"
                f"Категория официально открыта в вашем удостоверении.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В автошколу", callback_data="menu:driving_school")]])
            )
        else:
            await db.commit()
            await call.message.edit_text(
                f"❌ **Экзамен не сдан!**\nПошлина {fee} € удержана.\nПовторите правила и попробуйте снова.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В автошколу", callback_data="menu:driving_school")]])
            )

# --- ПРЕМИУМ-МАГАЗИН ОБОРУДОВАНИЯ ---
@dp.callback_query(F.data == "menu:bonus_shop")
async def show_bonus_shop(call: CallbackQuery):
    buttons = []
    for k, v in BONUS_ITEMS.items():
        buttons.append([InlineKeyboardButton(text=f"{v['name']} — {v['price']} €", callback_data=f"buybonus:{k}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])

    text = (
        "💎 **МАГАЗИН ЭЛИТНОГО ОБОРУДОВАНИЯ И ПРЕДМЕТОВ**\n\n"
        "Каждый из этих предметов даёт постоянный пассивный бонус к вашей выплате на РП сессиях!\n"
        "Их можно хранить в инвентаре или перепродавать другим игрокам на **5vito**.\n\n"
        "• **Чемодан инвестора** (+10% к доходу)\n"
        "• **Ноутбук криптотрейдера** (+20% к доходу)\n"
        "• **Часы Rolex** (+35% к доходу)\n"
        "• **Перстень магната** (+50% к доходу)\n\n"
        "Выберите предмет для покупки:"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buybonus:"))
async def buy_bonus_item(call: CallbackQuery):
    it_key = call.data.split(":")[1]
    item = BONUS_ITEMS.get(it_key)
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            u = await cur.fetchone()
        
        if not u or u[0] < item["price"]:
            await call.answer("❌ Недостаточно средств на банковском счёте!", show_alert=True)
            return

        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (item["price"], user_id))
        await db.execute("INSERT INTO inventory (user_id, item_name) VALUES (?, ?)", (user_id, item["name"]))
        await db.commit()

    await call.message.edit_text(
        f"🎉 **ПОЗДРАВЛЯЕМ С ПРИОБРЕТЕНИЕМ!**\n\n"
        f"Вы купили: **{item['name']}**\n"
        f"Эффект: **+{item['bonus_pct']}%** к доходу за сессию!\n"
        "Предмет добавлен в инвентарь. Вы в любой момент можете выставить его на 5vito.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В магазин", callback_data="menu:bonus_shop")]])
    )

# --- 5VITO МАРКЕТПЛЕЙС ---
@dp.callback_query(F.data == "menu:5vito")
async def show_5vito(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_id, title, price, seller_name, seller_username FROM market") as cur:
            items = await cur.fetchall()

    buttons = []
    text = "🛒 **ТОРГОВАЯ ПЛОЩАДКА 5VITO (ОБЪЯВЛЕНИЯ ЖИТЕЛЕЙ)**\n\n"
    if not items:
        text += "В данный момент активных объявлений нет. Вы можете продать любой предмет из своего инвентаря!"
    else:
        for it in items:
            uname_str = f"@{it[4]}" if it[4] else it[3]
            text += f"📦 **{it[1]}** — **{it[2]} €**\n👤 Продавец: {it[3]} ({uname_str})\n──────────────────\n"
            buttons.append([InlineKeyboardButton(text=f"Купить {it[1]} ({it[2]} €)", callback_data=f"buymarket:{it[0]}")])

    buttons.append([InlineKeyboardButton(text="➕ Выставить свой предмет на продажу", callback_data="5vito:sell_item")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data == "5vito:sell_item")
async def sell_item_pick(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT id, item_name FROM inventory WHERE user_id = ?", (user_id,)) as cur:
            items = await cur.fetchall()

    if not items:
        await call.answer("❌ У вас в инвентаре нет предметов для продажи!", show_alert=True)
        return

    buttons = []
    for it in items:
        buttons.append([InlineKeyboardButton(text=it[1], callback_data=f"select_sell:{it[0]}")])
    buttons.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="menu:5vito")])

    await call.message.edit_text("Выберите предмет из вашего инвентаря, который вы хотите продать на 5vito:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@dp.callback_query(F.data.startswith("select_sell:"))
async def select_sell_price(call: CallbackQuery, state: FSMContext):
    inv_id = int(call.data.split(":")[1])
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_name FROM inventory WHERE id = ?", (inv_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        await call.answer("Предмет не найден!", show_alert=True)
        return

    await state.update_data(inv_id=inv_id, item_title=row[0])
    await call.message.edit_text(f"Выбран предмет: **{row[0]}**.\n\nВведите цену продажи в **Евро (€)**:", parse_mode="Markdown")
    await state.set_state(SellSelectState.price)

@dp.message(SellSelectState.price)
async def confirm_sell(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Введите цену числом:")
        return

    price = int(message.text)
    data = await state.get_data()
    user_id = message.from_user.id
    seller_name = message.from_user.full_name
    seller_uname = message.from_user.username or ""

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM inventory WHERE id = ?", (data["inv_id"],))
        await db.execute("""
            INSERT INTO market (seller_id, seller_name, seller_username, title, price)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, seller_name, seller_uname, data["item_title"], price))
        await db.commit()

    await state.clear()
    await message.answer(
        f"✅ Объявление опубликовано!\nТовар **{data['item_title']}** выставлен на 5vito за **{price} €**.\n"
        f"Покупатели свяжутся с вами через @{seller_uname}.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛒 На 5vito", callback_data="menu:5vito")]]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("buymarket:"))
async def buy_market(call: CallbackQuery):
    item_id = int(call.data.split(":")[1])
    user_id = call.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_id, title, price, seller_id, seller_name FROM market WHERE item_id = ?", (item_id,)) as cur:
            item = await cur.fetchone()
        if not item:
            await call.answer("❌ Товар уже продан!", show_alert=True)
            return

        async with db.execute("SELECT bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            buyer = await cur.fetchone()
        if not buyer or buyer[0] < item[2]:
            await call.answer("❌ Недостаточно средств на банковском счёте!", show_alert=True)
            return

        # Перевод денег продавцу
        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (item[2], user_id))
        await db.execute("UPDATE players SET bank_balance = bank_balance + ? WHERE user_id = ?", (item[2], item[3]))
        # Выдача товара
        await db.execute("INSERT INTO inventory (user_id, item_name) VALUES (?, ?)", (user_id, item[1]))
        await db.execute("DELETE FROM market WHERE item_id = ?", (item_id,))
        await db.commit()

    await call.answer("✅ Товар успешно куплен и перемещён в ваш инвентарь!", show_alert=True)
    await show_5vito(call)

# --- АВТОСАЛОН С КАТЕГОРИЯМИ ---
@dp.callback_query(F.data == "menu:dealership")
async def show_dealership(call: CallbackQuery):
    buttons = []
    for k, v in list(CAR_CATALOG.items())[:12]:
        buttons.append([InlineKeyboardButton(text=f"{v['name']} [{v['cat']}] — {v['price']} €", callback_data=f"buycar:{k}")])
    buttons.append([InlineKeyboardButton(text="➡️ Следующая страница", callback_data="dealership:page2")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])

    text = "🚘 **ОФИЦИАЛЬНЫЙ АВТОСАЛОН ЭСТОНИИ (CAR CRASH SIMULATOR)**\n\nВыберите транспортное средство для покупки:"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data == "dealership:page2")
async def show_dealership_p2(call: CallbackQuery):
    buttons = []
    for k, v in list(CAR_CATALOG.items())[12:]:
        buttons.append([InlineKeyboardButton(text=f"{v['name']} [{v['cat']}] — {v['price']} €", callback_data=f"buycar:{k}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Предыдущая страница", callback_data="menu:dealership")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])

    text = "🚘 **АВТОСАЛОН (СТРАНИЦА 2)**\n\nВыберите технику:"
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- НЕДВИЖИМОСТЬ В ГОРОДЕ ---
@dp.callback_query(F.data == "menu:estate_agency")
async def show_estate(call: CallbackQuery):
    buttons = []
    for k, v in HOUSE_CATALOG.items():
        buttons.append([InlineKeyboardButton(text=f"{v['name']} — {v['price']} € (Налог: {v['tax']}€)", callback_data=f"buyhouse:{k}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])

    text = (
        "🏡 **РИЕЛТОРСКОЕ АГЕНТСТВО RANNARIK RP**\n\n"
        "Вся недвижимость находится непосредственно в черте города:\n"
        "• **Квартиры в городе** — доступное жилье\n"
        "• **Обычные дома** — комфорт и собственный гараж\n"
        "• **Люкс дома** — престиж и статус\n\n"
        "Выберите объект для покупки:"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

# --- БИЗНЕСЫ ОКРУГА ---
@dp.callback_query(F.data == "menu:businesses")
async def show_biz(call: CallbackQuery):
    buttons = []
    for k, v in BUSINESS_CATALOG.items():
        buttons.append([InlineKeyboardButton(text=f"{v['name']} ({v['price']} €)", callback_data=f"buybiz:{k}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])
    text = (
        "🏭 **КОММЕРЧЕСКИЕ ПРЕДПРИЯТИЯ ГОРОДА**\n\n"
        "Бизнес приносит гарантированный чистый доход после каждой проведенной РП сессии:\n"
        "• **СТО** (Автомастерская)\n"
        "• **Автобусное Депо**\n"
        "• **АЗС Circle K**\n"
        "• **База дальнобойщиков**\n\n"
        "Выберите объект для инвестирования:"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buybiz:"))
async def buy_biz(call: CallbackQuery):
    biz_key = call.data.split(":")[1]
    biz = BUSINESS_CATALOG.get(biz_key)
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            u = await cur.fetchone()
        if not u or u[0] < biz["price"]:
            await call.answer("❌ Недостаточно средств в банке!", show_alert=True)
            return

        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (biz["price"], user_id))
        await db.execute("INSERT INTO businesses (owner_id, biz_key, biz_name, income, tax) VALUES (?, ?, ?, ?, ?)",
                         (user_id, biz_key, biz["name"], biz["income"], biz["tax"]))
        await db.commit()

    await call.message.edit_text(
        f"🏢 **ПРЕДПРИЯТИЕ УСПЕШНО ЗАРЕГИСТРИРОВАНО!**\n\n"
        f"Название: **{biz['name']}**\n"
        f"📈 Доход за сессию: **+{biz['income']} €** (Налог: {biz['tax']} €).",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="menu:home")]])
    )

# --- ТЁМНЫЙ РЫНОК ---
@dp.callback_query(F.data == "menu:darkshop")
async def show_darkshop(call: CallbackQuery):
    buttons = []
    for k, v in DARK_ITEMS.items():
        buttons.append([InlineKeyboardButton(text=f"{v['name']} — {v['price']} €", callback_data=f"buydark:{k}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")])
    text = (
        "🕵️ **DARKNET КАТАЛОГ RANNARIK RP**\n\n"
        "☠️ *Внимание: полиция конфискует эти предметы при обыске!*\n"
        "• **Кокаин (Кокс)** даёт разовый буст: **+35% к выплате за следующую сессию**!\n\n"
        "Выберите нелегальный товар:"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buydark:"))
async def buy_dark(call: CallbackQuery):
    it = DARK_ITEMS.get(call.data.split(":")[1])
    user_id = call.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance, bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            u = await cur.fetchone()
        if not u or (u[0] + u[1]) < it["price"]:
            await call.answer("❌ Недостаточно средств!", show_alert=True)
            return

        if u[0] >= it["price"]:
            await db.execute("UPDATE players SET balance = balance - ? WHERE user_id = ?", (it["price"], user_id))
        else:
            await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (it["price"], user_id))

        await db.execute("INSERT INTO inventory (user_id, item_name) VALUES (?, ?)", (user_id, it["name"]))
        if it.get("is_coke"):
            await db.execute("UPDATE players SET has_coke_boost = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

    msg = f"✅ Вы приобрели: {it['name']}!"
    if it.get("is_coke"):
        msg += "\n⚡ Буст +35% активирован строго на следующую сессию!"
    await call.message.edit_text(msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:darkshop")]]))

# --- БАНК SWEDBANK И ПЕРЕВОДЫ ---
@dp.callback_query(F.data == "menu:bank")
async def show_bank(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT rp_name, balance, bank_balance, iban FROM players WHERE user_id = ?", (call.from_user.id,)) as cur:
            u = await cur.fetchone()

    if not u: return
    text = (
        f"🏦 **БАНК ЭСТОНИИ (SWEDBANK)**\n"
        f"Клиент: **{u[0]}**\n\n"
        f"💳 Номер счёта (IBAN):\n`{u[3]}`\n\n"
        f"💵 Наличные в кошельке: **{u[1]} €**\n"
        f"💳 Счёт в банке: **{u[2]} €**\n"
        f"📊 Общее состояние: **{u[1] + u[2]} €**\n\n"
        "Выберите операцию:"
    )
    await call.message.edit_text(text, reply_markup=get_bank_menu(), parse_mode="Markdown")

@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance, bank_balance, donate_coins, iban FROM players WHERE user_id = ?", (message.from_user.id,)) as cur:
            row = await cur.fetchone()
    if not row:
        await message.answer("❌ Сначала зарегистрируйтесь через /start")
        return
    text = (
        f"📊 **ВАШИ ФИНАНСЫ:**\n"
        f"💵 Наличные купюры: **{row[0]} €**\n"
        f"💳 Банковский счёт: **{row[1]} €**\n"
        f"💎 Донат-счёт: **{row[2]} Coins**\n"
        f"🏦 IBAN: `{row[3]}`"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("give"))
@dp.message(Command("pay"))
async def cmd_give(message: Message):
    args = message.text.split()
    sender_id = message.from_user.id

    if message.reply_to_message and len(args) >= 2:
        target_user_id = message.reply_to_message.from_user.id
        try:
            amount = int(args[1])
            if amount <= 0: raise ValueError
        except ValueError:
            await message.answer("❌ Укажите сумму числом!")
            return
        
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT balance, bank_balance FROM players WHERE user_id = ?", (sender_id,)) as cur:
                sender = await cur.fetchone()
            if not sender or (sender[0] + sender[1]) < amount:
                await message.answer("❌ Недостаточно средств!")
                return

            if sender[1] >= amount:
                await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (amount, sender_id))
            else:
                rem = amount - sender[1]
                await db.execute("UPDATE players SET bank_balance = 0, balance = balance - ? WHERE user_id = ?", (rem, sender_id))

            await db.execute("UPDATE players SET bank_balance = bank_balance + ? WHERE user_id = ?", (amount, target_user_id))
            await db.commit()

        await message.answer(f"✅ Перевод на сумму **{amount} €** успешно отправлен!", parse_mode="Markdown")
        return

    if len(args) < 3:
        await message.answer("📌 **Использование:**\n• `/give @username сумма`\n• Или ответом на сообщение игрока: `/give сумма`", parse_mode="Markdown")
        return

    target_uname = args[1].replace("@", "")
    try:
        amount = int(args[2])
        if amount <= 0: raise ValueError
    except ValueError:
        await message.answer("❌ Укажите корректную сумму!")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance, bank_balance FROM players WHERE user_id = ?", (sender_id,)) as cur:
            sender = await cur.fetchone()
        if not sender or (sender[0] + sender[1]) < amount:
            await message.answer("❌ Недостаточно денег!")
            return

        async with db.execute("SELECT user_id, rp_name FROM players WHERE username = ? COLLATE NOCASE", (target_uname,)) as cur:
            target = await cur.fetchone()
        if not target:
            await message.answer(f"❌ Пользователь @{target_uname} не зарегистрирован!")
            return

        if sender[1] >= amount:
            await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (amount, sender_id))
        else:
            rem = amount - sender[1]
            await db.execute("UPDATE players SET bank_balance = 0, balance = balance - ? WHERE user_id = ?", (rem, sender_id))

        await db.execute("UPDATE players SET bank_balance = bank_balance + ? WHERE user_id = ?", (amount, target[0]))
        await db.commit()

    await message.answer(f"✅ Банковский перевод **{amount} €** для **{target[1]}** (@{target_uname}) выполнен!", parse_mode="Markdown")

@dp.callback_query(F.data == "bank:transfer_start")
async def b_trans_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите **Telegram @username** получателя:\n(Пример: `@egorka80000`)", parse_mode="Markdown")
    await state.set_state(BankTransferState.target)

@dp.message(BankTransferState.target)
async def b_trans_target(message: Message, state: FSMContext):
    target = message.text.replace("@", "").strip()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, rp_name FROM players WHERE username = ? COLLATE NOCASE", (target,)) as cur:
            row = await cur.fetchone()
    if not row:
        await message.answer("❌ Гражданин не найден! Введите юзернейм ещё раз:")
        return
    await state.update_data(target_id=row[0], target_name=row[1], target_username=target)
    await message.answer(f"Получатель: **{row[1]}**.\nВведите сумму перевода в **Евро (€)**:")
    await state.set_state(BankTransferState.amount)

@dp.message(BankTransferState.amount)
async def b_trans_amount(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Введите сумму числом:")
        return
    amount = int(message.text)
    data = await state.get_data()
    sender_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT bank_balance FROM players WHERE user_id = ?", (sender_id,)) as cur:
            bal = (await cur.fetchone())[0]
        if bal < amount:
            await message.answer(f"❌ На банковском счёте недостаточно средств! Доступно: {bal} €")
            await state.clear()
            return

        await db.execute("UPDATE players SET bank_balance = bank_balance - ? WHERE user_id = ?", (amount, sender_id))
        await db.execute("UPDATE players SET bank_balance = bank_balance + ? WHERE user_id = ?", (amount, data["target_id"]))
        await db.commit()

    await state.clear()
    await message.answer(
        f"💸 **Перевод отправлен!**\nСумма: **{amount} €**\nПолучатель: **{data['target_name']}** (@{data['target_username']})",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏦 В банк", callback_data="menu:bank")]]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "bank:deposit_start")
async def b_dep_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Какую сумму **наличных** положить на банковский счёт?\nВведите число в евро:")
    await state.set_state(BankDepositState.amount)

@dp.message(BankDepositState.amount)
async def b_dep_amount(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Введите число:")
        return
    amount = int(message.text)
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            cash = (await cur.fetchone())[0]
        if cash < amount:
            await message.answer(f"❌ У вас только {cash} € наличных!")
            await state.clear()
            return

        await db.execute("UPDATE players SET balance = balance - ?, bank_balance = bank_balance + ? WHERE user_id = ?", (amount, amount, user_id))
        await db.commit()

    await state.clear()
    await message.answer(f"📥 На счёт Swedbank зачислено **{amount} €**!",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏦 В банк", callback_data="menu:bank")]]),
                         parse_mode="Markdown")

@dp.callback_query(F.data == "bank:withdraw_start")
async def b_with_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Какую сумму снять в банкомате?\nВведите число в евро:")
    await state.set_state(BankWithdrawState.amount)

@dp.message(BankWithdrawState.amount)
async def b_with_amount(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Введите число:")
        return
    amount = int(message.text)
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT bank_balance FROM players WHERE user_id = ?", (user_id,)) as cur:
            bank = (await cur.fetchone())[0]
        if bank < amount:
            await message.answer(f"❌ На счёте недостаточно денег! Доступно: {bank} €")
            await state.clear()
            return

        await db.execute("UPDATE players SET bank_balance = bank_balance - ?, balance = balance + ? WHERE user_id = ?", (amount, amount, user_id))
        await db.commit()

    await state.clear()
    await message.answer(f"📤 Банкомат выдал **{amount} €** наличными!",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏦 В банк", callback_data="menu:bank")]]),
                         parse_mode="Markdown")

# --- ПРОФИЛЬ, ГАРАЖ, ДОМА, ПРАВИЛА ---
@dp.callback_query(F.data == "menu:profile")
async def show_profile(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT roblox_nick, rp_name, birth_date, phone_number, faction, 
                   balance, bank_balance, donate_coins, sessions_count, record_criminal, 
                   is_vip, has_coke_boost, iban, license_a, license_b, license_c, license_d, is_cuffed
            FROM players WHERE user_id = ?
        """, (call.from_user.id,)) as cur:
            u = await cur.fetchone()

    lic_list = []
    if u[13] == 1: lic_list.append("A")
    if u[14] == 1: lic_list.append("B")
    if u[15] == 1: lic_list.append("C")
    if u[16] == 1: lic_list.append("D")
    lic_str = ", ".join(lic_list) if lic_list else "Отсутствуют"

    crim_str = "Чиста" if u[9] == 0 else f"⚠️ Судимостей: {u[9]}"
    vip_str = " 👑 VIP" if u[10] == 1 else ""
    cuff_str = "\n⛓️ **ВЫ СЕЙЧАС В НАРУЧНИКАХ!**" if u[17] == 1 else ""
    boost_str = "\n⚡ Активен буст с кокса (+35% к выплате за сессию)!" if u[11] == 1 else ""

    mult = await get_inventory_multiplier(call.from_user.id)
    bonus_str = f"\n💎 Бонус оборудования: **+{int((mult - 1.0) * 100)}%** к ЗП" if mult > 1.0 else ""

    text = (
        f"╭──────⎝乡⎞──────╮\n"
        f"   🪪 ПАСПОРТ ГРАЖДАНИНА{vip_str}\n"
        f"╰━─━─━─≪✦≫─━─━─━╯\n"
        f"👤 Гражданин: **{u[1]}**\n"
        f"🎮 Roblox Ник: `{u[0]}`\n"
        f"🎂 Дата рождения: **{u[2]}**\n"
        f"📱 Номер телефона: `{u[3]}`\n"
        f"🏢 Должность: **{u[4]}**\n"
        f"🚗 Водительские права: **{lic_str}**\n"
        f"⚖️ История судимостей: **{crim_str}**{cuff_str}\n\n"
        f"💰 **Финансовое состояние:**\n"
        f"💵 Наличные купюры: **{u[5]} €**\n"
        f"💳 Банковский счёт (Swedbank): **{u[6]} €**\n"
        f"🏦 Номер IBAN: `{u[12]}`\n"
        f"💎 Донат баланс: **{u[7]} Coins**\n"
        f"⏱ Проведено РП сессий: **{u[8]}**{boost_str}{bonus_str}\n"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В меню", callback_data="menu:home")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "menu:garage")
async def show_garage(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT model_name, plate_number, tax FROM cars WHERE owner_id = ?", (call.from_user.id,)) as cur:
            cars = await cur.fetchall()

    if not cars:
        await call.message.edit_text("🚗 Ваш гараж пуст. Приобретите авто в Автосалоне!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")]]))
        return

    text = "🚗 **ВАШ АВТОПАРК:**\n\n" + "\n".join([f"• **{c[0]}** | Номер: `{c[1]}` (Налог: {c[2]}€)" for c in cars])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "menu:my_houses")
async def show_my_houses(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT house_name, tax FROM houses WHERE owner_id = ?", (call.from_user.id,)) as cur:
            houses = await cur.fetchall()

    if not houses:
        await call.message.edit_text("🏠 У вас пока нет жилья. Посетите Риелторское агентство!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")]]))
        return

    text = "🏡 **ВАША НЕДВИЖИМОСТЬ В ГОРОДЕ:**\n\n" + "\n".join([f"• **{h[0]}** (Налог: {h[1]} €/сессия)" for h in houses])
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "menu:phone")
async def show_phone(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT phone_number, bank_balance FROM players WHERE user_id = ?", (call.from_user.id,)) as cur:
            u = await cur.fetchone()

    text = (
        f"📱 **СМАРТФОН iFruit / EST-Phone**\n\n"
        f"📞 SIM-номер: `{u[0]}`\n"
        f"💳 Мобильный банк: **{u[1]} €**\n\n"
        "Службы быстрого реагирования:\n"
        "• 🚑 Скорая / Пожарные: Отправьте в чат `*вызвал 112*`\n"
        "• 👮 Полиция: Отправьте в чат `*вызвал полицию*`\n"
        "• 🚕 Такси: Отправьте в чат `т-Вызываю такси`\n"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "menu:rules")
async def show_rules_menu(call: CallbackQuery):
    await call.message.edit_text(get_rules_text(), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад в меню", callback_data="menu:home")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "menu:donate")
async def show_donate(call: CallbackQuery):
    buttons = [
        [InlineKeyboardButton(text="💳 Пополнить Coins (DonationAlerts)", url=DONATION_ALERTS_URL)],
    ]
    for k, v in DONATE_PERKS.items():
        buttons.append([InlineKeyboardButton(text=f"{v['name']} — {v['coins']} 💎", callback_data=f"buyperk:{k}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:home")])

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT donate_coins FROM players WHERE user_id = ?", (call.from_user.id,)) as cur:
            coins = (await cur.fetchone())[0]

    text = (
        f"💎 **ДОНАТ-МАГАЗИН СЕРВЕРА**\n\n"
        f"Баланс: **{coins} Coins 💎**\n\n"
        f"📌 При донате через DonationAlerts **ОБЯЗАТЕЛЬНО УКАЖИТЕ ВАШ ТЕЛЕГРАМ НИК** (@{call.from_user.username or 'юзернейм'})!\n"
        f"Создатели зачислят монеты на аккаунт.\nКурс: 1 рубль = 1 Coin 💎"
    )
    await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("buyperk:"))
async def buy_perk(call: CallbackQuery):
    k = call.data.split(":")[1]
    perk = DONATE_PERKS.get(k)
    user_id = call.from_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT donate_coins FROM players WHERE user_id = ?", (user_id,)) as cur:
            coins = (await cur.fetchone())[0]

        if coins < perk["coins"]:
            await call.answer("❌ Недостаточно Coins 💎!", show_alert=True)
            return

        await db.execute("UPDATE players SET donate_coins = donate_coins - ? WHERE user_id = ?", (perk["coins"], user_id))
        if k == "vip_status":
            await db.execute("UPDATE players SET is_vip = 1 WHERE user_id = ?", (user_id,))
        elif k == "cash_50k":
            await db.execute("UPDATE players SET bank_balance = bank_balance + 50000 WHERE user_id = ?", (user_id,))
        elif k == "cash_150k":
            await db.execute("UPDATE players SET bank_balance = bank_balance + 150000 WHERE user_id = ?", (user_id,))
        elif k == "clear_criminal":
            await db.execute("UPDATE players SET record_criminal = 0 WHERE user_id = ?", (user_id,))
        elif k == "gold_number":
            await db.execute("UPDATE players SET phone_number = '+372 5777 7777' WHERE user_id = ?", (user_id,))

        await db.commit()

    await call.answer(f"🎉 Привилегия {perk['name']} активирована!", show_alert=True)

# --- ПРОВЕДЕНИЕ СЕССИЙ В ТЕЛЕГРАМ ЧАТЕ ---
@dp.message(Command("session"))
async def cmd_session(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username):
        await message.answer("❌ Запускать РП сессию могут только проводящие администраторы!")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE active_session SET is_active = 1 WHERE id = 1")
        await db.execute("DELETE FROM session_members")
        await db.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Зайти на РП сессию", callback_data="session:join")]
    ])
    text = (
        "🚨 **ВНИМАНИЕ! ОБЪЯВЛЕН СТАРТ РП СЕССИИ В RANNARIK RP!** 🚨\n\n"
        "📍 Сервер: **Car Crash Simulator (Эстония)**\n"
        "💶 Все присутствующие получат выплаты зарплат и прибыль с бизнеса в банк Swedbank!\n"
        "📑 Также будут списаны налоги на авто и жилье.\n\n"
        "Нажмите кнопку ниже для фиксации участия в сессии:"
    )
    await message.answer(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "session:join")
async def join_session(call: CallbackQuery):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_active FROM active_session WHERE id = 1") as cur:
            row = await cur.fetchone()
            if not row or row[0] == 0:
                await call.answer("❌ Сессия сейчас не запущена!", show_alert=True)
                return

        try:
            await db.execute("INSERT INTO session_members (user_id) VALUES (?)", (call.from_user.id,))
            await db.commit()
            await call.answer("✅ Вы отмечены в списке участников!", show_alert=True)
        except:
            await call.answer("Вы уже отметились на этой сессии!", show_alert=False)

@dp.message(Command("endsession"))
async def cmd_endsession(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username):
        await message.answer("❌ Завершать сессию могут только администраторы!")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_active FROM active_session WHERE id = 1") as cur:
            status = await cur.fetchone()
            if not status or status[0] == 0:
                await message.answer("❌ Нет активной сессии!")
                return

        async with db.execute("SELECT user_id FROM session_members") as cur:
            members = await cur.fetchall()

        report_lines = []
        total_payout = 0

        for (m_id,) in members:
            async with db.execute("""
                SELECT rp_name, faction, is_vip, sessions_count, has_coke_boost 
                FROM players WHERE user_id = ?
            """, (m_id,)) as cur:
                p_data = await cur.fetchone()
            if not p_data: continue

            p_name, frac, is_vip, sess_count, coke_boost = p_data
            
            # Базовая зарплата должности
            sal = SALARIES.get(frac, 0)
            if is_vip == 1:
                sal = int(sal * 1.5)
            if coke_boost == 1:
                sal = int(sal * 1.35)

            # Множитель от премиум предметов инвентаря
            inv_mult = await get_inventory_multiplier(m_id)
            sal = int(sal * inv_mult)

            # Доходы и налоги бизнеса
            async with db.execute("SELECT SUM(income), SUM(tax) FROM businesses WHERE owner_id = ?", (m_id,)) as cur:
                biz_row = await cur.fetchone()
                biz_inc = biz_row[0] or 0
                biz_tax = biz_row[1] or 0

            # Налоги на машины и дома
            async with db.execute("SELECT SUM(tax) FROM cars WHERE owner_id = ?", (m_id,)) as cur:
                car_tax = (await cur.fetchone())[0] or 0
            async with db.execute("SELECT SUM(tax) FROM houses WHERE owner_id = ?", (m_id,)) as cur:
                house_tax = (await cur.fetchone())[0] or 0

            total_taxes = car_tax + house_tax + biz_tax
            net_income = (sal + biz_inc) - total_taxes

            new_sessions = sess_count + 1

            # Начисление и сброс кокса
            await db.execute("""
                UPDATE players 
                SET bank_balance = bank_balance + ?, sessions_count = ?, has_coke_boost = 0 
                WHERE user_id = ?
            """, (net_income, new_sessions, m_id))

            total_payout += max(0, net_income)
            tax_str = f" (Налоги: -{total_taxes}€)" if total_taxes > 0 else ""
            report_lines.append(f"• **{p_name}** ({frac}): {'+' if net_income>=0 else ''}{net_income} €{tax_str}")

        await db.execute("UPDATE active_session SET is_active = 0 WHERE id = 1")
        await db.execute("DELETE FROM session_members")
        await db.commit()

    report = "\n".join(report_lines) if report_lines else "Никто не посетил сессию."
    final_text = (
        f"🏁 **РП СЕССИЯ ОФИЦИАЛЬНО ЗАВЕРШЕНА!**\n\n"
        f"📊 **Бухгалтерия округа (Выплаты зачислены в Swedbank):**\n{report}\n\n"
        f"Все налоги за транспорт и недвижимость списаны в государственную казну."
    )
    await message.answer(final_text, parse_mode="Markdown")

# --- АДМИН-ПАНЕЛЬ И РАССЫЛКА ---
@dp.callback_query(F.data == "admin:panel")
async def show_admin_panel(call: CallbackQuery):
    if not await is_admin(call.from_user.id, call.from_user.username):
        await call.answer("❌ Доступ запрещён!", show_alert=True)
        return
    text = (
        "👑 **ГЛАВНАЯ АДМИН-ПАНЕЛЬ СЕРВЕРА**\n\n"
        "Выберите действие:"
    )
    admin_kb = await get_admin_menu()
    await call.message.edit_text(text, reply_markup=admin_kb, parse_mode="Markdown")

@dp.callback_query(F.data == "admin:broadcast_start")
async def adm_broadcast_start(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введите текст сообщения для рассылки всем игрокам бота:")
    await state.set_state(BroadcastState.text)

@dp.message(BroadcastState.text)
async def adm_broadcast_send(message: Message, state: FSMContext):
    text_to_send = message.text
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM players") as cur:
            users = await cur.fetchall()

    count = 0
    for (u_id,) in users:
        try:
            await bot.send_message(u_id, f"📢 **ОФИЦИАЛЬНОЕ ОБЪЯВЛЕНИЕ АДМИНИСТРАЦИИ:**\n\n{text_to_send}", parse_mode="Markdown")
            count += 1
        except:
            pass

    await state.clear()
    await message.answer(f"✅ Рассылка успешно отправлена {count} игрокам!")

@dp.callback_query(F.data == "admin:checkuser_help")
async def adm_check_help(call: CallbackQuery):
    await call.message.edit_text(
        "🔍 **Просмотр досье игрока:**\n\n"
        "Напишите команду:\n"
        "`/checkuser @username` или ответьте на любое сообщение игрока командой `/checkuser`\n\n"
        "Бот выдаст полное админ-досье: баланс наличных, счёт в банке, донат, штрафы, судимости, открытые категории прав, купленный транспорт и недвижимость.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")]]),
        parse_mode="Markdown"
    )

@dp.message(Command("checkuser"))
async def cmd_checkuser(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username):
        await message.answer("❌ Доступно только администрации!")
        return

    args = message.text.split()
    target = None
    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("""
                SELECT user_id, roblox_nick, rp_name, birth_date, phone_number,
                       faction, balance, bank_balance, donate_coins, record_criminal, 
                       is_vip, is_admin, license_a, license_b, license_c, license_d, username
                FROM players WHERE user_id = ?
            """, (target_uid,)) as cur:
                target = await cur.fetchone()
    elif len(args) >= 2:
        target_name = args[1].replace("@", "")
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("""
                SELECT user_id, roblox_nick, rp_name, birth_date, phone_number,
                       faction, balance, bank_balance, donate_coins, record_criminal, 
                       is_vip, is_admin, license_a, license_b, license_c, license_d, username
                FROM players WHERE username = ? COLLATE NOCASE
            """, (target_name,)) as cur:
                target = await cur.fetchone()

    if not target:
        await message.answer("📌 Использование: `/checkuser @username` или ответом `/checkuser`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT model_name, plate_number FROM cars WHERE owner_id = ?", (target[0],)) as cur:
            cars = await cur.fetchall()
        async with db.execute("SELECT house_name FROM houses WHERE owner_id = ?", (target[0],)) as cur:
            houses = await cur.fetchall()
        async with db.execute("SELECT item_name FROM inventory WHERE user_id = ?", (target[0],)) as cur:
            items = await cur.fetchall()

    lic_list = []
    if target[12] == 1: lic_list.append("A")
    if target[13] == 1: lic_list.append("B")
    if target[14] == 1: lic_list.append("C")
    if target[15] == 1: lic_list.append("D")
    lic_str = ", ".join(lic_list) if lic_list else "Нет"

    cars_str = ", ".join([f"{c[0]} ({c[1]})" for c in cars]) if cars else "Нет авто"
    houses_str = ", ".join([h[0] for h in houses]) if houses else "Нет жилья"
    inv_str = ", ".join([i[0] for i in items]) if items else "Пусто"

    text = (
        f"⚙️ **АДМИНИСТРАТИВНОЕ ДОСЬЕ ИГРОКА**\n\n"
        f"🆔 Telegram ID: `{target[0]}` | @{target[16]}\n"
        f"👤 РП Имя: **{target[2]}**\n"
        f"🎮 Roblox Ник: `{target[1]}`\n"
        f"🎂 Дата рождения: **{target[3]}**\n"
        f"📱 Номер: `{target[4]}`\n"
        f"🏢 Должность: **{target[5]}**\n"
        f"💵 Наличные: **{target[6]} €** | 💳 Банк: **{target[7]} €**\n"
        f"💎 Coins: **{target[8]}**\n"
        f"⚖️ Судимостей: **{target[9]}**\n"
        f"🚗 Права (категории): **{lic_str}**\n"
        f"👑 VIP: {'Да' if target[10]==1 else 'Нет'} | Админ: {'Да' if target[11]==1 else 'Нет'}\n\n"
        f"🚘 **Транспорт:** {cars_str}\n"
        f"🏠 **Жильё:** {houses_str}\n"
        f"🎒 **Инвентарь:** {inv_str}\n"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.callback_query(F.data == "admin:all_commands")
async def adm_all_commands(call: CallbackQuery):
    cmd_list = (
        "📖 **СПИСОК ВСЕХ КОМАНД СЕРВЕРА:**\n\n"
        "👤 **Команды для всех игроков:**\n"
        "• `/start` — Открыть главное меню / паспорт\n"
        "• `/balance` — Посмотреть свой баланс евро и коинов\n"
        "• `/give @user сумма` (или ответом) — Перевести евро\n\n"
        "👮‍♂️ **Команды полиции (только для сотрудников):**\n"
        "• `/police` — Служебная панель и инструкция\n"
        "• `/frisk @user` — Досмотр гражданина\n"
        "• `/cuff @user` — Надеть/снять наручники\n"
        "• `/fine @user сумма причина` — Выписать штраф\n"
        "• `/arrest @user статья` — Задержать и посадить в тюрьму\n\n"
        "👑 **Команды администрации:**\n"
        "• `/checkuser @user` — Полное досье на игрока\n"
        "• `/admin money @user сумма` — Начислить евро\n"
        "• `/removemoney @user сумма` — Списать евро\n"
        "• `/setcoins @user сумма` — Начислить Coins 💎\n"
        "• `/promote @user` — Повысить офицера полиции по отчёту\n"
        "• `/setjob @user Должность` — Назначить любую должность\n"
        "• `/clearwanted @user` — Очистить судимости\n"
        "• `/session` — Начать РП сессию в чате\n"
        "• `/endsession` — Завершить РП сессию с расчётом зарплат"
    )
    await call.message.edit_text(cmd_list, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")]]), parse_mode="Markdown")

@dp.callback_query(F.data == "admin:give_money_help")
async def adm_m_help(call: CallbackQuery):
    await call.message.edit_text(
        "💶 **Начисление и списание денег:**\n\n"
        "• `/admin money @username сумма` — зачислить евро на счёт\n"
        "• `/removemoney @username сумма` — списать евро со счёта\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")]]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "admin:give_coins_help")
async def adm_c_help(call: CallbackQuery):
    await call.message.edit_text(
        "💎 **Выдача донат валюты Coins:**\n\n"
        "• `/setcoins @username сумма` — начислить монеты игроку (за донат через DonationAlerts)\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")]]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "admin:session_help")
async def adm_s_help(call: CallbackQuery):
    await call.message.edit_text(
        "🚨 **Управление РП Сессиями:**\n\n"
        "• `/session` — начать РП сессию в общем чате с пингом и кнопкой входа\n"
        "• `/endsession` — закрыть сессию, выдать зарплаты за роли и бизнесы, списать налоги на авто и жилье\n",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ В админку", callback_data="admin:panel")]]),
        parse_mode="Markdown"
    )

@dp.message(Command("promote"))
async def cmd_promote(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username): return
    args = message.text.split()
    target_uname = None
    target_uid = None

    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
    elif len(args) >= 2:
        target_uname = args[1].replace("@", "")
    else:
        await message.answer("📌 Использование: `/promote @username` или ответом `/promote`", parse_mode="Markdown")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        if target_uid:
            async with db.execute("SELECT user_id, rp_name, faction, username FROM players WHERE user_id = ?", (target_uid,)) as cur:
                target = await cur.fetchone()
        else:
            async with db.execute("SELECT user_id, rp_name, faction, username FROM players WHERE username = ? COLLATE NOCASE", (target_uname,)) as cur:
                target = await cur.fetchone()

        if not target:
            await message.answer("❌ Гражданин не найден!")
            return

        cur_frac = target[2]
        new_frac = None
        if cur_frac == "Младший Констебль":
            new_frac = "Констебль"
        elif cur_frac == "Констебль":
            new_frac = "Главный Констебль"
        else:
            await message.answer(f"❌ Гражданин {target[1]} имеет должность '{cur_frac}'. Повышение доступно только для сотрудников полиции!")
            return

        await db.execute("UPDATE players SET faction = ? WHERE user_id = ?", (new_frac, target[0]))
        await db.commit()

    await message.answer(
        f"🎖 **ПРИКАЗ О ПОВЫШЕНИИ ПО СЛУЖБЕ**\n\n"
        f"👤 Офицер: **{target[1]}** (@{target[3]})\n"
        f"⭐ Новое специальное звание: **{new_frac}**!\n"
        f"Основание: успешно сданный рапорт / отчёт в чате.",
        parse_mode="Markdown"
    )

@dp.message(Command("setjob"))
async def cmd_setjob(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username): return
    args = message.text.split()
    if len(args) < 3 and not (message.reply_to_message and len(args) >= 2):
        await message.answer("📌 Использование: `/setjob @username Название_Роли` или ответом `/setjob Название_Роли`", parse_mode="Markdown")
        return

    target_uname = None
    target_uid = None

    if message.reply_to_message:
        target_uid = message.reply_to_message.from_user.id
        new_role = " ".join(args[1:])
    else:
        target_uname = args[1].replace("@", "")
        new_role = " ".join(args[2:])

    matched_role = None
    for r in SALARIES.keys():
        if r.lower() == new_role.lower():
            matched_role = r
            break

    if not matched_role:
        roles_avail = ", ".join(SALARIES.keys())
        await message.answer(f"❌ Роль '{new_role}' не найдена!\nДоступные: {roles_avail}")
        return

    async with aiosqlite.connect(DB_NAME) as db:
        if target_uid:
            async with db.execute("SELECT user_id, rp_name, username FROM players WHERE user_id = ?", (target_uid,)) as cur:
                target = await cur.fetchone()
        else:
            async with db.execute("SELECT user_id, rp_name, username FROM players WHERE username = ? COLLATE NOCASE", (target_uname,)) as cur:
                target = await cur.fetchone()

        if not target:
            await message.answer("❌ Гражданин не найден!")
            return

        await db.execute("UPDATE players SET faction = ? WHERE user_id = ?", (matched_role, target[0]))
        await db.commit()

    await message.answer(f"✅ Должность гражданина **{target[1]}** (@{target[2]}) успешно изменена на **{matched_role}**!")

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username): return
    args = message.text.split()
    if len(args) >= 4 and args[1] == "money":
        target = args[2].replace("@", "")
        amt = int(args[3])
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("UPDATE players SET bank_balance = bank_balance + ? WHERE username = ? COLLATE NOCASE", (amt, target))
            await db.commit()
        await message.answer(f"✅ Начислено **{amt} €** пользователю @{target}!")
        return

    text = (
        "⚙️ **КОМАНДЫ АДМИНИСТРАЦИИ:**\n\n"
        "• `/admin money @user сумма` — начислить евро на счёт\n"
        "• `/removemoney @user сумма` — списать евро со счёта\n"
        "• `/setcoins @user сумма` — выдать донат Coins 💎\n"
        "• `/promote @user` — повысить офицера полиции по отчёту\n"
        "• `/setjob @user Должность` — назначить любую должность игроку\n"
        "• `/checkuser @user` — полное досье на игрока\n"
        "• `/session` и `/endsession` — проведение РП сессий"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("setcoins"))
async def cmd_setcoins(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username): return
    args = message.text.split()
    if len(args) < 3: return
    target = args[1].replace("@", "")
    amt = int(args[2])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE players SET donate_coins = donate_coins + ? WHERE username = ? COLLATE NOCASE", (amt, target))
        await db.commit()
    await message.answer(f"✅ Начислено **{amt} Coins 💎** пользователю @{target}!")

@dp.message(Command("removemoney"))
async def cmd_removemoney(message: Message):
    if not await is_admin(message.from_user.id, message.from_user.username): return
    args = message.text.split()
    if len(args) < 3: return
    target = args[1].replace("@", "")
    amt = int(args[2])
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE players SET bank_balance = MAX(0, bank_balance - ?) WHERE username = ? COLLATE NOCASE", (amt, target))
        await db.commit()
    await message.answer(f"✅ Списано **{amt} €** у пользователя @{target}.")

@dp.callback_query(F.data == "menu:home")
async def back_home(call: CallbackQuery):
    menu = await get_main_menu(call.from_user.id, call.from_user.username)
    await call.message.edit_text("Главное меню Rannarik:", reply_markup=menu)

# --- ТОЧКА ВХОДА ---
async def start_health_server():
    from aiohttp import web
    async def handle_ping(request):
        return web.Response(text="Bot is running!")
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/healthz", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Health-check веб-сервер запущен на порту {port}")

async def main():
    await init_db()
    # Запускаем фоновый порт для Render Web Service (чтобы статус был Live)
    if "PORT" in os.environ:
        try:
            await start_health_server()
        except Exception as e:
            print("Health server error:", e)
    print("🚀 Car RP Bot Rannarik успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
