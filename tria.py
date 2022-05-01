import json
from operator import truediv

from imap_tools import MailBox
import time

import asyncio

with open("tria.json") as jsonfile:
	config = json.load(jsonfile)

#######################################

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


def send_mail(send_from, send_to, subject, text, files = {}, server = config["MAIL"]["smtp"]):
	assert isinstance(send_to, list)
	msg = MIMEMultipart()
	msg['From'] = send_from
	msg['To'] = COMMASPACE.join(send_to)
	msg['Date'] = formatdate(localtime=True)
	msg['Subject'] = subject
	msg.attach(MIMEText(text))
	for k, v in files.items():
		with open(v, "rb") as fil:
			part = MIMEApplication(
				fil.read(),
				Name=k
			)
		# After the file is closed
		part['Content-Disposition'] = 'attachment; filename="%s"' % k
		msg.attach(part)
	smtp = smtplib.SMTP(server)
	smtp.login(config["MAIL"]["user"], config["MAIL"]["password"])
	smtp.sendmail(send_from, send_to, msg.as_string())
	smtp.close()
#####################################################################

import os
import tempfile

async def take_picture_and_send(email):
	cmd = config["BOT"]["capture"]
	with tempfile.NamedTemporaryFile() as file:
		full_cmd = "{0} {1}".format(cmd, file.name)
		print(full_cmd)
		os.system(full_cmd)
		send_mail(config["MAIL"]["user"], [email], "Picture", "See attachment", {"image.jpg" : file.name})

#####################################################################

emails = config["MAIL"]["allowed_emails"]

async def handle_mail(message):
	if message.from_ in emails:
		if message.subject.lower() == "photo garage":
			await take_picture_and_send(message.from_)
			return True
	return True

async def check_mail():
	user, password = config["MAIL"]["user"], config["MAIL"]["password"]
	start = time.time()
	try:
		# get list of email body from INBOX folder
		body_set = []
		with MailBox(config["MAIL"]["imap"]).login(user, password) as mailbox:
			uids = []
			for msg in mailbox.fetch():
				if await handle_mail(msg):
					uids.append(msg.uid)
			if len(uids) > 0:
				mailbox.delete(uids)
	except Exception as e:
		print("ErrorType : {}, Error : {}".format(type(e).__name__, e))

#######################################

async def periodic():
	while True:
		print("Starting checking mails...")
		await check_mail()
		print("Done checking mails.")
		print("Waiting for 30 seconds...")
		await asyncio.sleep(30)
		print("Done waiting.")

asyncio.run(periodic())