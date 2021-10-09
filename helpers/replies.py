from random import randint
from discord import Embed


def enrich(reply, name=None, ref_name=None, prefix=None, insert=None, insert2=None, addon=None, mention=None,
           ref_mention=None, channel=None, start=None, url=None, search=None):
    if name:        reply = reply.replace('{name}', name)
    if ref_name:    reply = reply.replace('{ref_name}', ref_name)
    if prefix:      reply = reply.replace('{prefix}', prefix)
    if mention:     reply = reply.replace('{mention}', mention)
    if ref_mention: reply = reply.replace('{ref_mention}', ref_mention)
    if channel:     reply = reply.replace('{channel}', channel)
    if insert:      reply = reply.replace('{insert}', str(insert))
    if insert2:     reply = reply.replace('{insert2}', str(insert2))
    if url:         reply = reply.replace('{url}', url)
    if search:      reply = reply.replace('{search}', str(search))
    if start:       reply = start + reply  # Append to beginning
    if addon:       reply += ' ' + addon  # Append to End

    return reply


def get_reply(replies: list):
    random = randint(0, len(replies) - 1)
    return replies[random]
