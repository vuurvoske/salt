"""
Module for notifications via Twilio

.. versionadded:: 2014.7.0

:depends:   - twilio python module
:configuration: Configure this module by specifying the name of a configuration
    profile in the minion config, minion pillar, or master config (with :conf_master:`pillar_opts` set to True).

    .. warning: Setting pillar_opts to True in the master config may be considered
      unsafe as it copies the master config to pillar

    For example:

    .. code-block:: yaml

        my-twilio-account:
            twilio.account_sid: AC32a3c83990934481addd5ce1659f04d2
            twilio.auth_token: mytoken
"""

import logging

HAS_LIBS = False
try:
    import twilio

    # Grab version, ensure elements are ints
    twilio_version = tuple([int(x) for x in twilio.__version_info__])
    if twilio_version > (5,):
        TWILIO_5 = False
        from twilio.rest import Client as TwilioRestClient
        from twilio.rest import TwilioException as TwilioRestException
    else:
        TWILIO_5 = True
        from twilio.rest import TwilioRestClient
        from twilio import TwilioRestException
    HAS_LIBS = True
except ImportError:
    pass


log = logging.getLogger(__name__)

__virtualname__ = "twilio"


def __virtual__():
    """
    Only load this module if twilio is installed on this minion.
    """
    if HAS_LIBS:
        return __virtualname__
    return (
        False,
        "The twilio_notify execution module failed to load: the twilio python library"
        " is not installed.",
    )


def _get_twilio(profile):
    """
    Return the twilio connection
    """
    creds = __salt__["config.option"](profile)
    client = TwilioRestClient(
        creds.get("twilio.account_sid"),
        creds.get("twilio.auth_token"),
    )

    return client


def send_sms(profile, body, to, from_):
    """
    Send an sms

    CLI Example:

        twilio.send_sms my-twilio-account 'Test sms' '+18019999999' '+18011111111'
    """
    ret = {}
    ret["message"] = {}
    ret["message"]["sid"] = None
    client = _get_twilio(profile)
    try:
        if TWILIO_5:
            message = client.sms.messages.create(body=body, to=to, from_=from_)
        else:
            message = client.messages.create(body=body, to=to, from_=from_)
    except TwilioRestException as exc:
        ret["_error"] = {}
        ret["_error"]["code"] = exc.code
        ret["_error"]["msg"] = exc.msg
        ret["_error"]["status"] = exc.status
        log.debug("Could not send sms. Error: %s", ret)
        return ret
    ret["message"] = {}
    ret["message"]["sid"] = message.sid
    ret["message"]["price"] = message.price
    ret["message"]["price_unit"] = message.price_unit
    ret["message"]["status"] = message.status
    ret["message"]["num_segments"] = message.num_segments
    ret["message"]["body"] = message.body
    ret["message"]["date_sent"] = str(message.date_sent)
    ret["message"]["date_created"] = str(message.date_created)
    log.info(ret)
    return ret
