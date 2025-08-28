from dataclasses import dataclass
import datetime

@dataclass
class LogEvent:
    t: str; who: str; msg: str

class Logger:
    def __init__(self): self.events = []
    def add(self, who, msg): self.events.append(LogEvent("event", who, msg))
    def warn(self, who, msg): self.events.append(LogEvent("warning", who, msg))
    def error(self, who, msg): self.events.append(LogEvent("error", who, msg))
    def dump(self): return "\n".join(
        {"event":"[=]","warning":"[!]","error":"[x]"}[e.t]+f" {e.who}: {e.msg}" for e in self.events)

def log(message: str):
    print(f"[{datetime.datetime.now().isoformat()}] {message}")
