import socket
import logging
from telegram.ext import Application, CommandHandler, ContextTypes

# Конфигурация
TELEGRAM_TOKEN = 'PLACE_YOUR_TOKEN_HERE'
OWNER_CHAT_ID = PLACE_YOUR_CHAD_ID_HERE  # Ваш chat id в телеге
RDP_IP = 'IP_адрес_RDP_сервера'
RDP_PORT = порт
CHECK_INTERVAL = 300  # в секундах

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

last_status = None


async def is_owner(update):
    """Проверяет, является ли пользователь владельцем"""
    return update.effective_user.id == OWNER_CHAT_ID


async def check_rdp_connection(ip, port):
    """Проверяет доступность RDP соединения"""
    try:
        with socket.create_connection((ip, port), timeout=10):
            return True
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as e:
        logger.warning(f"RDP недоступен: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке RDP: {e}")
        return False


async def send_owner_notification(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Отправляет уведомление только владельцу"""
    try:
        await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=message)
        logger.info("Уведомление отправлено владельцу")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")


async def monitor_rdp(context: ContextTypes.DEFAULT_TYPE):
    """Периодическая проверка RDP"""
    global last_status
    current_status = await check_rdp_connection(RDP_IP, RDP_PORT)

    if last_status is not None and current_status != last_status:
        message = (f"✅ RDP доступен!" if current_status
                   else f"⚠️ RDP недоступен!")
        await send_owner_notification(context, message)

    last_status = current_status


async def start(update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /start только для владельца"""
    if not await is_owner(update):
        logger.warning(f"Попытка доступа от {update.effective_user.id}")
        return

    await update.message.reply_text(
        f"Бот мониторинга RDP для владельца\n"
        f"Сервер: {RDP_IP}:{RDP_PORT}\n"
        f"Проверка каждые {CHECK_INTERVAL // 60} мин."
    )


async def status(update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик /status только для владельца"""
    if not await is_owner(update):
        return

    status = await check_rdp_connection(RDP_IP, RDP_PORT)
    await update.message.reply_text(
        f"✅ Доступен" if status else f"❌ Недоступен"
    )


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # Периодическая проверка
    job_queue = application.job_queue
    job_queue.run_repeating(monitor_rdp, interval=CHECK_INTERVAL, first=5)

    application.run_polling()


if __name__ == '__main__':
    main()
