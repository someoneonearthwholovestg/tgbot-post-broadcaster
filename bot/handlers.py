import logging

import telegram
from telegram import Update
from telegram.ext import CallbackContext

from . import dbadapter
from . import settings
from . import storage

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=settings.LOG_LEVEL,
)
logger = logging.getLogger(__name__)

# TODO
HELP = '''Post Broadcaster Bot is'''


# Bot commands
# ============

def command_start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text(HELP)


def command_enable(update: Update, context: CallbackContext) -> None:
    """Connect current group to channel via it's short name."""
    logger.debug(f'Command /enable in {update.effective_chat.id} group.')

    db_session = storage.BotData.get_db_session(context.bot_data)
    rg = dbadapter.ReceiverGroup.enable_by_chat_id(
        chat_id=update.effective_chat.id,
        session=db_session,
    )
    db_session.commit()

    update.effective_message.reply_text(
        f'Broadcasting to this group chat successfully enabled.'
    )


def command_disable(update: Update, context: CallbackContext) -> None:
    """Disable broadcasting to current group from channel."""
    logger.debug(f'Command /disable in {update.effective_chat.id} group.')

    db_session = storage.BotData.get_db_session(context.bot_data)
    rg = dbadapter.ReceiverGroup.disable_by_chat_id(
        chat_id=update.effective_chat.id,
        session=db_session,
    )
    db_session.commit()

    update.effective_message.reply_text(
        f'Broadcasting to this group chat successfully disabled.'
    )


def handler_broadcast_post(update: Update, context: CallbackContext) -> None:
    """Broadcast post from channel to connected groups."""
    logger.debug(f'Post in {update.effective_chat.id} channel.')

    db_session = storage.BotData.get_db_session(context.bot_data)
    groups_broadcast_to = dbadapter.ReceiverGroup.list_enabled_chat_ids(session=db_session)

    for group_id in groups_broadcast_to:
        try:
            context.bot.forward_message(
                chat_id=group_id,
                from_chat_id=update.effective_chat.id,
                message_id=update.effective_message.message_id,
            )
        except telegram.error.BadRequest as bad_request:
            logger.warning(
                f'Attempt to forward message to {group_id} failed due to '
                f'BadRequest error: {bad_request}'
            )
        except Exception as exc:
            logger.exception(f'Unhandled error during attempt ot forward message:')
        else:
            logger.debug(
                f'Successfully forwarded message {update.effective_message.message_id}'
                f' to chat {group_id}'
            )
