import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)
from flask import Flask, request

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация (переменные будут загружены из .env)
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Состояния для ConversationHandler
(
    MAIN_MENU,
    CHOOSING_SERVICE,
    TYPING_CAR_MODEL,
    CHOOSING_SIGNAL_TYPE,
    CHOOSING_TINTING_TYPE,
    CHOOSING_CAMERA_NEED,
    CHOOSING_MILEAGE,
    CHOOSING_LAST_SERVICE,
    CHOOSING_LOCATION
) = range(9)

# Ключи для хранения данных в user_data
CAR_MODEL, SERVICE_TYPE, SERVICE_DETAIL, LOCATION = range(4)

# Инициализация Flask приложения
flask_app = Flask(__name__)

# Глобальная переменная для хранения объекта Application бота
bot_application = None

# Функция для создания главного меню
def main_menu_keyboard():
    keyboard = [
        ['📍 Наши адреса'],
        ['🚘 Установка сигнализации', '🪟 Тонировка авто'],
        ['📱 Установка магнитолы', '🔧 Плановое ТО'],
        ['◀️ Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Добро пожаловать! Выберите услугу:',
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

# Обработчик кнопки "Назад"
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Главное меню:',
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

# Обработчик кнопки "Наши адреса"
async def show_addresses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone1 = '+7 (927) 267-90-70'
    phone2 = '+7 (937) 180-96-33'
    
    message = (
        "Работаем без выходных с 9 до 19\n\n"
        f"📍ул. Фадеева, 51А\n"
        f"<a href='tel:{phone1}'>{phone1}</a>\n\n"
        f"📍Московское ш., 16 км, 1А\n"
        f"<a href='tel:{phone2}'>{phone2}</a>"
    )
    
    # Отправляем сообщение с HTML-разметкой
    await update.message.reply_text(
        message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Записаться на установку!", callback_data='appointment_global')]
        ])
    )
    return MAIN_MENU

# Обработчик инлайн-кнопки "Записаться на установку!"
async def global_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Давайте запишем вас на установку!")
    
    # Сохраняем тип услуги как глобальная запись
    context.user_data[SERVICE_TYPE] = 'global'
    
    await query.message.reply_text(
        "Какой у вас автомобиль? (Укажите марку, модель и год)",
        reply_markup=ReplyKeyboardMarkup([['◀️ Назад']], resize_keyboard=True)
    )
    return TYPING_CAR_MODEL

# Обработчики выбора услуг
async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    service = update.message.text
    service_map = {
        '🚘 Установка сигнализации': 'signal',
        '🪟 Тонировка авто': 'tinting',
        '📱 Установка магнитолы': 'android_auto',
        '🔧 Плановое ТО': 'maintenance'
    }
    
    context.user_data[SERVICE_TYPE] = service_map.get(service, 'unknown')
    
    await update.message.reply_text(
        "Какой у вас автомобиль? (Укажите марку, модель и год)",
        reply_markup=ReplyKeyboardMarkup([['◀️ Назад']], resize_keyboard=True)
    )
    return TYPING_CAR_MODEL

# Получение данных об автомобиле
async def receive_car_model(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[CAR_MODEL] = update.message.text
    service_type = context.user_data.get(SERVICE_TYPE, 'global')
    
    if service_type == 'signal':
        keyboard = [['Сигнализация с автозапуском', 'Сигнализация без автозапуска'], ['◀️ Назад']]
        await update.message.reply_text(
            "Выберите тип сигнализации:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_SIGNAL_TYPE
        
    elif service_type == 'tinting':
        keyboard = [['Задний отсек', 'Передние боковые', 'Лобовое стекло'], ['◀️ Назад']]
        await update.message.reply_text(
            "Что тонируем?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_TINTING_TYPE
        
    elif service_type == 'android_auto':
        keyboard = [['Да', 'Нет'], ['◀️ Назад']]
        await update.message.reply_text(
            "Требуется ли установка камеры заднего вида?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_CAMERA_NEED
        
    elif service_type == 'maintenance':
        keyboard = [
            ['До 15 000 км', '15 000 - 30 000 км'],
            ['30 000 - 60 000 км', '60 000 - 100 000 км'],
            ['Свыше 100 000 км'],
            ['◀️ Назад']
        ]
        await update.message.reply_text(
            "Какой у вас пробег автомобиля?",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_MILEAGE
        
    else:  # global appointment
        keyboard = [
            ['Установка сигнализации', 'Тонировка авто'],
            ['Установка магнитолы', 'Плановое ТО'],
            ['◀️ Назад']
        ]
        await update.message.reply_text(
            "Выберите услугу для записи:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHOOSING_SERVICE

# Обработчики для разных типов услуг
async def receive_signal_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[SERVICE_DETAIL] = update.message.text
    return await ask_for_location(update, context)

async def receive_tinting_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[SERVICE_DETAIL] = update.message.text
    return await ask_for_location(update, context)

async def receive_camera_need(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[SERVICE_DETAIL] = update.message.text
    return await ask_for_location(update, context)

async def receive_mileage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[SERVICE_DETAIL] = update.message.text
    keyboard = [
        ['Менее 6 месяцев назад', '6-12 месяцев назад'],
        ['Более года назад', 'Не помню'],
        ['◀️ Назад']
    ]
    await update.message.reply_text(
        "Когда было последнее ТО?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_LAST_SERVICE

async def receive_last_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['last_service'] = update.message.text
    return await ask_for_location(update, context)

# Запрос выбора локации
async def ask_for_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [['📍ул. Фадеева, 51А', '📍Московское ш., 16 км, 1А'], ['◀️ Назад']]
    await update.message.reply_text(
        "Выберите удобный адрес:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHOOSING_LOCATION

# Финальный шаг - получение локации и отправка заявки
async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data[LOCATION] = update.message.text
    
    # Формируем сообщение для админа
    service_names = {
        'signal': 'Установка сигнализации',
        'tinting': 'Тонировка авто',
        'android_auto': 'Установка Android магнитолы',
        'maintenance': 'Плановое ТО и Ремонт',
        'global': 'Запись на установку'
    }
    
    service_type = context.user_data.get(SERVICE_TYPE, 'global')
    message = f"✅ <b>Новая заявка!</b>\n\n"
    message += f"Услуга: {service_names.get(service_type, 'Неизвестная услуга')}\n"
    message += f"Автомобиль: {context.user_data.get(CAR_MODEL, 'Не указан')}\n"
    
    if SERVICE_DETAIL in context.user_data:
        message += f"Детали: {context.user_data[SERVICE_DETAIL]}\n"
    
    if 'last_service' in context.user_data:
        message += f"Последнее ТО: {context.user_data['last_service']}\n"
    
    message += f"Адрес: {context.user_data.get(LOCATION, 'Не указан')}\n\n"
    message += f"Клиент: @{update.effective_user.username or 'Нет username'}"
    
    # Отправляем сообщение админу
    if ADMIN_CHAT_ID:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=message,
            parse_mode='HTML'
        )
    
    # Подтверждение пользователю
    await update.message.reply_text(
        "Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время.",
        reply_markup=main_menu_keyboard()
    )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    return MAIN_MENU

# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Диалог отменен. Возврат в главное меню.',
        reply_markup=main_menu_keyboard()
    )
    context.user_data.clear()
    return MAIN_MENU

# Настройка обработчиков
def setup_handlers(application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex('^📍 Наши адреса$'), show_addresses),
                MessageHandler(filters.Regex('^(🚘 Установка сигнализации|🪟 Тонировка авто|📱 Установка магнитолы|🔧 Плановое ТО)$'), choose_service),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            TYPING_CAR_MODEL: [
                MessageHandler(filters.TEXT & ~filters.Regex('^◀️ Назад$'), receive_car_model),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_SERVICE: [
                MessageHandler(filters.Regex('^(Установка сигнализации|Тонировка авто|Установка магнитолы|Плановое ТО)$'), choose_service),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_SIGNAL_TYPE: [
                MessageHandler(filters.Regex('^(Сигнализация с автозапуском|Сигнализация без автозапуска)$'), receive_signal_type),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_TINTING_TYPE: [
                MessageHandler(filters.Regex('^(Задний отсек|Передние боковые|Лобовое стекло)$'), receive_tinting_type),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_CAMERA_NEED: [
                MessageHandler(filters.Regex('^(Да|Нет)$'), receive_camera_need),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_MILEAGE: [
                MessageHandler(filters.Regex('^(До 15 000 км|15 000 - 30 000 км|30 000 - 60 000 км|60 000 - 100 000 км|Свыше 100 000 км)$'), receive_mileage),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_LAST_SERVICE: [
                MessageHandler(filters.Regex('^(Менее 6 месяцев назад|6-12 месяцев назад|Более года назад|Не помню)$'), receive_last_service),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
            CHOOSING_LOCATION: [
                MessageHandler(filters.Regex('^(📍ул. Фадеева, 51А|📍Московское ш., 16 км, 1А)$'), receive_location),
                MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(filters.Regex('^◀️ Назад$'), back_to_menu)],
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(global_appointment, pattern='^appointment_global$'))

# Функция для запуска бота
async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(application)
    
    global bot_application
    bot_application = application
    
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

# Flask endpoint для вебхука
@flask_app.route('/webhook', methods=['POST'])
async def webhook():
    if bot_application is None:
        return 'Bot not initialized', 500
    
    update = Update.de_json(request.get_json(), bot_application.bot)
    await bot_application.process_update(update)
    return 'OK'

# Запуск Flask сервера
if __name__ == '__main__':
    import asyncio
    from threading import Thread
    
    def run_flask():
        flask_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
    
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаем бота
    asyncio.run(run_bot())
