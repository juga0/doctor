"""
Module for issuing email notifications to me via gmail.
"""

import logging
import os
import smtplib
import subprocess

from email import Encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.MIMEBase import MIMEBase

import stem.util.log

FROM_ADDRESS = 'verelsa@gmail.com'
TO_ADDRESS = 'tor-consensus-health@lists.torproject.org'
ERROR_ADDRESS = 'atagar@torproject.org'
PASSWORD = None


def get_path(*comp):
  """
  Provides a path relative of these scripts.

  :returns: absolute path, relative of these scripts
  """

  return os.path.abspath(os.path.join(os.path.dirname(__file__), *comp))


def get_logger(name):
  """
  Provides a logger configured to write to our local 'logs' directory.

  :param str name: name of our log file

  :returns: preconfigured logger
  """

  log_dir = get_path('logs')

  if not os.path.exists(log_dir):
    os.mkdir(log_dir)

  handler = logging.FileHandler(os.path.join(log_dir, name))
  handler.setFormatter(logging.Formatter(
    fmt = '%(asctime)s [%(levelname)s] %(message)s',
    datefmt = '%m/%d/%Y %H:%M:%S',
  ))

  log = logging.getLogger(name)
  log.setLevel(logging.DEBUG)
  log.addHandler(handler)

  return log


def log_stem_debugging(name):
  """
  Logs trace level stem output to the given log file.

  :param str name: prefix name for our log file
  """

  log_dir = get_path('logs')

  if not os.path.exists(log_dir):
    os.mkdir(log_dir)

  handler = logging.FileHandler(os.path.join(log_dir, name + '.stem_debug'))
  handler.setFormatter(logging.Formatter(
    fmt = '%(asctime)s [%(levelname)s] %(message)s',
    datefmt = '%m/%d/%Y %H:%M:%S',
  ))

  log = stem.util.log.get_logger()
  log.addHandler(handler)


def send(subject, body_text = None, destination = TO_ADDRESS, cc_destinations = None, bcc_destinations = None):
  """
  Sends an email notification via the local mail application.

  :param str subject: subject of the email
  :param str body_text: plaintext body of the email
  :param str destination: location to send the email to
  :param list cc_destinations: addresses for the cc field
  :param list bcc_destinations: addresses for the bcc field

  :raises: **Exception** if the email fails to be sent
  """

  args = ['mail', '-E', '-s', subject]

  if cc_destinations:
    args += ['-c', ','.join(cc_destinations)]

  if bcc_destinations:
    args += ['-b', ','.join(bcc_destinations)]

  args.append(destination)

  process = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
  stdout, stderr = process.communicate(body_text)
  exit_code = process.poll()

  if exit_code != 0:
    raise ValueError("Unable to send email: %s" % stderr.strip())


def send_via_gmail(subject, body_text = None, body_html = None, attachment = None, destination = TO_ADDRESS):
  """
  Sends an email notification via gmail.

  :param str subject: subject of the email
  :param str body_text: plaintext body of the email
  :param str body_html: html body of the email
  :param str attachment: path of a file to attach
  :param str destination: location to send the email to

  :raises: **Exception** if the email fails to be sent
  """

  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = FROM_ADDRESS
  msg['To'] = destination

  if body_text:
    msg.attach(MIMEText(body_text, 'plain'))

  if body_html:
    msg.attach(MIMEText(body_html, 'html'))

  if attachment:
    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(attachment, "rb").read())
    Encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(attachment))
    msg.attach(part)

  # send the message via the gmail SMTP server
  server = smtplib.SMTP('smtp.gmail.com:587')
  server.starttls()
  server.login(FROM_ADDRESS, _get_password())
  server.sendmail(FROM_ADDRESS, [destination], msg.as_string())
  server.quit()


def _get_password():
  """
  Provides the password for our gmail account. This is expected to be in a
  local 'gmail_pw' file.

  :returns: **str** with our gmail password

  :raises: **ValueError** if our password file is unavalable or can't be read
  """

  global PASSWORD

  if PASSWORD is None:
    pw_path = get_path('gmail_pw')

    if not os.path.exists(pw_path):
      raise ValueError("Unable to determine our gmail password, '%s' doesn't exist" % pw_path)

    try:
      PASSWORD = open(pw_path).read().strip()
    except Exception, exc:
      raise ValueError('Unable to determine our gmail password: %s' % exc)

  return PASSWORD
