#!/usr/bin/env python3
# Tanya24 IRC Bot - Command & Conquer Edition

import asyncio
import os
import socket
import json
from datetime import datetime
from modules import natural_ai
from modules.master import handle as ghost_handle

CONFIG_PATH = "config.json"


class TanyaIRCBot:
    def __init__(self, config):
        self.server = config["server"]
        self.port = config["port"]
        self.nick = config["nick"]
        self.channels = config["channels"]
        self.master = config["master"]
        self.bindhost = config.get("bindhost")
        self.xlogin_account = config.get("xlogin_account", self.nick)
        self.channel_password = config.get("channel_password")
        self.realname = "Tanya24 C&C Bot"
        self.reader = None
        self.writer = None

        # Ghost Watch
        self.watch_ips = set()
        self.watch_nicks = set(["corky", "Corky", "corky_", "Vader"])

    async def connect(self):
        print(f"[{self.ts()}] Tanya24: Connecting to {self.server}:{self.port}...")
        local_addr = (self.bindhost, 0) if self.bindhost else None
        self.reader, self.writer = await asyncio.open_connection(
            self.server, self.port, local_addr=local_addr
        )
        self.send_raw(f"NICK {self.nick}")
        self.send_raw(f"USER {self.nick} 0 * :{self.realname}")

    def send_raw(self, data: str):
        msg = data + "\r\n"
        self.writer.write(msg.encode("utf-8"))
        print(f"[{self.ts()}] >> {data}")

    async def join_channels(self):
        for chan in self.channels:
            self.send_raw(f"JOIN {chan}")
            await asyncio.sleep(1)

    async def x_login(self):
        if not self.channel_password:
            return
        self.send_raw(f"PRIVMSG x@channels.undernet.org :LOGIN {self.xlogin_account} {self.channel_password}")
        await asyncio.sleep(2)
        self.send_raw(f"MODE {self.nick} +x")
        await asyncio.sleep(1)

    async def handle_line(self, line: str):
        line = line.strip("\r\n")
        print(f"[{self.ts()}] << {line}")

        # PING/PONG
        if line.startswith("PING"):
            pong = line.replace("PING", "PONG")
            self.send_raw(pong)
            return

        parts = line.split()
        if len(parts) < 2:
            return

        prefix = ""
        if line.startswith(":"):
            prefix, *rest = line[1:].split(" ", 1)
            parts = rest[0].split()

        cmd = parts[0]

        # 001 = welcome
        if cmd == "001":
            await self.x_login()
            await self.join_channels()
            print(f"[{self.ts()}] Tanya24: Joined channels {self.channels}")
            return

        # PRIVMSG
        if cmd == "PRIVMSG":
            target = parts[1]
            msg = " ".join(parts[2:])[1:] if len(parts) > 2 else ""
            nick = prefix.split("!")[0] if "!" in prefix else prefix

            await self.handle_privmsg(nick, target, msg, prefix)

    async def handle_privmsg(self, nick: str, target: str, msg: str, prefix: str):
        # Surveillance Ghost
        await self.watch_activity(nick, prefix, target, msg)

        if ghost_handle(
            self,
            nick,
            prefix,
            target,
            msg
        ):
            return


        # Commandes du maître
        if nick.lower() == self.master.lower():
            if msg.startswith("!tanya "):
                cmd = msg[len("!tanya "):].strip()
                await self.handle_master_command(nick, target, cmd)
                return

        # IA naturelle si on lui parle
        if msg.lower().startswith("tanya24") or msg.lower().startswith("tanya"):
            prompt = f"{nick} in {target} says: {msg}"
            ai_reply = await natural_ai.generate_reply(prompt)
            self.reply(target, nick, ai_reply)
            return

        # Réponses simples
        if "red alert" in msg.lower():
            self.reply(target, nick, "This is Tanya. Lock and load.")
        elif "bonjour" in msg.lower():
            self.reply(target, nick, "Salut. C&C mode activé.")

    async def handle_master_command(self, nick: str, target: str, cmd: str):
        if cmd == "status":
            self.reply(target, nick, "Online, monitoring channels and targets.")
        elif cmd.startswith("watch nick "):
            wnick = cmd[len("watch nick "):].strip()
            self.watch_nicks.add(wnick)
            self.reply(target, nick, f"Nick {wnick} ajouté à la surveillance.")
        elif cmd.startswith("watch ip "):
            wip = cmd[len("watch ip "):].strip()
            self.watch_ips.add(wip)
            self.reply(target, nick, f"IP {wip} ajoutée à la surveillance.")
        elif cmd == "channels":
            self.reply(target, nick, f"Je surveille: {', '.join(self.channels)}")
        else:
            self.reply(target, nick, f"Commande inconnue: {cmd}")

    async def watch_activity(self, nick: str, prefix: str, target: str, msg: str):
        # Surveillance des nicks
        if nick in self.watch_nicks:
            self.log_watch(f"NICK WATCH: {nick} in {target} -> {msg}")

        # Surveillance IP (si visible dans prefix)
        if "@" in prefix:
            host = prefix.split("@", 1)[1]
            ip = host.split(":", 1)[0]
            if ip in self.watch_ips:
                self.log_watch(f"IP WATCH: {ip} ({nick}) in {target} -> {msg}")

    def log_watch(self, text: str):
        line = f"[{self.ts()}] {text}"
        print(line)
        os.makedirs("logs", exist_ok=True)
        with open("logs/tanya_watch.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def reply(self, target: str, nick: str, text: str):
        if target.startswith("#"):
            self.send_raw(f"PRIVMSG {target} :{nick}: {text}")
        else:
            self.send_raw(f"PRIVMSG {nick} :{text}")

    async def run(self):
        await self.connect()
        while True:
            try:
                line = await self.reader.readline()
                if not line:
                    print(f"[{self.ts()}] Connection closed by server, reconnecting...")
                    await asyncio.sleep(5)
                    await self.connect()
                    continue
                await self.handle_line(line.decode("utf-8", errors="ignore"))
            except (ConnectionResetError, socket.error) as e:
                print(f"[{self.ts()}] Connection error: {e}, reconnecting...")
                await asyncio.sleep(5)
                await self.connect()
            except Exception as e:
                print(f"[{self.ts()}] Error: {e}")

    @staticmethod
    def ts():
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


async def main():
    config = load_config()
    bot = TanyaIRCBot(config)
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())
