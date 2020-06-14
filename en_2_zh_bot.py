#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, splitCommand
from telegram.ext import Updater, MessageHandler, Filters
import yaml
import threading
import translate
from datetime import datetime

scheulded = False
queue = []

wait = 60 * 5
if 'test' in sys.argv:
	wait = 1

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

tele = Updater(credential['bot'], use_context=True)  # @en_2_zh_bot
debug_group = tele.bot.get_chat(420074357)

def popMessages(msg):
	global queue
	if not msg.media_group_id:
		return []
	result = [m for m in queue if m.media_group_id == msg.media_group_id]
	queue = [m for m in queue if m.media_group_id != msg.media_group_id]
	return result

def translate(text): # in markdown format
	return text

def processMsg(original_messages):
	if original_messages.photo:
		media = []
		for m in original_messages:
			photo = InputMediaPhoto(m.photo[-1].file_id, 
				caption=translate(m.caption_markdown),
				parse_mode='Markdown')
			if m.caption_markdown:
				media = [photo] + media
			else:
				media.append(photo)
		bot.send_media_group(msg.chat_id, media)
	if msg.chat.username == 'twitter_translate':
		for r in original_messages:
			r.delete()

@log_on_fail(debug_group)
def process():
	global queue
	new_queue = []
	while queue:
		msg = queue.pop(0)
		original_messages = [msg] + popMessages(msg)
		epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
		timestamp = (msg.date.replace(tzinfo=timezone.utc) - epoch) / timedelta(seconds=1)
		if time.time() - timestamp < wait:
			new_queue += original_messages
			continue
		processMsg(original_messages)
	queue = new_queue
	if queue:
		threading.Timer(wait, process).start()
	else:
		global scheulded
		scheulded = False

def handleUpdate(update, context):
	msg = update.effective_message
	if not msg or msg.chat_id == debug_group.id:
		return
	queue.append(msg)
	global scheulded
	if not scheulded:
		scheulded = True
		threading.Timer(wait, process).start()

if __name__ == '__main__':
	dp = tele.dispatcher
	dp.add_handler(MessageHandler(~Filters.command, handleUpdate))
	tele.start_polling()
	tele.idle()