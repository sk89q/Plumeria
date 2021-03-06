"""Commands to modify server settings."""

import asyncio
import io

from plumeria.command import commands, CommandError, channel_only
from plumeria.message import Message
from plumeria.message.image import read_image
from plumeria.perms import have_all_perms
from plumeria.transport.transport import ForbiddenError


@commands.create('icon set', 'iconset', 'set icon', 'seticon', category='Management')
@channel_only
@have_all_perms('manage_server')
async def set_icon(message: Message):
    """
    Set the server icon to the given image.

    Example::

        /drawtext Hello there! | icon set

    Requires an input image.
    """
    attachment = await read_image(message)
    if not attachment:
        raise CommandError("No image is available to process.")

    def execute():
        width, height = attachment.image.size
        if width < 128 or height < 128:
            raise CommandError("Image is too small (128x128 minimum size).")
        buffer = io.BytesIO()
        attachment.image.save(buffer, "png")
        return buffer.getvalue()

    image_data = await asyncio.get_event_loop().run_in_executor(None, execute)

    try:
        await message.server.update(icon=image_data)
        return "Server icon updated."
    except ForbiddenError as e:
        raise CommandError("The bot doesn't have the permissions to do this: {}".format(str(e)))


def setup():
    commands.add(set_icon)
