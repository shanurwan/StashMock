import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")

app = App(token=SLACK_BOT_TOKEN)

@app.command("/incident")
def incident(ack, respond, command, client):
    ack()
    title = command.get("text") or "New Incident"
    # Create channel
    channel_name = f"inc-{title.replace(' ', '-')[:20]}"
    result = client.conversations_create(name=channel_name)
    channel_id = result["channel"]["id"]
    respond(f"Incident channel <#{channel_id}> created.")
    # (Placeholder) Open GitHub issue via GH API here.

if __name__ == "__main__":
    if not (SLACK_APP_TOKEN and SLACK_BOT_TOKEN):
        print("Set SLACK_APP_TOKEN and SLACK_BOT_TOKEN")
    else:
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
