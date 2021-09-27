import traceback
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os


app = Flask(__name__)
Base = declarative_base()

#環境変数取得
# LINE Developersで設定されているアクセストークンとChannel Secretをを取得し、設定します。
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(120))
    status = Column(String(10))


#PostgreSQLとの接続用
db_uri = os.environ['DATABASE_URL']
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine(db_uri)
session_factory = sessionmaker(bind=engine)
session = session_factory()

Base.metadata.create_all(bind = engine)

## 1 ##
#Webhookからのリクエストをチェックします。
@app.route("/callback", methods=['POST'])
def callback():
    # リクエストヘッダーから署名検証のための値を取得します。
    signature = request.headers['X-Line-Signature']

    # リクエストボディを取得します。
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    # 署名を検証し、問題なければhandleに定義されている関数を呼び出す。
    try:
        handler.handle(body, signature)
    # 署名検証で失敗した場合、例外を出す。
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return 'OK'

## 2 ##
###############################################
#LINEのメッセージの取得と返信内容の設定(オウム返し)
###############################################

#LINEでMessageEvent（普通のメッセージを送信された場合）が起こった場合に、
#def以下の関数を実行します。
#reply_messageの第一引数のevent.reply_tokenは、イベントの応答に用いるトークンです。 
#第二引数には、linebot.modelsに定義されている返信用のTextSendMessageオブジェクトを渡しています。


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    if "追加" in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = "何を追加しますか？"))
    elif "削除" in event.message.text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = "何を削除しますか？"))
    elif "登録" in event.message.text:
        try:
            user_data = User(user_name=profile.use_id, status="登録")
            session.add(user_data)
            session.commit()
        except:
            t = traceback.format_exc()
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text = t)
            )
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text = "登録ありがとうございます！\n user_id = {}".format(profile.user_id[:5]))
        )

"""
#フォロー時にRDBにデータを追加
@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text = "登録ありがとうございます！")
    )
    user = User(profile, "登録")
    db.session.add(user)
    db.session.commit()"""

# ポート番号の設定
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
