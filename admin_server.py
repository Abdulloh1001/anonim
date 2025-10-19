from flask import Flask, render_template, request, jsonify
import asyncio
from telegram.ext import ApplicationBuilder
from core.config import BOT_TOKEN
from core.utils import db_conn, add_tokens, display_for, log_channel_send

app = Flask(__name__)
bot = None

@app.route('/')
def admin_panel():
    return render_template('admin.html')

@app.route('/gift_tokens', methods=['POST'])
async def gift_tokens():
    try:
        data = request.json
        user_id = int(data['user_id'])
        amount = int(data['amount'])
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': '❌ Token miqdori musbat son bo\'lishi kerak'
            })
        
        conn = db_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE id=?", (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': '❌ Bunday foydalanuvchi topilmadi'
            })
        
        prev, new = add_tokens(user_id, amount)
        
        # Foydalanuvchiga xabar yuborish
        await bot.send_message(
            chat_id=user_id,
            text=f"🎁 Sizga {amount} token hadya qilindi!\nYangi balansingiz: {new}"
        )
        
        # Log kanalga xabar
        await log_channel_send(bot, f"🎁 {user_id} ga {amount} token hadya qilindi")
        
        conn.close()
        return jsonify({
            'success': True,
            'message': f'✅ {user_id} ga {amount} token berildi\nYangi balans: {new}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Xatolik yuz berdi: {str(e)}'
        })

def run_server():
    global bot
    bot = ApplicationBuilder().token(BOT_TOKEN).connect_timeout(10).read_timeout(10).build().bot
    app.run(host='127.0.0.1', port=5000)