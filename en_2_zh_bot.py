#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram_util import log_on_fail, splitCommand, isUrl
from telegram.ext import Updater, MessageHandler, Filters
import yaml
import threading
from translate import Translator
from datetime import datetime, timedelta, timezone
import sys
import time
from telegram import InputMediaPhoto
translator= Translator(to_lang="zh")

scheulded = False
queue = []

wait = 60 * 5
if 'test' in sys.argv:
	wait = 10

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

def en2zhPiece(text):
	if not text.strip() or text.startswith('['):
		return text
	result = translator.translate(text)
	l_char_len = len(text) - len(text.lstrip())
	l_char = text[:l_char_len]
	r_char_len = len(text) - len(text.rstrip())
	if not r_char_len:
		r_char = ''
	else:
		r_char = text[-r_char_len:]
	return l_char + result + r_char

def en2zh(text): # in markdown format
	pieces = []
	while text:
		first_piece = text.split('[')[0]
		text = text[len(first_piece):]
		quote = text.split(')')[0]
		text = text[len(quote):]
		pieces += [first_piece, quote]
	pieces = [en2zhPiece(text) for text in pieces]
	return ''.join(pieces)

def processMsg(original_messages):
	msg = original_messages[0]
	if msg.photo:
		media = []
		for m in original_messages:
			photo = InputMediaPhoto(m.photo[-1].file_id, 
				caption=en2zh(m.caption_markdown_v2),
				parse_mode='MarkdownV2')
			if m.caption_markdown_v2:
				media = [photo] + media
			else:
				media.append(photo)
		msg.bot.send_media_group(msg.chat_id, media)
	elif msg.video:
		msg.bot.send_video(msg.chat_id, 
			msg.video.file_id, 
			caption=en2zh(msg.caption_markdown_v2), 
			parse_mode='MarkdownV2', timeout = 20*60)
	else:
		text = en2zh(msg.text_markdown_v2)
		msg.bot.send_message(msg.chat_id, text,
			parse_mode='MarkdownV2', timeout = 20*60, 
			disable_web_page_preview = (
				not isUrl(text.split('[source]')[0])))

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