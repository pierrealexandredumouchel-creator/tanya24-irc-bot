from modules.permissions import is_master

def handle(bot, nick, target, msg):

    if not is_master(nick):
        return False

    if msg == "!status":
        bot.send(target, "GhostCore online.")
        return True

    if msg.startswith("!join "):
        chan = msg.split(" ",1)[1]
        bot.sock.send(f"JOIN {chan}\r\n".encode())
        return True

    if msg.startswith("!part "):
        chan = msg.split(" ",1)[1]
        bot.sock.send(f"PART {chan}\r\n".encode())
        return True

    return False
